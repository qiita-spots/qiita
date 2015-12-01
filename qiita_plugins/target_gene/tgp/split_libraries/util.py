# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from os.path import join, exists
from functools import partial
from os import makedirs

import requests
import pandas as pd
from h5py import File
# Currently the EBI submission is not part of the target gene plugin
# and the demux file is not its own project, so we need to import from
# qiita_ware. Plans are to the EBI submission to the target gene plugin
from qiita_ware.demux import to_hdf5

from tgp.util import execute_request_retry


def get_artifact_information(server_url, artifact_id):
    """Retrieves the artifact information for running split libraries

    Parameters
    ----------
    server_url : str
        The URL of the server
    artifact_id : str
        The artifact id

    Returns
    -------
    list of (str, str), str, str
        The artifact filepaths and their type
        The artifact mapping file
        The artifact type
    """
    # Get the artifact filepath information
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

    # Get the artifact metadata
    url = "%s/qiita_db/artifacts/%s/mapping/" % (server_url, artifact_id)
    metadata_info = execute_request_retry(requests.get, url)
    if not metadata_info or not metadata_info['success']:
        error_msg = "Could not get artifact metadata information %s"
        if metadata_info:
            error_msg = error_msg % metadata_info['error']
        else:
            error_msg = error_msg % "could not connect with the server"
        raise ValueError(error_msg)
    mapping_file = metadata_info['mapping']

    # Get the artifact type
    url = "%s/qiita_db/artifacts/%s/type/" % (server_url, artifact_id)
    type_info = execute_request_retry(requests.get, url)
    if not type_info or not type_info['success']:
        error_msg = "Could not get artifact metadata information %s"
        if type_info:
            error_msg = error_msg % type_info['error']
        else:
            error_msg = error_msg % "could not connect with the server"
        raise ValueError(error_msg)
    artifact_type = type_info['type']

    return fps, mapping_file, artifact_type


def split_mapping_file(mapping_file, out_dir):
    """Splits a QIIME-compliant mapping file by run_prefix

    Parameters
    ----------
    mapping_file : str
        The mapping file filepath
    out_dir : str
        The path to the output directory

    Returns
    -------
    list of str
        The paths to the splitted mapping files
    """
    mf = pd.read_csv(mapping_file, delimiter='\t', dtype=str, encoding='utf-8')
    mf.set_index('#SampleID', inplace=True)

    path_builder = partial(join, out_dir)
    if 'run_prefix' in mf:
        if not exists(out_dir):
            makedirs(out_dir)
        output_fps = []
        for prefix, df in mf.groupby('run_prefix'):
            out_fp = path_builder('%s_mapping_file.txt' % prefix)
            output_fps.append(out_fp)
            df.to_csv(out_fp, index_label='#SampleID', sep='\t')
    else:
        output_fps = [mapping_file]

    return output_fps


def generate_demux_file(sl_out):
    """Creates the HDF5 demultiplexed file

    Parameters
    ----------
    sl_out : str
        Path to the output directory of split libraries

    Returns
    -------
    str
        The path of the demux file

    Raises
    ------
    ValueError
        If the split libraries output does not contain the demultiplexed fastq
        file
    """
    fastq_fp = join(sl_out, 'seqs.fastq')
    if not exists(fastq_fp):
        raise ValueError("The split libraries output directory does not "
                         "contain the demultiplexed fastq file.")

    demux_fp = join(sl_out, 'seqs.demux')
    with File(demux_fp, "w") as f:
        to_hdf5(fastq_fp, f)

    return demux_fp
