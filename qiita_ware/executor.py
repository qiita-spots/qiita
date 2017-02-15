# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from subprocess import Popen, PIPE
from os.path import join
from functools import partial

from qiita_ware.context import context, _redis_wrap
from qiita_core.qiita_settings import qiita_config
from qiita_db.processing_job import ProcessingJob
from qiita_db.util import get_work_base_dir
from qiita_db.logger import LogEntry


def system_call(cmd):
    """Call cmd and return (stdout, stderr, return_value)

    Parameters
    ----------
    cmd : str or iterator of str
        The string containing the command to be run, or a sequence of strings
        that are the tokens of the command.

    Notes
    -----
    This function is ported from QIIME (http://www.qiime.org), previously named
    qiime_system_call. QIIME is a GPL project, but we obtained permission from
    the authors of this function to port it to Qiita and keep it under BSD
    license.
    """
    proc = Popen(cmd, universal_newlines=True, shell=True, stdout=PIPE,
                 stderr=PIPE)
    # Communicate pulls all stdout/stderr from the PIPEs
    # This call blocks until the command is done
    stdout, stderr = proc.communicate()
    return_value = proc.returncode
    return stdout, stderr, return_value


def execute(job_id):
    """Executes a job through the plugin system

    Parameters
    ----------
    job_id : str
        The id of the job to execute
    """
    # Create the new job
    job = ProcessingJob(job_id)
    job_dir = join(get_work_base_dir(), job.id)
    software = job.command.software
    plugin_start_script = software.start_script
    plugin_env_script = software.environment_script

    # Get the command to start the plugin
    cmd = '%s "%s" "%s" "%s" "%s" "%s"' % (
        qiita_config.plugin_launcher, plugin_env_script, plugin_start_script,
        qiita_config.base_url, job.id, job_dir)

    # Start the plugin
    std_out, std_err, return_value = system_call(cmd)
    if return_value != 0:
        # Something wrong happened during the plugin start procedure
        job.status = 'error'
        log = LogEntry.create(
            'Runtime',
            "Error starting plugin '%s':\nStd output:%s\nStd error:%s"
            % (software.name, std_out, std_err))
        job.log = log


def _submit(ctx, user, parameters):
    """Submit a plugin job to a cluster

    Parameters
    ----------
    ctx : qiita_db.ware.Dispatch
        A Dispatch object to submit through
    user : qiita_db.user.User
        The user doing the submission
    parameters : qiita_db.software.Parameters
        The parameters of the job

    Returns
    -------
    str
        The job id
    """
    job = ProcessingJob.create(user, parameters)
    redis_deets = {'job_id': job.id, 'pubsub': user.id,
                   'messages': user.id + ':messages'}
    ctx.submit_async(_redis_wrap, execute, redis_deets, job.id)
    return job.id


plugin_submit = partial(_submit, context)
