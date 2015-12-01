# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from os.path import join, basename
from functools import partial

import pandas as pd

from tgp.util import update_job_step, system_call, format_payload
from .util import (get_artifact_information, split_mapping_file,
                   generate_demux_file)


def generate_parameters_string(parameters):
    """Generates the parameters string from the parameters dictionary

    Parameters
    ----------
    parameters : dict
        The parameter values, keyed by parameter name

    Returns
    -------
    str
        A string with the parameters to the CLI call
    """
    flag_params = ['rev_comp_barcode', 'rev_comp_mapping_barcodes', 'rev_comp']
    str_params = ['max_bad_run_length', 'min_per_read_length_fraction',
                  'sequence_max_n', 'phred_quality_threshold', 'barcode_type',
                  'max_barcode_errors']
    result = ["--%s %s" % (sp, parameters[sp]) for sp in str_params]
    for fp in flag_params:
        if parameters[fp]:
            result.append("--%s" % fp)
    return ' '.join(result)


def get_sample_names_by_run_prefix(mapping_file):
    """Generates a dictionary of run_prefix and sample names

    Parameters
    ----------
    mapping_file : str
        The mapping file

    Returns
    -------
    dict
        Dict mapping run_prefix to sample id

    Raises
    ------
    ValueError
        If there is more than 1 sample per run_prefix
    """
    qiime_map = pd.read_csv(mapping_file, delimiter='\t', dtype=str,
                            encoding='utf-8')
    qiime_map.set_index('#SampleID', inplace=True)

    samples = {}
    errors = []
    for prefix, df in qiime_map.groupby('run_prefix'):
        len_df = len(df)
        if len_df != 1:
            errors.append('%s has %d samples (%s)' % (prefix, len_df,
                                                      ', '.join(df.index)))
        else:
            samples[prefix] = df.index.values[0]

    if errors:
        raise ValueError("You have run_prefix values with multiple "
                         "samples: %s" % ' -- '.join(errors))

    return samples


def generate_per_sample_fastq_command(forward_seqs, reverse_seqs, barcode_fps,
                                      mapping_file, output_dir, params_str):
    """Generates the per-sample FASTQ split_libraries_fastq.py command

    Parameters
    ----------
    forward_seqs : list of str
        The list of forward seqs filepaths
    reverse_seqs : list of str
        The list of reverse seqs filepaths
    barcode_fps : list of str
        The list of barcode filepaths
    mapping_file : str
        The path to the mapping file
    output_dir : str
        The path to the split libraries output directory
    params_str : str
        The string containing the parameters to pass to
        split_libraries_fastq.py

    Returns
    -------
    str
        The CLI to execute

    Raises
    ------
    ValueError
        - If barcode_fps is not an empty list
        - If there are run prefixes in the mapping file that do not match
        the sample names
    """
    if barcode_fps:
        raise ValueError('per_sample_FASTQ can not have barcodes: %s'
                         % (', '.join(basename(b) for b in barcode_fps)))
    sn_by_rp = get_sample_names_by_run_prefix(mapping_file)
    samples = []
    for f in forward_seqs:
        # getting just the main filename
        f = basename(f).split('_', 1)[1]
        # removing extentions: fastq or fastq.gz
        if 'fastq' in f.lower().rsplit('.', 2):
            f = f[:f.lower().rindex('.fastq')]
        # this try/except block is simply to retrieve all possible errors
        # and display them in the next if block
        try:
            samples.append(sn_by_rp[f])
            del sn_by_rp[f]
        except KeyError:
            pass

    if sn_by_rp:
        raise ValueError(
            'Some run_prefix values do not match your sample names: %s'
            % ', '.join(sn_by_rp.keys()))

    cmd = str("split_libraries_fastq.py --store_demultiplexed_fastq "
              "-i %s --sample_ids %s -o %s %s"
              % (','.join(forward_seqs), ','.join(samples),
                 output_dir, params_str))
    return cmd


def generate_split_libraries_fastq_cmd(filepaths, mapping_file, atype,
                                       out_dir, parameters):
    """Generates the split_libraries_fastq.py command

    Parameters
    ----------
    filepaths : list of (str, str)
        The artifact filepaths and their type
    mapping_file : str
        The artifact QIIME-compliant mapping file
    atype : str
        The artifact type
    out_dir : str
        The job output directory

    Returns
    -------
    str
        The CLI to execute

    Raises
    ------
    NotImplementedError
        If there is a not supported filepath type
    ValueError
        If the number of barcode files and the number of sequence files do not
        match
    """
    forward_seqs = []
    reverse_seqs = []
    barcode_fps = []
    for fp, fp_type in filepaths:
        if fp_type == 'raw_forward_seqs':
            forward_seqs.append(fp)
        elif fp_type == 'raw_reverse_seqs':
            reverse_seqs.append(fp)
        elif fp_type == 'raw_barcodes':
            barcode_fps.append(fp)
        else:
            raise NotImplementedError("File type not supported %s" % fp_type)

    # We need to sort the filepaths to make sure that each lane's file is in
    # the same order, so they match when passed to split_libraries_fastq.py
    # All files should be prefixed with run_prefix, so the ordering is
    # ensured to be correct
    forward_seqs = sorted(forward_seqs)
    reverse_seqs = sorted(reverse_seqs)
    barcode_fps = sorted(barcode_fps)

    output_dir = join(out_dir, "sl_out")

    params_str = generate_parameters_string()

    if atype == "per_sample_FASTQ":
        cmd = generate_per_sample_fastq_command(
            forward_seqs, reverse_seqs, barcode_fps, mapping_file,
            output_dir, params_str)
    else:
        if len(barcode_fps) != len(forward_seqs):
            raise ValueError("The number of barcode files and the number of "
                             "sequence files should match: %d != %s"
                             % (len(barcode_fps), len(forward_seqs)))

        map_out_dir = join(out_dir, 'mappings')
        mapping_files = sorted(split_mapping_file(mapping_file, map_out_dir))

        cmd = str("split_libraries_fastq.py --store_demultiplexed_fastq -i %s "
                  "-b %s -m %s -o %s %s"
                  % (','.join(forward_seqs), ','.join(barcode_fps),
                     ','.join(mapping_files), output_dir, params_str))

    return cmd, output_dir


def split_libraries_fastq(server_url, job_id, parameters, out_dir):
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
    # Step 1 get the rest of the information need to run split libraries
    update_job_step(server_url, job_id, "Step 1 of 4: Collecting information")
    artifact_id = parameters['input_data']
    filepaths, mapping_file, atype = get_artifact_information(
        server_url, artifact_id)

    # Step 2 generate the split libraries fastq command
    update_job_step(server_url, job_id, "Step 2 of 4: Generating command")
    command, sl_out = generate_split_libraries_fastq_cmd(
        filepaths, mapping_file, atype, out_dir, parameters)

    # Step 3 execute split libraries
    update_job_step(
        server_url, job_id,
        "Step 3 of 4: Executing demultiplexing and quality control")
    std_out, std_err, return_value = system_call(command)

    # Step 4 generate the demux file
    update_job_step(server_url, job_id, "Step 4 of 4: Generating demux file")
    generate_demux_file(sl_out)

    path_builder = partial(join, sl_out)
    filepaths = [(path_builder('seqs.fna'), 'preprocessed_fasta'),
                 (path_builder('seqs.fastq'), 'preprocessed_fastq'),
                 (path_builder('seqs.demux'), 'preprocessed_demux'),
                 (path_builder('split_library_log.txt'), 'log')]
    artifacts_info = ['Demultiplexed', filepaths, True, True]

    return format_payload(True, artifacts_info=artifacts_info)
