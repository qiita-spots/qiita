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
    get_lat_longs
"""
# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from __future__ import division

from itertools import chain

from qiita_core.qiita_settings import qiita_config
from .study import Study
from .data import RawData, PreprocessedData, ProcessedData
from .analysis import Analysis
from .sql_connection import TRN
from .metadata_template import PrepTemplate, SampleTemplate
from .portal import Portal


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
    with TRN:
        obj = constructor(object_id)
        return {fpid for fpid, _, _ in obj.get_filepaths()}


def get_accessible_filepath_ids(user):
    """Gets all filepaths that this user should have access to

    This gets all raw, preprocessed, and processed filepaths, for studies
    that the user has access to, as well as all the mapping files and biom
    tables associated with the analyses that the user has access to.

    Parameters
    ----------
    user : User object
        The user we are interested in


    Returns
    -------
    set
        A set of filepath ids

    Notes
    -----
    Admins have access to all files, so all filepath ids are returned for
    admins
    """
    with TRN:
        if user.level == "admin":
            # admins have access all files
            TRN.add("SELECT filepath_id FROM qiita.filepath")
            return set(TRN.execute_fetchflatten())

        # First, the studies
        # There are private and shared studies
        study_ids = user.user_studies | user.shared_studies

        filepath_ids = set()
        for study_id in study_ids:
            study = Study(study_id)

            # For each study, there are raw, preprocessed, and
            # processed filepaths
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
                    # related to https://github.com/biocore/qiita/issues/596
                    if PrepTemplate.exists(pt_id):
                        for _id, _ in PrepTemplate(pt_id).get_filepaths():
                            prep_fp_ids.append(_id)
            filepath_ids.update(prep_fp_ids)

            if SampleTemplate.exists(study_id):
                sample_fp_ids = [_id for _id, _
                                 in SampleTemplate(study_id).get_filepaths()]
                filepath_ids.update(sample_fp_ids)

        # Next, the public processed data
        processed_data_ids = ProcessedData.get_by_status('public')
        for pd_id in processed_data_ids:
            processed_data = ProcessedData(pd_id)

            # Add the filepaths of the processed data
            pd_fps = (fpid for fpid, _, _ in processed_data.get_filepaths())
            filepath_ids.update(pd_fps)

            # Each processed data has a preprocessed data
            ppd = PreprocessedData(processed_data.preprocessed_data)
            ppd_fps = (fpid for fpid, _, _ in ppd.get_filepaths())
            filepath_ids.update(ppd_fps)

            # Each preprocessed data has a prep template
            pt_id = ppd.prep_template
            # related to https://github.com/biocore/qiita/issues/596
            if PrepTemplate.exists(pt_id):
                pt = PrepTemplate(pt_id)
                pt_fps = (fpid for fpid, _ in pt.get_filepaths())
                filepath_ids.update(pt_fps)

                # Each prep template has a raw data
                rd = RawData(pt.raw_data)
                rd_fps = (fpid for fpid, _, _ in rd.get_filepaths())
                filepath_ids.update(rd_fps)

            # And each processed data has a study, which has a sample template
            st_id = processed_data.study
            if SampleTemplate.exists(st_id):
                sample_fp_ids = (_id for _id, _
                                 in SampleTemplate(st_id).get_filepaths())
                filepath_ids.update(sample_fp_ids)

        # Next, analyses
        # Same as before, there are public, private, and shared
        analysis_ids = Analysis.get_by_status('public') | \
            user.private_analyses | user.shared_analyses

        for analysis_id in analysis_ids:
            analysis = Analysis(analysis_id)

            # For each analysis, there are mapping, biom, and job result
            # filepaths
            filepath_ids.update(analysis.all_associated_filepath_ids)

        return filepath_ids


def get_lat_longs():
    """Retrieve the latitude and longitude of all the samples in the DB

    Returns
    -------
    list of [float, float]
        The latitude and longitude for each sample in the database
    """
    portal_table_ids = Portal(qiita_config.portal).get_studies()

    with TRN:
        sql = """SELECT DISTINCT table_name
                 FROM information_schema.columns
                 WHERE table_name SIMILAR TO 'sample_[0-9]+'
                    AND table_schema = 'qiita'
                    AND column_name IN ('latitude', 'longitude')
                    AND SPLIT_PART(table_name, '_', 2)::int IN %s;"""
        TRN.add(sql, [tuple(portal_table_ids)])

        sql = """SELECT latitude, longitude
                 FROM qiita.{0}
                 WHERE latitude IS NOT NULL
                    AND longitude IS NOT NULL"""
        idx = TRN.index

        portal_tables = TRN.execute_fetchflatten()

        for table in portal_tables:
            TRN.add(sql.format(table))

        return list(chain.from_iterable(TRN.execute()[idx:]))
