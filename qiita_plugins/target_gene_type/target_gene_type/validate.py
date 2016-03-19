# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from os.path import basename, join, splitext
from json import loads
from shutil import copy

from h5py import File
from qiita_client import format_payload
from skbio.parse.sequences import load

# This is temporary. We should move the demux file format somewhere else
# (Jose) I'm planning to do this soon
from qiita_ware.demux import to_hdf5, to_ascii, format_fasta_record

FILEPATH_TYPE_DICT = {
    'SFF': ({'raw_sff'}, set()),
    'FASTQ': ({'raw_forward_seqs', 'raw_barcodes'}, {'raw_reverse_seqs'}),
    'FASTA': ({'raw_fasta', 'raw_qual'}, set()),
    'FASTA_Sanger': ({'raw_fasta'}, set()),
}


def _validate_multiple(qclient, job_id, prep_info, files, atype):
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
    unsupported_fp_types = set(files) - all_fp_types
    if unsupported_fp_types:
        return format_payload(
            success=False,
            error_msg="Filepath type(s) %s not supported by artifact "
                      "type %s. Supported filepath types: %s"
                      % (', '.join(unsupported_fp_types), atype,
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
            success=False, error_msg="Missing required filepath type(s): %s"
                                     % ', '.join(missing))

    # Check if there was any offending file
    if offending:
        error_list = ["%s: %s" % (k, v) for k, v in offending.items()]
        error_msg = ("Error creating artifact. Offending files:\n%s"
                     % '\n'.join(error_list))
        return format_payload(success=False, error_msg=error_msg)

    # Everything is ok
    filepaths = [[fps, fps_type] for fps_type, fps in files.items()]
    return format_payload(
        success=True, artifacts_info=[[None, atype, filepaths]])


def _validate_per_sample_FASTQ(qclient, job_id, prep_info, files):
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
    unsupported_fp_types = set(files) - {'raw_forward_seqs',
                                         'raw_reverse_seqs'}
    if unsupported_fp_types:
        return format_payload(
            success=False,
            error_msg="Filepath type(s) %s not supported by artifact "
                      "type per_sample_FASTQ. Supported filepath types: "
                      "raw_forward_seqs, raw_reverse_seqs"
                      % ', '.join(unsupported_fp_types))

    if 'raw_forward_seqs' not in files:
        return format_payload(
            success=False,
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
            success=False,
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
                success=False,
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
            success=False,
            error_msg=error_msg % (', '.join(fwd_fail), ', '.join(rev_fail)))

    filepaths = [[fps, fps_type] for fps_type, fps in files.items()]
    return format_payload(
        success=True, artifacts_info=[[None, 'per_sample_FASTQ', filepaths]])


def _validate_demux_file(qclient, job_id, prep_info, out_dir, demux_fp,
                         fastq_fp=None, fasta_fp=None, log_fp=None):
    """Validate and fix a 'demux' file and regenerate fastq and fasta files

    Parameters
    ----------
    qclient : qiita_client.QiitaClient
        The Qiita server client
    job_id : str
        The job id
    out_dir : str
        The output directory
    demux_fp : str
        The demux file path
    fastq_fp : str, optional
        The original fastq filepath. If demux is correct, it will not be
        regenerated
    fasta_fp : str, optional
        The original fasta filepath. If demux is correct, it will no be
        regenerated
    log_fp : str, optional
        The original log filepath

    Returns
    -------
    dict
        The results og the job
    """
    pt_sample_ids = set(prep_info)
    with File(demux_fp) as f:
        demux_sample_ids = set(f.keys())

    if not pt_sample_ids.issuperset(demux_sample_ids):
        # The demux sample ids are different from the ones in the prep template
        qclient.update_job_step(job_id, "Step 3: Fixing sample ids")
        # Atempt 1: the user provided the run prefix column - in this case the
        # run prefix column holds the sample ids present in the demux file
        if 'run_prefix' in prep_info[next(iter(pt_sample_ids))]:
            id_map = {v['run_prefix']: k for k, v in prep_info.items()}
            if not set(id_map).issuperset(demux_sample_ids):
                return format_payload(
                    success=False,
                    error_msg='The sample ids in the "run_prefix" columns '
                              'from the prep information do not match the '
                              'ones in the demux file. Please, correct the '
                              'column "run_prefix" in the prep information to '
                              'map the existing sample ids to the prep '
                              'information sample ids.')
        else:
            # Attempt 2: the sample ids in the demux table are the same that
            # in the prep template but without the prefix
            prefix = next(iter(pt_sample_ids)).split('.', 1)[0]
            prefixed = set("%s.%s" % (prefix, s) for s in demux_sample_ids)
            if pt_sample_ids.issuperset(prefixed):
                id_map = {s: "%s.%s" % (prefix, s) for s in demux_sample_ids}
            else:
                # There is nothing we can do. The samples in the demux file do
                # not match the ones in the prep template and we can't fix it
                return format_payload(
                    success=False,
                    error_msg='The sample ids in the demultiplexed files do '
                              'not match the ones in the prep information. '
                              'Please, provide the column "run_prefix" in '
                              'the prep information to map the existing sample'
                              ' ids to the prep information sample ids.')
        # Fix the sample ids
        # Do not modify the original demux file, copy it to a new location
        new_demux_fp = join(out_dir, basename(demux_fp))
        copy(demux_fp, new_demux_fp)
        # Need to catch an error
        with File(new_demux_fp, 'r+') as f:
            for old in f:
                f.move(old, id_map[old])

        # When we fix, we always generate the FASTQ and FASTA file
        # By setting them to None, below will be generated
        demux_fp = new_demux_fp
        fastq_fp = None
        fasta_fp = None

    # If we didn't fix anything, we only generate the files if they don't
    # already exists
    name = splitext(basename(demux_fp))[0]
    if not fastq_fp:
        fastq_fp = join(out_dir, "%s.fastq" % name)
        with open(fastq_fp, 'w') as fq:
            with File(demux_fp, 'r') as dx:
                for record in to_ascii(dx):
                    fq.write(record)

    if not fasta_fp:
        fasta_fp = join(out_dir, "%s.fasta" % name)
        with open(fasta_fp, 'w') as f:
            for r in load(fastq_fp):
                f.write(format_fasta_record(r['SequenceID'], r['Sequence'],
                                            r['Qual']))

    filepaths = [[[fastq_fp], 'preprocessed_fastq'],
                 [[fasta_fp], 'preprocessed_fasta'],
                 [[demux_fp], 'preprocessed_demux']]
    if log_fp:
        filepaths.append([[log_fp], 'log'])
    return format_payload(
        success=True, artifacts_info=[[None, 'Demultiplexed', filepaths]])


def _validate_demultiplexed(qclient, job_id, prep_info, files, out_dir):
    """Validate and fix a new 'Demultiplexed' artifact

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
    out_dir : str
        The output directory

    Returns
    -------
    dict
        The results of the job
    """
    qclient.update_job_step(job_id, "Step 2: Validating 'Demultiplexed' files")

    supported_fp_types = {'preprocessed_fasta', 'preprocessed_fastq',
                          'preprocessed_demux', 'log'}
    unsupported_fp_types = set(files) - supported_fp_types
    if unsupported_fp_types:
        return format_payload(
            success=False,
            error_msg="Filepath type(s) %s not supported by artifact type "
                      "Demultiplexed. Supported filepath types: %s"
                      % (', '.join(unsupported_fp_types),
                         ', '.join(sorted(supported_fp_types)))
        )

    # At most one file of each type can be provided
    offending = set(fp_t for fp_t, fps in files.items() if len(fps) > 1)
    if offending:
        errors = ["%s (%d): %s"
                  % (fp_t, len(files[fp_t]), ', '.join(files[fp_t]))
                  for fp_t in sorted(offending)]
        return format_payload(
            success=False,
            error_msg="Only one file of each filepath type is supported. %s"
                      % "; ".join(errors))

    # Check which files we have available:
    fasta = (files['preprocessed_fasta'][0]
             if 'preprocessed_fasta' in files else None)
    fastq = (files['preprocessed_fastq'][0]
             if 'preprocessed_fastq' in files else None)
    demux = (files['preprocessed_demux'][0]
             if 'preprocessed_demux' in files else None)
    log = (files['log'][0] if 'log' in files else None)
    if demux:
        # If demux is available, use that one to perform the validation and
        # generate the fasta and fastq from it
        payload = _validate_demux_file(qclient, job_id, prep_info, out_dir,
                                       demux, log_fp=log)
    elif fastq:
        # Generate the demux file from the fastq
        demux = join(out_dir, "%s.demux" % splitext(basename(fastq))[0])
        with File(demux, "w") as f:
            to_hdf5(fastq, f)
        # Validate the demux, providing the original fastq
        payload = _validate_demux_file(qclient, job_id, prep_info, out_dir,
                                       demux, fastq_fp=fastq, log_fp=log)
    elif fasta:
        # Generate the demux file from the fasta
        demux = join(out_dir, "%s.demux" % splitext(basename(fasta))[0])
        with File(demux, "w") as f:
            to_hdf5(fasta, f)
        # Validate the demux, providing the original fasta
        payload = _validate_demux_file(qclient, job_id, prep_info, out_dir,
                                       demux, fasta_fp=fasta, log_fp=log)
    else:
        payload = format_payload(
            success=False,
            error_msg="Either a 'preprocessed_demux', 'preprocessed_fastq' or "
                      "'preprocessed_fasta' file should be provided.")

    return payload


def validate(qclient, job_id, parameters, out_dir):
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
    prep_info = qclient.get("/qiita_db/prep_template/%s/data/" % prep_id)
    if not prep_info or not prep_info['success']:
        error_msg = "Could not get prep information: %s"
        if prep_info:
            error_msg = error_msg % prep_info['error']
        else:
            error_msg = error_msg % "could not connect with the server"
        raise ValueError(error_msg)
    prep_info = prep_info['data']

    if a_type in ['SFF', 'FASTQ', 'FASTA', 'FASTA_Sanger']:
        _validate_multiple(qclient, job_id, prep_info, files, a_type)
    elif a_type == 'per_sample_FASTQ':
        _validate_per_sample_FASTQ(qclient, job_id, prep_info, files)
    elif a_type == 'Demultiplexed':
        _validate_demultiplexed(qclient, job_id, prep_info, files, out_dir)
    else:
        return format_payload(
            success=False,
            error_msg="Unknown artifact_type %s. Supported types: 'SFF', "
                      "'FASTQ', 'FASTA', 'FASTA_Sanger', 'per_sample_FASTQ', "
                      "'Demultiplexed'" % a_type)
