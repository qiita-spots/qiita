# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

import traceback
import sys
from os.path import exists, join, dirname, abspath
from os import makedirs, environ
from future import standard_library

from qiita_client import QiitaClient

from tgp.split_libraries import split_libraries, split_libraries_fastq
from tgp.pick_otus import pick_closed_reference_otus

with standard_library.hooks():
    from configparser import ConfigParser

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
    # Set up the Qiita Client
    dflt_conf_fp = join(dirname(abspath(__file__)), 'support_files',
                        'config_file.cfg')
    conf_fp = environ.get('QP_TARGET_GENE_CONFIG_FP', dflt_conf_fp)
    config = ConfigParser()
    with open(conf_fp, 'U') as conf_file:
        config.readfp(conf_file)

    qclient = QiitaClient(server_url, config.get('main', 'CLIENT_ID'),
                          config.get('main', 'CLIENT_SECRET'),
                          server_cert=config.get('main', 'SERVER_CERT'))

    # Request job information. If there is a problem retrieving the job
    # information, the QiitaClient already raises an error
    job_info = qclient.get_job_info(job_id)
    # Starting the heartbeat
    qclient.start_heartbeat(job_id)
    # Execute the given task
    task_name = job_info['command']
    task = TASK_DICT[task_name]

    if not exists(output_dir):
        makedirs(output_dir)
    try:
        success, artifacts_info, error_msg = task(
            qclient, job_id, job_info['parameters'], output_dir)
    except Exception:
        exc_str = repr(traceback.format_exception(*sys.exc_info()))
        error_msg = ("Error executing %s:\n%s" % (task_name, exc_str))
        success = False
        artifacts_info = None
    # The job completed
    qclient.complete_job(job_id, success, error_msg=error_msg,
                         artifacts_info=artifacts_info)
