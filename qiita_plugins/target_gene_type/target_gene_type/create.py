# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from os.path import basename
from json import loads

from qiita_client import format_payload

FILEPATH_TYPE_DICT = {
    'SFF': ({'raw_sff'}, set()),
    'FASTQ': ({'raw_forward_seqs', 'raw_barcodes'}, {'raw_reverse_seqs'}),
    'FASTA': ({'raw_fasta', 'raw_qual'}, set()),
    'FASTA_Sanger': ({'raw_fasta'}, set()),
}


def _create_artifact_run_prefix(qclient, job_id, prep_info, files, atype):
    """Validae and fix a new 'SFF', 'FASTQ', 'FASTA' or 'FASTA_Sanger' artifact

    Parameters
    ----------
    qclient : qiita_client.QiitaClient
        The Qiita server client
    job_id : str
        The job id
    prep_info : dict of {str: dict of {str: str}}
        The prep information keyed by sample id
    files : dict of {str: list of str}
        The files to add to the new artifact, keyed by filepath type
    atype: str
        The type of the artifact

    Returns
    -------
    dict
        The results of the job
    """
    qclient.update_job_step(job_id, "Step 2: Validating '%s' files" % atype)
    req_fp_types, opt_fp_types = FILEPATH_TYPE_DICT[atype]
    all_fp_types = req_fp_types | opt_fp_types

    # Check if there is any filepath type that is not supported
    not_supported_fp_types = set(files) - all_fp_types
    if not_supported_fp_types:
        return format_payload(
            False,
            error_msg="Filepath type(s) %s not supported by artifact "
                      "type %s. Supported filepath types: %s"
                      % (', '.join(not_supported_fp_types), atype,
                         ', '.join(sorted(all_fp_types))))

    # Check if the run_prefix column is present in the prep info
    offending = {}
    types_seen = set()
    if 'run_prefix' in prep_info[next(iter(prep_info))]:
        # We can potentially have more than one lane in the prep information
        # so check that the provided files are prefixed with the values in
        # the run_prefix column
        run_prefixes = set(v['run_prefix'] for k, v in prep_info.items())
        num_prefixes = len(run_prefixes)

        # Check those filepath types that are required
        for ftype, t_files in files.items():
            if num_prefixes != len(t_files):
                offending[ftype] = (
                    "The number of provided files (%d) doesn't match the "
                    "number of run prefix values in the prep info (%d): %s"
                    % (len(t_files), num_prefixes,
                       ', '.join(basename(f) for f in t_files)))
            else:
                fail = [basename(fp) for fp in t_files
                        if not basename(fp).startswith(tuple(run_prefixes))]
                if fail:
                    offending[ftype] = (
                        "The provided files do not match the run prefix "
                        "values in the prep information: %s" % ', '.join(fail))

            types_seen.add(ftype)
    else:
        # If the run prefix column is not provided, we only allow a single
        # lane, so check that we have a single file for each provided
        # filepath type
        for ftype, t_files in files.items():
            if len(t_files) != 1:
                offending[ftype] = (
                    "Only one file per type is allowed. Please provide the "
                    "column 'run_prefix' if you need more than one file per "
                    "type: %s" % ', '.join(basename(fp) for fp in t_files))

            types_seen.add(ftype)

    # Check that all required filepath types where present
    missing = req_fp_types - types_seen
    if missing:
        return format_payload(
            False, error_msg="Missing required filepath type(s): %s"
                             % ', '.join(missing))

    # Check if there was any offending file
    if offending:
        error_list = ["%s: %s" % (k, v) for k, v in offending.items()]
        error_msg = ("Error creating artifact. Offending files:\n%s"
                     % '\n'.join(error_list))
        return format_payload(False, error_msg=error_msg)

    # Everything is ok
    filepaths = [[fps, fps_type] for fps_type, fps in files.items()]
    return format_payload(True, artifacts_info=[[None, atype, filepaths]])


def _create_artifact_per_sample(qclient, job_id, prep_info, files):
    """Validae and fix a new 'per_sample_FASTQ' artifact

    Parameters
    ----------
    qclient : qiita_client.QiitaClient
        The Qiita server client
    job_id : str
        The job id
    prep_info : dict of {str: dict of {str: str}}
        The prep information keyed by sample id
    files : dict of {str: list of str}
        The files to add to the new artifact, keyed by filepath type

    Returns
    -------
    dict
        The results of the job
    """
    qclient.update_job_step(
        job_id, "Step 2: Validating 'per_sample_FASTQ' files")

    samples = prep_info.keys()
    samples_count = len(samples)

    # Check if there is any filepath type that is not supported
    not_supported_fp_types = set(files) - {'raw_forward_seqs',
                                           'raw_reverse_seqs'}
    if not_supported_fp_types:
        return format_payload(
            False,
            error_msg="Filepath type(s) %s not supported by artifact "
                      "type per_sample_FASTQ. Supported filepath types: "
                      "raw_forward_seqs, raw_reverse_seqs"
                      % ', '.join(not_supported_fp_types))

    if 'raw_forward_seqs' not in files:
        return format_payload(
            False,
            error_msg="Missing required filepath type: raw_forward_seqs")

    # Make sure that we hve the same number of files than samples
    fwd_count = len(files['raw_forward_seqs'])
    counts_match = fwd_count == samples_count
    if 'raw_reverse_seqs' in files:
        rev_count = len(files['raw_reverse_seqs'])
        counts_match = counts_match and (rev_count == samples_count)
    else:
        rev_count = 0

    if not counts_match:
        return format_payload(
            False,
            error_msg="The number of provided files doesn't match the "
                      "number of samples (%d): %d raw_forward_seqs, "
                      "%d raw_reverse_seqs (optional, 0 is ok)"
                      % (samples_count, fwd_count, rev_count))

    if 'run_prefix' in prep_info[samples[0]]:
        # The column 'run_prefix' is present in the prep information.
        # Make sure that twe have the same number of run_prefix values
        # than the number of samples
        run_prefixes = [v['run_prefix'] for k, v in prep_info.items()]
        if samples_count != len(set(run_prefixes)):
            repeated = ["%s (%d)" % (p, run_prefixes.count(p))
                        for p in set(run_prefixes)
                        if run_prefixes.count(p) > 1]
            return format_payload(
                False,
                error_msg="The values for the column 'run_prefix' are not "
                          "unique for each sample. Repeated values: %s"
                          % ', '.join(repeated))

        error_msg = ("The provided files do not match the run prefix values "
                     "in the prep information. Offending files: "
                     "raw_forward_seqs: %s, raw_reverse_seqs: %s")
    else:
        # The column 'run_prefix' is not in the prep template. In this case,
        # check that the files are prefixed by the sample ids without the
        # study id
        run_prefixes = [sid.split('.', 1)[1] for sid in samples]
        error_msg = ("The provided files are not prefixed by sample id. "
                     "Please provide the 'run_prefix' column in your prep "
                     "information. Offending files: raw_forward_seqs: %s, "
                     "raw_reverse_seqs: %s")

    # Check that the provided files match the run prefixes
    fwd_fail = [basename(fp) for fp in files['raw_forward_seqs']
                if not basename(fp).startswith(tuple(run_prefixes))]
    if rev_count > 0:
        rev_fail = [basename(fp) for fp in files['raw_reverse_seqs']
                    if not basename(fp).startswith(tuple(run_prefixes))]
    else:
        rev_fail = []

    if fwd_fail or rev_fail:
        return format_payload(
            False,
            error_msg=error_msg % (', '.join(fwd_fail), ', '.join(rev_fail)))

    filepaths = [[fps, fps_type] for fps_type, fps in files.items()]
    return format_payload(
        True, artifacts_info=[[None, 'per_sample_FASTQ', filepaths]])


def _create_artifact_demultiplexed(qclient, job_id, prep_info, files):
    """Validae and fix a new 'Demultiplexed' artifact

    Parameters
    ----------
    qclient : qiita_client.QiitaClient
        The Qiita server client
    job_id : str
        The job id
    prep_info : dict of {str: dict of {str: str}}
        The prep information keyed by sample id
    files : dict of {str: list of str}
        The files to add to the new artifact, keyed by filepath type

    Returns
    -------
    dict
        The results of the job
    """
    qclient.update_job_step(job_id, "Step 2: Validating 'Demultiplexed' files")

    supported_fp_types = {'preprocessed_fasta', 'preprocessed_fastq',
                          'preprocessed_demux', 'log'}
    not_supported_fp_types = set(files) - supported_fp_types
    if not_supported_fp_types:
        return format_payload(
            False,
            error_msg="Filepath type(s) %s not supported by artifact type "
                      "Demultiplexed. Supported filepath types: %s"
                      % (', '.join(not_supported_fp_types),
                         ', '.join(sorted(supported_fp_types)))
        )

    samples = prep_info.keys()
    samples_count = len(samples)


def create_artifact(qclient, job_id, parameters, out_dir):
    """Validae and fix a new artifact

    Parameters
    ----------
    qclient : qiita_client.QiitaClient
        The Qiita server client
    job_id : str
        The job id
    parameters : dict
        The parameter values to validate and create the artifact
    out_dir : str
        The path to the job's output directory

    Returns
    -------
    dict
        The results of the job

    Raises
    ------
    ValueError
        If there is any error gathering the information from the server
    """
    prep_id = parameters['template']
    files = loads(parameters['files'])
    a_type = parameters['artifact_type']

    qclient.update_job_step(job_id, "Step 1: Collecting prep information")
    prep_info = qclient.get("/qiita_db/prep_template/%s/data" % prep_id)
    if not prep_info or not prep_info['success']:
        error_msg = "Could not get prep information: %s"
        if prep_info:
            error_msg = error_msg % prep_info['error']
        else:
            error_msg = error_msg % "could not connect with the server"
        raise ValueError(error_msg)
    prep_info = prep_info['data']

    if a_type in ['SFF', 'FASTQ', 'FASTA', 'FASTA_Sanger']:
        _create_artifact_run_prefix(qclient, job_id, prep_info, files, a_type)
    elif a_type == 'per_sample_FASTQ':
        _create_artifact_per_sample(qclient, job_id, prep_info, files)
    elif a_type == 'Demultiplexed':
        _create_artifact_demultiplexed(qclient, job_id, prep_info, files)
    else:
        return format_payload(
            False,
            error_msg="Unknown artifact_type %s. Supported types: 'SFF', "
                      "'FASTQ', 'FASTA', 'FASTA_Sanger', 'per_sample_FASTQ', "
                      "'Demultiplexed'")
