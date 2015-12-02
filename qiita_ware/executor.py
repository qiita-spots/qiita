# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from subprocess import Popen, PIPE
from os.path import join

from qiita_core.qiita_settings import qiita_config
from qiita_db.processing_job import ProcessingJob
from qiita_db.util import get_work_base_dir
from qiita_db.logger import LogEntry


def system_call(cmd):
    """Call command and return (stdout, stderr, return_value)

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


def execute(user, parameters):
    """Executes a job through the plugin system

    Parameters
    ----------
    user : qiita_db.user.User
        The user who launches the job
    parameters : qiita_db.software.Parameters
        The parameters of the job
    """
    # Create the new job
    job = ProcessingJob.create(user, parameters)
    job_dir = join(get_work_base_dir(), job.id)
    software = parameters.command.software
    plugin_start_script = software.start_script
    plugin_env_name = software.environment_name

    # Get the command to start the plugin
    cmd = [qiita_config.plugin_launcher, plugin_env_name, plugin_start_script,
           qiita_config.base_url, job.id, job_dir]

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
