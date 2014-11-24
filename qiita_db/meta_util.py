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
from .metadata_template import PrepTemplate, SampleTemplate


def _get_data_fpids(constructor, object_id):
    """Small function for getting filepath IDS associated with data object

    Parameters
    ----------
    constructor : a subclass of BaseData
        E.g., RawData, PreprocessedData, or ProcessedData
    object_id : int
        The ID of the data object

    Returns
    -------
    set of int
    """
    obj = constructor(object_id)
    return {fpid for fpid, _, _ in obj.get_filepaths()}


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
    study_ids = Study.get_by_status('public') + user.user_studies + \
        user.shared_studies

    filepath_ids = set()
    for study_id in study_ids:
        study = Study(study_id)

        # For each study, there are raw, preprocessed, and processed filepaths
        raw_data_ids = study.raw_data()
        preprocessed_data_ids = study.preprocessed_data()
        processed_data_ids = study.processed_data()

        constructor_data_ids = ((RawData, raw_data_ids),
                                (PreprocessedData, preprocessed_data_ids),
                                (ProcessedData, processed_data_ids))

        for constructor, data_ids in constructor_data_ids:
            for data_id in data_ids:
                filepath_ids.update(_get_data_fpids(constructor, data_id))

        # adding prep and sample templates
        prep_fp_ids = []
        for rdid in study.raw_data():
            for pt_id in RawData(rdid).prep_templates:
                for _id, _ in PrepTemplate(pt_id).get_filepaths():
                    prep_fp_ids.append(_id)
        filepath_ids.update(prep_fp_ids)

        if SampleTemplate.exists(study_id):
            sample_fp_ids = [_id for _id, _
                             in SampleTemplate(study_id).get_filepaths()]
            filepath_ids.update(sample_fp_ids)

    # Next, analyses
    # Same as before, ther eare public, private, and shared
    analysis_ids = Analysis.get_by_status('public') + user.private_analyses + \
        user.shared_analyses

    for analysis_id in analysis_ids:
        analysis = Analysis(analysis_id)

        # For each analysis, there are mapping, biom, and job result filepaths
        # This call will get biom and mapping files
        filepath_ids.update(analysis.all_associated_filepath_ids)

        # TODO: add job filepaths. See github.com/biocore/qiita/issues/636

    return filepath_ids
