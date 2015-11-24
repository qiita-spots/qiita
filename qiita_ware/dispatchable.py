# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from traceback import format_exception_only
from sys import exc_info

from .processing_pipeline import StudyPreprocessor, StudyProcessor
from .analysis_pipeline import RunAnalysis
from qiita_ware.commands import submit_EBI, submit_VAMPS
from qiita_db.study import Study
from qiita_db.analysis import Analysis
from qiita_db.metadata_template.prep_template import PrepTemplate


def processor(preprocessed_data_id, param_id, param_constructor):
    """Dispatch the processor work"""
    preprocessed_data = PreprocessedData(preprocessed_data_id)
    params = param_constructor(param_id)

    sp = StudyProcessor()
    try:
        process_out = sp(preprocessed_data, params)
    except Exception as e:
        error_msg = ''.join(format_exception_only(e, exc_info()))
        preprocessed_data.processing_status = "failed: %s" % error_msg
        process_out = None

    return process_out


def preprocessor(study_id, prep_template_id, param_id, param_constructor):
    """Dispatch for preprocessor work"""
    study = Study(study_id)
    prep_template = PrepTemplate(prep_template_id)
    params = param_constructor(param_id)

    sp = StudyPreprocessor()
    try:
        preprocess_out = sp(study, prep_template, params)
    except Exception as e:
        error_msg = ''.join(format_exception_only(e, exc_info()))
        prep_template.preprocessing_status = "failed: %s" % error_msg
        preprocess_out = None

    return preprocess_out


def submit_to_ebi(preprocessed_data_id, submission_type):
    """Submit a study to EBI"""
    submit_EBI(preprocessed_data_id, submission_type, True)


def submit_to_VAMPS(preprocessed_data_id):
    """Submit a study to VAMPS"""
    return submit_VAMPS(preprocessed_data_id)


def run_analysis(analysis_id, commands, comm_opts=None,
                 rarefaction_depth=None, **kwargs):
    """Run an analysis"""
    analysis = Analysis(analysis_id)
    ar = RunAnalysis(**kwargs)
    return ar(analysis, commands, comm_opts, rarefaction_depth)


def create_raw_data(filetype, prep_template, filepaths):
    """Creates a new raw data

    Needs to be dispachable because it moves large files
    """
    RawData.create(filetype, [prep_template], filepaths)


def add_files_to_raw_data(raw_data_id, filepaths):
    """Add files to raw data

    Needs to be dispachable because it moves large files
    """
    rd = RawData(raw_data_id)
    rd.add_filepaths(filepaths)


def unlink_all_files(raw_data_id):
    """Removes all files from raw data

    Needs to be dispachable because it does I/O and a lot of DB calls
    """
    rd = RawData(raw_data_id)
    rd.clear_filepaths()
