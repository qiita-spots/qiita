# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from os.path import join, isdir
from os import makedirs
from functools import partial

from qiita_db.study import Study
from qiita_db.data import PreprocessedData
from qiita_ware.ebi import EBISubmission


ebi_actions = ['ADD', 'VALIDATE', 'MODIFY']


def submit_EBI_from_files(preprocessed_data_id, sample_template, prep_template,
                          fastq_dir_fp, output_dir_fp, investigation_type,
                          action, send, new_investigation_type=None):
    """EBI submission from files

    Parameters
    ----------
    preprocessed_data_id : int
        The preprocesssed data id
    sample_template : File
        The file handler of the sample template file
    prep_template : File
        The file handler of the prep template file
    fastq_dir_fp : str
        The fastq filepath
    output_dir_fp : str
        The output directory
    investigation_type : str
        The investigation type string
    action : %s
        The action to perform with this data
    send : bool
        True to actually send the files
    new_investigation_type : str, optional
        If investigation_type is `'Other'` then a value describing this new
        investigation type should be specified. 'mimarks-survey' or
        'metagenomics' are commonly used.
    """

    preprocessed_data = PreprocessedData(preprocessed_data_id)
    preprocessed_data_id_str = str(preprocessed_data_id)
    study = Study(preprocessed_data.study)

    # Get study-specific output directory and set filepaths
    get_output_fp = partial(join, output_dir_fp)
    study_fp = get_output_fp('study.xml')
    sample_fp = get_output_fp('sample.xml')
    experiment_fp = get_output_fp('experiment.xml')
    run_fp = get_output_fp('run.xml')
    submission_fp = get_output_fp('submission.xml')

    if not isdir(output_dir_fp):
        makedirs(output_dir_fp)
    else:
        raise ValueError('The output folder already exists: %s' %
                         output_dir_fp)

    # this is a know issue and @ElDeveloper is working on a fix:
    # https://github.com/biocore/qiita/pull/522
    if investigation_type == "Other":
        investigation_type = 'Amplicon Sequencing'
    submission = EBISubmission.from_templates_and_per_sample_fastqs(
        preprocessed_data_id_str, study.title, study.info['study_abstract'],
        investigation_type, sample_template, prep_template,
        fastq_dir_fp, new_investigation_type=new_investigation_type,
        pmids=study.pmids)

    submission.write_all_xml_files(study_fp, sample_fp, experiment_fp, run_fp,
                                   submission_fp, action)

    if send:
        submission.send_sequences()
        study_accession, submission_accession = submission.send_xml()
    else:
        study_accession, submission_accession = None, None

    return study_accession, submission_accession


submit_EBI_from_files.__doc__ %= ebi_actions
