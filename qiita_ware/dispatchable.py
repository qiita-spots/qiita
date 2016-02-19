# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from .analysis_pipeline import RunAnalysis
from qiita_ware.commands import submit_EBI, submit_VAMPS
from qiita_db.analysis import Analysis
from qiita_db.artifact import Artifact


def submit_to_ebi(preprocessed_data_id, submission_type):
    """Submit a study to EBI"""
    submit_EBI(preprocessed_data_id, submission_type, True)


def submit_to_VAMPS(preprocessed_data_id):
    """Submit a study to VAMPS"""
    return submit_VAMPS(preprocessed_data_id)


def run_analysis(analysis_id, commands, comm_opts=None,
                 rarefaction_depth=None, merge_duplicated_sample_ids=False,
                 **kwargs):
    """Run an analysis"""
    analysis = Analysis(analysis_id)
    ar = RunAnalysis(**kwargs)
    return ar(analysis, commands, comm_opts, rarefaction_depth,
              merge_duplicated_sample_ids)


def create_raw_data(filetype, prep_template, filepaths):
    """Creates a new raw data

    Needs to be dispachable because it moves large files
    """
    Artifact.create(filepaths, filetype, prep_template=prep_template)


def copy_raw_data(prep_template, artifact_id):
    """Creates a new raw data by copying from artifact_id"""
    Artifact.copy(Artifact(artifact_id), prep_template)
