# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from os.path import join, basename, splitext

from tgp.util import update_job_step, system_call, format_payload
from .util import (get_artifact_information, split_mapping_file,
                   generate_demux_file, generate_artifact_info)


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

    Raises
    ------
    ValueError
        If the value for the 'reverse_primers' parameter is not one of
        `["disable", "truncate_only", "truncate_remove"]`
    """
    accepted_vals = ["disable", "truncate_only", "truncate_remove"]
    if parameters['reverse_primers'] not in accepted_vals:
        raise ValueError(
            "Value for 'reverse_primers' not recognized: %s. Please, choose a "
            "value from %s" % (parameters['reverse_primers'],
                               ', '.join(accepted_vals)))

    flag_params = ['trim_seq_length', 'disable_bc_correction',
                   'disable_primers', 'truncate_ambi_bases']
    str_params = ['min_seq_len', 'max_seq_len', 'min_qual_score', 'max_ambig',
                  'max_homopolymer', 'max_primer_mismatch', 'barcode_type',
                  'max_barcode_errors', 'qual_score_window',
                  'reverse_primer_mismatches', 'reverse_primers']

    result = ["--%s %s" % (sp, parameters[sp]) for sp in str_params]
    for fp in flag_params:
        if parameters[fp]:
            result.append("--%s" % fp)
    return ' '.join(result)


def generate_process_sff_commands(sffs, out_dir):
    """Processes the sff files in `sffs`

    Parameters
    ----------
    sffs : list of str
        The list of sff filepaths
    out_dir : str
        The path of the output directory

    Returns
    -------
    list of str, list of str, list of str
        The list of process_sff.py commands
        The list of fasta filepaths
        The list of qual filepaths
    """
    sff_cmd_template = "process_sff.py -i %s -o %s"
    seqs = []
    quals = []
    cmds = []
    for sff in sffs:
        base = splitext(basename(sff))[0]
        if sff.endswith('.gz'):
            base = splitext(base)[0]

        cmds.append(sff_cmd_template % (sff, out_dir))
        seqs.append(join(out_dir, '%s.fna' % base))
        quals.append(join(out_dir, '%s.qual' % base))

    return cmds, seqs, quals


def generate_split_libraries_cmd(seqs, quals, mapping_file, out_dir, params):
    """Generates the split libraries commands

    Parameters
    ----------
    seqs : list of str
        The fasta filepaths
    quals : list of str
        The qual filepaths
    mapping_file : str
        The mapping file filepath
    out_dir : str
        The job output directory
    params : dict
        The command's parameters, keyed by parameter name

    Returns
    -------
    list of str, list of str
        The list of split_libraries.py commands
        The list of the split_libraries.py output directory filepaths

    Raises
    ------
    ValueError
        If the number of seqs files do not match the number of values specified
        in the `run_prefix` column in the mapping file
    """
    map_out_dir = join(out_dir, 'mappings')
    mapping_files = sorted(split_mapping_file(mapping_file, map_out_dir))
    params_str = generate_parameters_string(params)
    cmds = []
    out_dirs = []

    if len(mapping_files) == 1:
        qual_str = "-q %s -d" % ','.join(quals) if quals else ""
        cmds = ["split_libraries.py -f %s -m %s %s -o %s %s"
                % (','.join(seqs), mapping_files[0], qual_str, out_dir,
                   params_str)]
        out_dirs = [out_dir]
    else:
        len_seqs = len(seqs)
        len_mapping_files = len(mapping_files)

        if len_mapping_files != len_seqs:
            mapping_files = [basename(m) for m in mapping_files]
            seqs = [basename(s) for s in seqs]
            raise ValueError(
                "Your run prefix column defines '%s', but you have '%s' "
                "as sequence files"
                % (', '.join(mapping_files), ', '.join(seqs)))
        n = 1
        for i, (seq, mapping) in enumerate(zip(seqs, mapping_files)):
            qual_str = '-q %s -d' % quals[i] if quals else ''
            split_dir = join(out_dir, splitext(basename(mapping))[0])
            out_dirs.append(split_dir)
            cmds.append("split_libraries.py -f %s -m %s %s -o %s -n %s %s"
                        % (seq, mapping, qual_str, split_dir, n, params_str))
            # Number comes from (100K larger than amplicon):
            # http://454.com/products/gs-FLX-system/index.asp
            n = (i + 1) * 800000

    return cmds, out_dirs


def split_libraries(server_url, job_id, parameters, out_dir):
    """Run split libraries with the given parameters

    Parameters
    ----------
    server_url : str
        The URL of the server
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
    NotImplementedError
        If one of the filepath types attached to the artifact is not recognized
    ValueError
        If the artifact has SFF and fasta files
        IF the artifact has qual files but not fasta files
        If the artifact has fasta files but not quals
    RuntimeError
        If there is an error processing an sff file
        If there is an error running split_libraries.py
        If there is an error merging the results
    """
    # Step 1 get the rest of the information need to run split libraries
    update_job_step(server_url, job_id, "Step 1 of 4: Collecting information")
    artifact_id = parameters['input_data']
    filepaths, mapping_file, atype = get_artifact_information(
        server_url, artifact_id)

    # Step 2 generate the split libraries command
    update_job_step(server_url, job_id, "Step 2 of 4: preparing files")
    sffs = []
    seqs = []
    quals = []
    for fp, fp_type in filepaths:
        if fp_type == 'raw_sff':
            sffs.append(fp)
        elif fp_type == 'raw_fasta':
            seqs.append(fp)
        elif fp_type == 'raw_qual':
            quals.append(fp)
        else:
            raise NotImplementedError("File type not supported %s" % fp_type)

    if seqs and sffs:
        raise ValueError('Cannot have SFF and raw fasta on the same artifact')
    elif quals and not seqs:
        raise ValueError('Cannot have just qual files on the artifact, you '
                         'also need raw fasta files')
    elif seqs and not quals:
        raise ValueError('It is not currently possible to process fasta '
                         'file(s) without qual file(s). This will be '
                         'supported in the future. You can track progress on '
                         'this by following: '
                         'https://github.com/biocore/qiita/issues/953')
    elif seqs:
        seqs = sorted(seqs)
        quals = sorted(quals)
    else:
        cmds, seqs, quals = generate_process_sff_commands(sffs, out_dir)
        len_cmds = len(cmds)
        for i, cmd in enumerate(cmds):
            update_job_step(
                server_url, job_id,
                "Step 2 of 4: preparing files (processing sff file %d of %d)"
                % (i, len_cmds))
            std_out, std_err, return_value = system_call(cmd)
            if return_value != 0:
                raise RuntimeError(
                    "Error processing sff file:\nStd output: %s\n Std error:%s"
                    % (std_out, std_err))

    output_dir = join(out_dir, 'sl_out')

    commands, sl_outs = generate_split_libraries_cmd(
        seqs, quals, mapping_file, output_dir, parameters)

    # Step 3 execute split libraries
    cmd_len = len(commands)
    for i, cmd in enumerate(commands):
        update_job_step(
            server_url, job_id,
            "Step 3 of 4: Executing demultiplexing and quality control "
            "(%d of %d)" % (i, cmd_len))
        std_out, std_err, return_value = system_call(cmd)
        if return_value != 0:
            raise RuntimeError(
                "Error running split libraries:\nStd output: %s\nStd error:%s"
                % (std_out, std_err))

    # Step 4 merging results
    if cmd_len > 1:
        update_job_step(
            server_url, job_id,
            "Step 4 of 4: Merging results (concatenating files)")
        to_cat = ['split_library_log.txt', 'seqs.fna']
        if quals:
            to_cat.append('seqs_filtered.qual')
        for tc in to_cat:
            files = [join(x, tc) for x in sl_outs]
            cmd = "cat %s > %s" % (' '.join(files), join(output_dir, tc))
            std_out, std_err, return_value = system_call(cmd)
            if return_value != 0:
                raise RuntimeError(
                    "Error concatenating %s files:\nStd output: %s\n"
                    "Std error:%s" % (tc, std_out, std_err))
        if quals:
            update_job_step(
                server_url, job_id,
                "Step 4 of 4: Merging results (converting fastqual to fastq)")
            cmd = ("convert_fastaqual_fastq.py -f %s -q %s -o %s -F"
                   % (join(output_dir, 'seqs.fna'),
                      join(output_dir, 'seqs_filtered.qual'),
                      output_dir))
    update_job_step(
        server_url, job_id,
        "Step 4 of 4: Merging results (generating demux file)")

    generate_demux_file(output_dir)

    artifacts_info = generate_artifact_info(output_dir)

    return format_payload(True, artifacts_info=artifacts_info)
