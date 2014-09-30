# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from os.path import join
from os import makedirs
from functools import partial

from qiita_db.study import Study
from qiita_db.metadata_template import PrepTemplate, SampleTemplate
from qiita_ware.ebi import EBISubmission


def generate(study_id, output_dir, action, investigation_type):
    # Get study information from database
    study_id_str = str(study_id)
    study = Study(study_id)
    submission = EBISubmission(study_id_str, study.title,
                               study.info['study_abstract'],
                               investigation_type)

    # Get study-specific output directory and set filepaths
    get_output_fp = partial(join, output_dir)
    study_fp = get_output_fp('study.xml')
    sample_fp = get_output_fp('sample.xml')
    experiment_fp = get_output_fp('experiment.xml')
    run_fp = get_output_fp('run.xml')
    submission_fp = get_output_fp('submission.xml')
    sample_template_fp = get_output_fp('sample_template.tsv')

    sample_template = SampleTemplate(study.sample_template)
    sample_template.to_file(sample_template_fp)

    submission.write_all_xml_files(study_fp, sample_fp, experiment_fp, run_fp,
                                   submission_fp, action)


def generate_from_files(study_id, sample_template, prep_template_fps,
                        fastq_dir, investigation_type, output_dir):
    study = Study(study_id)
    study_id_str = str(study_id)

    prep_templates = [open(prep_template_fp)
                      for prep_template_fp in prep_template_fps]

    submission = from_templates_and_per_sample_fastqs(
        study_id_str, study.title, study.info['study_abstract'],
        investigation_type, sample_template, prep_templates, fastq_dir)

    # Get study-specific output directory and set filepaths
    get_output_fp = partial(join, output_dir)
    study_fp = get_output_fp('study.xml')
    sample_fp = get_output_fp('sample.xml')
    experiment_fp = get_output_fp('experiment.xml')
    run_fp = get_output_fp('run.xml')
    submission_fp = get_output_fp('submission.xml')

    submission.write_all_xml_files(study_fp, sample_fp, experiment_fp, run_fp,
                                   submission_fp, action)

    for prep_template in prep_templates:
        prep_template.close()
