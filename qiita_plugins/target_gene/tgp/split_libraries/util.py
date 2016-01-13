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

import pandas as pd
from h5py import File
# Currently the EBI submission is not part of the target gene plugin
# and the demux file is not its own project, so we need to import from
# qiita_ware. Plans are to the EBI submission to the target gene plugin
from qiita_ware.demux import to_hdf5


def get_artifact_information(qclient, artifact_id):
    """Retrieves the artifact information for running split libraries

    Parameters
    ----------
    qclient : tgp.qiita_client.QiitaClient
        The Qiita server client
    artifact_id : str
        The artifact id

    Returns
    -------
    list of (str, str), str, str
        The artifact filepaths and their type
        The artifact mapping file
        The artifact type

    Raises
    ------
    ValueError
        If there is any problem gathering the information from the server
    """
    # Get the artifact filepath information
    fps_info = qclient.get("/qiita_db/artifacts/%s/filepaths/" % artifact_id)
    if not fps_info or not fps_info['success']:
        error_msg = "Could not get artifact filepath information: %s"
        if fps_info:
            error_msg = error_msg % fps_info['error']
        else:
            error_msg = error_msg % "could not connect with the server"
        raise ValueError(error_msg)
    fps = fps_info['filepaths']

    # Get the artifact metadata
    metadata_info = qclient.get(
        "/qiita_db/artifacts/%s/mapping/" % artifact_id)
    if not metadata_info or not metadata_info['success']:
        error_msg = "Could not get artifact metadata information %s"
        if metadata_info:
            error_msg = error_msg % metadata_info['error']
        else:
            error_msg = error_msg % "could not connect with the server"
        raise ValueError(error_msg)
    mapping_file = metadata_info['mapping']

    # Get the artifact type
    type_info = qclient.get("/qiita_db/artifacts/%s/type/" % artifact_id)
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
    fastq_fp = str(join(sl_out, 'seqs.fastq'))
    if not exists(fastq_fp):
        raise ValueError("The split libraries output directory does not "
                         "contain the demultiplexed fastq file.")

    demux_fp = join(sl_out, 'seqs.demux')
    with File(demux_fp, "w") as f:
        to_hdf5(fastq_fp, f)
    return demux_fp


def generate_artifact_info(sl_out):
    """Creates the artifact information to attach to the payload

    Parameters
    ----------
    sl_out : str
        Path to the split libraries output directory

    Returns
    -------
    list of [str, list of (str, str), bool, bool]
        The artifacts information to include in the payload when the split
        libraries job is completed.
        - The artifact type
        - The list of filepaths with their artifact type
        - Whether the artifact can be submitted to ebi
        - Whether the artifact can be submitted to vamps
    """
    path_builder = partial(join, sl_out)
    filepaths = [(path_builder('seqs.fna'), 'preprocessed_fasta'),
                 (path_builder('seqs.fastq'), 'preprocessed_fastq'),
                 (path_builder('seqs.demux'), 'preprocessed_demux'),
                 (path_builder('split_library_log.txt'), 'log')]
    return [['Demultiplexed', filepaths, True, True]]
