# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from os.path import join
from functools import partial
from glob import glob

import requests

from tgp.util import (update_job_step, execute_request_retry, system_call,
                      format_payload)


def write_parameters_file(fp, parameters):
    """Write the QIIME parameters file

    Parameters
    ----------
    fp : str
        The paramters file filepath
    parameters : dict
        The commands parameters, keyed by parameter name
    """
    params = ['sortmerna_max_pos', 'similarity', 'sortmerna_coverage',
              'threads']
    with open(fp, 'w') as f:
        for p in params:
            f.write("pick_otus:%s\t%s" % (p, parameters[p]))


def generate_pick_closed_reference_otus_cmd(filepaths, out_dir, parameters,
                                            reference_fps):
    """Generates the pick_closed_reference_otus.py command

    Parameters
    ----------
    filepaths : list of (str, str)
        The artifact's filepaths and their types
    out_dir : str
        The job output directory
    parameters : dict
        The command's parameters, keyed by parameter name
    reference_fps : list of (str, str)
        The reference filepaths and their types

    Returns
    -------
    str
        The pick_closed_reference_otus.py command
    """
    seqs_fp = None
    for fp, fp_type in filepaths:
        if fp_type == 'preprocessed_fasta':
            seqs_fp = fp
            break

    if not seqs_fp:
        raise ValueError("No sequence file found on the artifact")

    output_dir = join(out_dir, 'cr_otus')
    param_fp = join(out_dir, 'cr_params.txt')

    write_parameters_file(param_fp, parameters)

    reference_fp = None
    taxonomy_fp = None
    for rfp, rfp_type in reference_fps:
        if rfp_type == 'reference_seqs':
            reference_fp = rfp
        elif rfp_type == 'reference_tax':
            taxonomy_fp = rfp

    params_str = "-t %s" % taxonomy_fp if taxonomy_fp else ""

    cmd = str("pick_closed_reference_otus.py -i %s-r %s -o %s -p %s %s"
              % (seqs_fp, reference_fp, output_dir, param_fp, params_str))
    return cmd


def pick_closed_reference_otus(server_url, job_id, parameters, out_dir):
    """Run split libraries fastq with the given parameters

    Parameters
    ----------
    parameters : dict
        The parameter values to run split libraries

    Returns
    -------
    dict
        The results of the job
    """
    update_job_step(server_url, job_id, "Step 1 of 3: Collecting information")
    artifact_id = parameters['input_data']
    url = "%s/qiita_db/artifacts/%s/filepaths/" % (server_url, artifact_id)
    fps_info = execute_request_retry(requests.get, url)
    if not fps_info or not fps_info['success']:
        error_msg = "Could not get artifact filepath information: %s"
        if fps_info:
            error_msg = error_msg % fps_info['error']
        else:
            error_msg = error_msg % "could not connect with the server"
        raise ValueError(error_msg)
    fps = fps_info['filepaths']

    reference_id = parameters['reference_id']
    url = "%s/qiita_db/reference/%s/filepaths/" % (server_url, reference_id)
    ref_info = execute_request_retry(requests.get, url)
    if not ref_info or not ref_info['success']:
        error_msg = "Could not get artifact filepath information: %s"
        if ref_info:
            error_msg = error_msg % ref_info['error']
        else:
            error_msg = error_msg % "could not connect with the server"
        raise ValueError(error_msg)
    reference_fps = ref_info['filepaths']

    update_job_step(server_url, job_id, "Step 2 of 3: Generating command")
    command, pick_out = generate_pick_closed_reference_otus_cmd(
        fps, out_dir, parameters, reference_fps)

    update_job_step(server_url, job_id, "Step 3 of 3: Executing OTU picking")
    std_out, std_err, return_value = system_call(command)
    if return_value != 0:
        error_msg = ("Error running OTU picking:\nStd out: %s\nStd err: %s"
                     % (std_out, std_err))
        return format_payload(True, error_msg=error_msg)

    path_builder = partial(join, pick_out)
    filepaths = [(path_builder('otu_table.biom'), 'biom'),
                 (path_builder('sortmerna_picked_otus'), 'directory'),
                 (glob(path_builder('log_*.txt')), 'log')]
    artifacts_info = ['BIOM', filepaths, True, True]

    return format_payload(True, artifacts_info=artifacts_info)
