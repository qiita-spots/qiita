# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from moi.job import system_call


def submit_async_deps(ctx, deps, cmd, *args, **kwargs):
    """Submit as async command to execute after all dependencies are done

    Parameters
    ----------
    ctx : moi.context.Context
        The submission context
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
    with ctx.bv.temp_flags(after=deps, block=False):
        if isinstance(cmd, str):
            task = ctx.apply_async(system_call, cmd)
        else:
            task = ctx.apply_async(cmd, *args, **kwargs)

    return task


def wait(ctx, handlers):
    """Waits until all async jobs in handlers have finished

    Parameters
    ----------
    ctx : moi.context.Context
        The submission context
    handlers : list of AsyncResult
        The AsyncResult objects to wait for
    """
    return ctx.bv.wait(handlers)
