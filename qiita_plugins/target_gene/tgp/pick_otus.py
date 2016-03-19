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

from qiita_client import format_payload

from tgp.util import system_call


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
        f.write("pick_otus:otu_picking_method\tsortmerna\n")
        for p in params:
            f.write("pick_otus:%s\t%s\n" % (p, parameters[p]))


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
    str, str
        The pick_closed_reference_otus.py command
        The output directory

    Raises
    ------
    ValueError
        If there is no sequence file fount in the artifact
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

    cmd = str("pick_closed_reference_otus.py -i %s -r %s -o %s -p %s %s"
              % (seqs_fp, reference_fp, output_dir, param_fp, params_str))
    return cmd, output_dir


def generate_artifact_info(pick_out):
    """Creates the artifact information to attach to the payload

    Parameters
    ----------
    pick_out : str
        Path to the pick otus directory

    Returns
    -------
    list
        The artifacts information
    """
    path_builder = partial(join, pick_out)
    filepaths = [(path_builder('otu_table.biom'), 'biom'),
                 (path_builder('sortmerna_picked_otus'), 'directory'),
                 (glob(path_builder('log_*.txt'))[0], 'log')]
    return [['OTU table', 'BIOM', filepaths]]


def pick_closed_reference_otus(qclient, job_id, parameters, out_dir):
    """Run split libraries fastq with the given parameters

    Parameters
    ----------
    qclient : tgp.qiita_client.QiitaClient
        The Qiita server client
    job_id : str
        The job id
    parameters : dict
        The parameter values to run split libraries
    out_dir : str
        Yhe path to the job's output directory

    Returns
    -------
    dict
        The results of the job

    Raises
    ------
    ValueError
        If there is any error gathering the information from the server
    """
    qclient.update_job_step(job_id, "Step 1 of 3: Collecting information")
    artifact_id = parameters['input_data']
    fps_info = qclient.get("/qiita_db/artifacts/%s/filepaths/" % artifact_id)
    if not fps_info or not fps_info['success']:
        error_msg = "Could not get artifact filepath information: %s"
        if fps_info:
            error_msg = error_msg % fps_info['error']
        else:
            error_msg = error_msg % "could not connect with the server"
        raise ValueError(error_msg)
    fps = fps_info['filepaths']

    reference_id = parameters['reference']
    ref_info = qclient.get("/qiita_db/references/%s/filepaths/" % reference_id)
    if not ref_info or not ref_info['success']:
        error_msg = "Could not get artifact filepath information: %s"
        if ref_info:
            error_msg = error_msg % ref_info['error']
        else:
            error_msg = error_msg % "could not connect with the server"
        raise ValueError(error_msg)
    reference_fps = ref_info['filepaths']

    qclient.update_job_step(job_id, "Step 2 of 3: Generating command")
    command, pick_out = generate_pick_closed_reference_otus_cmd(
        fps, out_dir, parameters, reference_fps)

    qclient.update_job_step(job_id, "Step 3 of 3: Executing OTU picking")
    std_out, std_err, return_value = system_call(command)
    if return_value != 0:
        error_msg = ("Error running OTU picking:\nStd out: %s\nStd err: %s"
                     % (std_out, std_err))
        return format_payload(False, error_msg=error_msg)

    artifacts_info = generate_artifact_info(pick_out)

    return format_payload(True, artifacts_info=artifacts_info)
