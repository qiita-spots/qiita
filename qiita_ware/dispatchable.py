from traceback import format_exception_only
from sys import exc_info

from .processing_pipeline import StudyPreprocessor
from .analysis_pipeline import RunAnalysis
from qiita_ware.commands import submit_EBI
from qiita_db.study import Study
from qiita_db.analysis import Analysis
from qiita_db.metadata_template import PrepTemplate
from qiita_db.data import RawData


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
    study_acc, submission_acc = submit_EBI(preprocessed_data_id,
                                           submission_type,
                                           True)

    return study_acc, submission_acc


def run_analysis(user_id, analysis_id, commands, comm_opts=None,
                 rarefaction_depth=None):
    """Run a meta-analysis"""
    analysis = Analysis(analysis_id)
    ar = RunAnalysis()
    return ar(user_id, analysis, commands, comm_opts, rarefaction_depth)


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
