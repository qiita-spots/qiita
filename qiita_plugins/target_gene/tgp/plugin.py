# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

import traceback
import sys

import requests

from tgp.util import (start_heartbeat, complete_job, execute_request_retry,
                      format_payload)
from tgp.split_libraries import split_libraries, split_libraries_fastq
from tgp.pick_otus import pick_closed_reference_otus

TASK_DICT = {
    'Split libraries FASTQ': split_libraries_fastq,
    'Split libraries': split_libraries,
    'Pick closed-reference OTUs': pick_closed_reference_otus
}


def execute_job(server_url, job_id, output_dir):
    """Starts the plugin and executes the assigned task

    Parameters
    ----------
    server_url : str
        The url of the server
    job_id : str
        The job id

    Raises
    ------
    RuntimeError
        If there is a problem gathering the job information
    """
    # Request job information
    url = "%s/qiita_db/jobs/%s" % (server_url, job_id)
    job_info = execute_request_retry(requests.get, url)
    # Check if we have received the job information so we can start it
    if job_info['success']:
        # Starting the heartbeat
        start_heartbeat(server_url, job_id)
        # Execute the given task
        task_name = job_info['command']
        task = TASK_DICT[task_name]
        try:
            payload = task(server_url, job_id, job_info['parameters'],
                           output_dir)
        except Exception:
            exc_str = repr(traceback.format_exception(*sys.exc_info()))
            error_msg = ("Error executing %s:\n%s" % (task_name, exc_str))
            payload = format_payload(False, error_msg=error_msg)
        # The job completed
        complete_job(server_url, job_id, payload)
    else:
        raise RuntimeError("Can't get job (%s) information" % job_id)
