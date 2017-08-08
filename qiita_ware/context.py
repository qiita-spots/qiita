# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from subprocess import Popen, PIPE
from uuid import uuid4
from functools import partial
from time import sleep

from IPython.parallel import Client
from moi import r_client

from .exceptions import ComputeError


def system_call(cmd):
    """Call cmd and return (stdout, stderr, return_value).

    cmd: can be either a string containing the command to be run, or a
     sequence of strings that are the tokens of the command.

    This function is ported from QIIME (http://www.qiime.org), previously
    named qiime_system_call. QIIME is a GPL project, but we obtained permission
    from the authors of this function to port it to pyqi (and keep it under
    pyqi's BSD license).
    """
    proc = Popen(cmd,
                 universal_newlines=True,
                 shell=True,
                 stdout=PIPE,
                 stderr=PIPE)
    # communicate pulls all stdout/stderr from the PIPEs to
    # avoid blocking -- don't remove this line!
    stdout, stderr = proc.communicate()
    return_value = proc.returncode

    if return_value != 0:
        raise ComputeError("Failed to execute: %s\nstdout: %s\nstderr: %s" %
                           (cmd, stdout, stderr))

    return stdout, stderr, return_value


class Dispatch(object):
    """Dispatch compute

    Attributes
    ----------
    reserved
    reserved_lview
    general
    general_lview
    demo
    demo_lview

    Methods
    -------
    submit_async
    submit_async_deps
    submit_sync
    sync

    """
    def __init__(self):
        from moi import ctx_default
        self.demo = Client(profile=ctx_default)

        # checking that at least 2 workers exist, see:
        # https://github.com/biocore/qiita/issues/1066
        workers = len(self.demo.ids)
        if workers < 2:
            raise ValueError('You need to have at least 2 IPython workers '
                             'but you have %d' % workers)

        self.demo_lview = self.demo.load_balanced_view()

    def sync(self, data):
        """Sync data to engines

        Parameters
        ----------
        data : dict
            dict of objects and to sync

        """
        self.demo[:].update(data)

    def submit_async(self, cmd, *args, **kwargs):
        """Submit an async command to execute

        Parameters
        ----------
        cmd : {function, str}
            A function to execute or a system call to execute
        args : list
            Arguments to pass to a function (if cmd is function)
        kwargs : dict
            Keyword arguments to pass to a function (if cmd is function)

        Returns
        -------
        IPython.parallel.client.asyncresult.AsyncResult

        """
        if isinstance(cmd, str):
            task = self.demo_lview.apply_async(system_call, cmd)
        else:
            task = self.demo_lview.apply_async(cmd, *args, **kwargs)

        return task

    def submit_async_deps(self, deps, cmd, *args, **kwargs):
        """Submit as async command to execute after all dependencies are done

        Parameters
        ----------
        deps : list of AsyncResult
            The list of job dependencies for cmd
        cmd : {function, str}
            A function to execute or a system call to execute
        args : list
            Arguments to pass to a function (if cmd is function)
        kwargs : dict
            Keyword arguments to pass to a function (if cmd is function)

        Returns
        -------
        IPython.parallel.client.asyncresult.AsyncResult
        """
        with self.demo_lview.temp_flags(after=deps, block=False):
            if isinstance(cmd, str):
                task = self.demo_lview.apply_async(system_call, cmd)
            else:
                task = self.demo_lview.apply_async(cmd, *args, **kwargs)

        return task

    def submit_sync(self, cmd, *args, **kwargs):
        """Submit an sync command to execute

        Parameters
        ----------
        cmd : {function, str}
            A function to execute or a system call to execute
        args : list
            Arguments to pass to a function (if cmd is function)
        kwargs : dict
            Keyword arguments to pass to a function (if cmd is function)

        Returns
        -------
        Dependent on cmd

        """
        if isinstance(cmd, str):
            result = self.demo_lview.apply_sync(system_call, cmd)
        else:
            result = self.demo_lview.apply_sync(cmd, *args, **kwargs)

        return result

    def wait(self, handlers):
        """Waits until all async jobs in handlers have finished

        Parameters
        ----------
        handlers : list of AsyncResult
            The AsyncResult objects to wait for
        """
        return self.demo_lview.wait(handlers)


def _redis_wrap(f, redis_deets, *args, **kwargs):
    """Wrap something to compute, and notify about state

    At the end, sets the key job_id with the serialized payload result. The
    payload consists of:

        {'job_id': uuid,
         'status_msg': {'Success', 'Failed'},
         'return': up to f}

    The set key will expire in 7 days.

    The result is also pushed to the corresponding messages key in redis_deets,
    as well as published on the corresponding pubsub key.

    Parameters
    ----------
    f : function
        A function to execute
    redis_deets : dict
        Redis details, specifically {'job_id': uuid,
                                     'pubsub': key to publish on,
                                     'messages': key to push messages to}
    """
    def _deposit_payload(redis_deets, payload):
        """Drop messages into redis

        This is being defined inline as we need to use it multiple times, and
        for an undiagnosed reason, having this function call it as a first
        class function does not work.
        """
        from json import dumps
        from moi import r_client

        job_id = redis_deets['job_id']
        pubsub = redis_deets['pubsub']
        messages = redis_deets['messages']

        serialized = dumps(payload)

        # First, we need to push the message on to the messages queue which is
        # in place in the event of a race-condition where a websocket client
        # may not be already listening to the pubsub.
        r_client.rpush(messages, serialized)

        # Next, in support of our "normal" and desired means of communicating,
        # we "publish" our payload. Anyone listening on the pubsub will see
        # this and fire an event (e.g., WebSocketHandler.callback)
        r_client.publish(pubsub, serialized)

        # Finally, we dump the payload keyed by job ID so that subsequent
        # handlers who are not listening on the channel can examine the results
        r_client.set(job_id, serialized, ex=86400 * 7)  # expire at 1 week

    job_id = redis_deets['job_id']
    payload = {'job_id': job_id, 'status_msg': 'Running', 'return': None}

    _deposit_payload(redis_deets, payload)
    try:
        payload['return'] = f(*args, **kwargs)
        payload['status_msg'] = 'Success'
    except Exception:
        import sys
        import traceback
        payload['return'] = repr(traceback.format_exception(*sys.exc_info()))
        payload['status_msg'] = 'Failed'
    finally:
        _deposit_payload(redis_deets, payload)


def _submit(ctx, channel, f, *args, **kwargs):
    """Submit a function to a cluster

    The work is submitted to the context, and a UUID describing the job is
    returned. On completion, regardless of success or fail, the status of the
    job will be set in `r_client` under the key of the UUID, and additionally,
    the UUID will be published to the channel 'qiita-compute-complete'.

    Parameters
    ----------
    ctx : Dispatch
        A Dispatch object to submit through
    channel : str
        channel to submit the run to
    f : function
        The function to execute. Any returns from this function will be
        serialized and deposited into Redis using the uuid for a key.
    args : tuple or None
        Any args for ``f``
    kwargs : dict or None
        Any kwargs for ``f``

    Returns
    -------
    uuid
        The job ID
    """
    uuid = str(uuid4())
    redis_deets = {'job_id': uuid, 'pubsub': channel,
                   'messages': channel + ':messages'}
    ctx.submit_async(_redis_wrap, f, redis_deets, *args, **kwargs)
    return uuid


# likely want this in qiita_ware.__init__
context = Dispatch()
submit = partial(_submit, context)


def safe_submit(*args, **kwargs):
    """Safe wraper for the submit function

    There are cases in which a race condition may occur: submit returns the
    job id but moi hasn't submitted the job. In some cases this is not
    acceptable, so this wrapper makes sure that the job_id
    is returned only once the job has already been submitted.

    From previous tests, the while loop is executed ~2 times, so there is not
    much time lost in here
    """
    job_id = submit(*args, **kwargs)
    payload = r_client.get(job_id)
    while not payload:
        sleep(0.005)
        payload = r_client.get(job_id)

    return job_id
