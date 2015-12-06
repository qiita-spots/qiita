# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from .analysis_pipeline import RunAnalysis
from qiita_ware.commands import submit_EBI, submit_VAMPS
from qiita_ware.executor import execute
from qiita_db.user import User
from qiita_db.software import Parameters, DefaultParameters
from qiita_db.analysis import Analysis
from qiita_db.artifact import Artifact


def processor(user_id, preprocessed_data_id, param_id):
    """Dispatch the processor work"""
    user = User(user_id)
    parameters = Parameters.from_default_params(
        DefaultParameters(param_id), {'input_data': preprocessed_data_id})
    return execute(user, parameters)


def preprocessor(user_id, artifact_id, param_id):
    """Dispatch for preprocessor work"""
    user = User(user_id)
    parameters = Parameters.from_default_params(
        DefaultParameters(param_id), {'input_data': artifact_id})
    return execute(user, parameters)


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
    Artifact.create(filepaths, filetype, prep_template=prep_template)
