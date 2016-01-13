# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

import time
import threading
from json import dumps
from subprocess import Popen, PIPE

JOB_COMPLETED = False


def system_call(cmd):
    """Call command and return (stdout, stderr, return_value)

    Parameters
    ----------
    cmd : str or iterator of str
        The string containing the command to be run, or a sequence of strings
        that are the tokens of the command.

    Returns
    -------
    str, str, int
        - The stabdard output of the command
        - The standard error of the command
        - The exit status of the command

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


def heartbeat(qclient, url):
    """Send the heartbeat calls to the server

    Parameters
    ----------
    qclient : tgp.qiita_client.QiitaClient
        The Qiita server client
    url : str
        The url to issue the heartbeat
    """
    while not JOB_COMPLETED:
        json_reply = qclient.post(url, data='')
        if not json_reply or not json_reply['success']:
            # The server did not accept our heartbeat - stop doing it
            break
        # Perform the heartbeat every 5 seconds
        time.sleep(5)


def start_heartbeat(qclient, job_id):
    """Create and start a thread that would send the heartbeats to the server

    Parameters
    ----------
    qclient : tgp.qiita_client.QiitaClient
        The Qiita server client
    job_id : str
        The job id
    """
    url = "/qiita_db/jobs/%s/heartbeat/" % job_id
    heartbeat_thread = threading.Thread(
        target=heartbeat, args=(qclient, url))
    heartbeat_thread.daemon = True
    heartbeat_thread.start()


def update_job_step(qclient, job_id, new_step):
    """Updates the curent step of the job in the server

    Parameters
    ----------
    qclient : tgp.qiita_client.QiitaClient
        The Qiita server client
    jon_id : str
        The job id
    new_step : str
        The new step
    """
    json_payload = dumps({'step': new_step})
    qclient.post("/qiita_db/jobs/%s/step/" % job_id, data=json_payload)


def complete_job(qclient, job_id, payload):
    """Stops the heartbeat thread and send the job results to the server

    Parameters
    ----------
    qclient : tgp.qiita_client.QiitaClient
        The Qiita server client
    job_id : str
        The job id
    payload : dict
        The job's results
    """
    # Stop the heartbeat thread
    global JOB_COMPLETED
    JOB_COMPLETED = True
    # Create the URL where we have to post the results
    json_payload = dumps(payload)
    qclient.post("/qiita_db/jobs/%s/complete/" % job_id, data=json_payload)


def format_payload(success, error_msg=None, artifacts_info=None):
    """Generates the payload dictionary for the job

    Parameters
    ----------
    success : bool
        Whether if the job completed successfully or not
    error_msg : str, optional
        If `success` is False, ther error message to include in the optional.
        If `success` is True, it is ignored
    artifacts_info : list of (str, list of (str, str), bool, bool)
        For each artifact that needs to be created, the artifact type,
        the list of files attached to the artifact, a boolean indicating if
        the artifact can be submitted to ebi and a boolean indicating if the
        artifact can be submitted to vamps

    Returns
    -------
    dict
        Format:
        {'success': bool,
         'error': str,
         'artifacts': list of {'artifact_type': str,
                               'filepaths': list of (str, str),
                               'can_be_submitted_to_ebi': bool,
                               'can_be_submitted_to_vamps': bool}}
    """
    if success:
        error_msg = ''
        artifacts = [
            {'artifact_type': atype,
             'filepaths': filepaths,
             'can_be_submitted_to_ebi': ebi,
             'can_be_submitted_to_vamps': vamps}
            for atype, filepaths, ebi, vamps in artifacts_info]
    else:
        artifacts = None

    payload = {'success': success,
               'error': error_msg if not success else '',
               'artifacts': artifacts}
    return payload
