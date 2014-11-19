r"""
Util functions (:mod: `qiita_db.meta_util`)
===========================================

..currentmodule:: qiita_db.meta_util

This module provides utility functions that use the ORM objects. ORM objects
CANNOT import from this file.

Methods
-------

..autosummary::
    :toctree: generated/

    get_accessible_filepath_ids
"""
# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from __future__ import division

from .user import User
from .study import Study
from .data import RawData, PreprocessedData, ProcessedData
from .analysis import Analysis


def get_accessible_filepath_ids(user_id):
    """Gets all filepaths that this user should have access to

    This gets all raw, preprocessed, and processed filepaths, for studies
    that the user has access to, as well as all the mapping files and biom
    tables associated with the analyses that the user has access to.

    Returns
    -------
    set
        A set of filepath ids
    """
    user = User(user_id)

    # First, the studies
    # There are public, private, and shared studies
    study_ids = Study.get_public() + user.private_studies + \
        user.shared_studies

    def _get_study_fpids(constructor, object_id):
        obj = constructor(object_id)
        return [fpid for fpid, fp, fptid in obj.get_filepaths()]

    filepath_ids = []
    for study_id in study_ids:
        study = Study(study_id)

        # For each study, there are raw, preprocessed, and processed filepaths
        raw_data_ids = study.raw_data()
        preprocessed_data_ids = study.preprocessed_data()
        processed_data_ids = study.processed_data()

        for raw_data_id in raw_data_ids:
            filepath_ids.extend(_get_study_fpids(RawData, raw_data_id))

        for preprocessed_data_id in preprocessed_data_ids:
            filepath_ids.extend(_get_study_fpids(PreprocessedData,
                                                 preprocessed_data_id))

        for processed_data_id in processed_data_ids:
            filepath_ids.extend(_get_study_fpids(ProcessedData,
                                                 processed_data_id))

    # Next, analyses
    # Same as before, ther eare public, private, and shared
    analysis_ids = Analysis.get_public() + user.private_analyses + \
        user.shared_analyses

    for analysis_id in analysis_ids:
        analysis = Analysis(analysis_id)

        # For each analysis, there are mapping, biom, and job result filepaths
        # This call will get biom and mapping files
        filepath_ids.extend(analysis.all_associated_filepath_ids)

        # TODO: add job filepaths. See github.com/biocore/qiita/issues/636

    return set(filepath_ids)
