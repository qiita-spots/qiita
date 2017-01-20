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
import qiita_db as qdb


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
    with qdb.sql_connection.TRN:
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
    with qdb.sql_connection.TRN:
        if user.level == "admin":
            # admins have access all files
            qdb.sql_connection.TRN.add(
                "SELECT filepath_id FROM qiita.filepath")
            return set(qdb.sql_connection.TRN.execute_fetchflatten())

        # First, the studies
        # There are private and shared studies
        studies = user.user_studies | user.shared_studies

        filepath_ids = set()
        for study in studies:
            # Add the sample template files
            if study.sample_template:
                filepath_ids.update(
                    {fid for fid, _ in study.sample_template.get_filepaths()})

            # Add the prep template filepaths
            for pt in study.prep_templates():
                filepath_ids.update({fid for fid, _ in pt.get_filepaths()})

            # Add the artifact filepaths
            for artifact in study.artifacts():
                filepath_ids.update({fid for fid, _, _ in artifact.filepaths})

        # Next, the public artifacts
        for artifact in qdb.artifact.Artifact.iter_public():
            # Add the filepaths of the artifact
            filepath_ids.update({fid for fid, _, _ in artifact.filepaths})

            # Then add the filepaths of the prep templates
            for pt in artifact.prep_templates:
                filepath_ids.update({fid for fid, _ in pt.get_filepaths()})

            # Then add the filepaths of the sample template
            filepath_ids.update(
                {fid
                 for fid, _ in artifact.study.sample_template.get_filepaths()})

        # Next, analyses
        # Same as before, there are public, private, and shared
        analyses = qdb.analysis.Analysis.get_by_status('public') | \
            user.private_analyses | user.shared_analyses

        for analysis in analyses:
            filepath_ids.update(analysis.all_associated_filepath_ids)

        return filepath_ids


def get_lat_longs():
    """Retrieve the latitude and longitude of all the samples in the DB

    Returns
    -------
    list of [float, float]
        The latitude and longitude for each sample in the database
    """
    portal_table_ids = [
        s.id for s in qdb.portal.Portal(qiita_config.portal).get_studies()]

    with qdb.sql_connection.TRN:
        # getting all tables in the portal
        sql = """SELECT DISTINCT table_name
                 FROM information_schema.columns
                 WHERE table_name SIMILAR TO 'sample_[0-9]+'
                    AND table_schema = 'qiita'
                    AND column_name IN ('latitude', 'longitude')
                    AND SPLIT_PART(table_name, '_', 2)::int IN %s;"""
        qdb.sql_connection.TRN.add(sql, [tuple(portal_table_ids)])

        sql = [('SELECT CAST(latitude AS FLOAT), '
                       'CAST(longitude AS FLOAT) '
                'FROM qiita.%s '
                'WHERE isnumeric(latitude) AND isnumeric(latitude)' % s)
                for s in qdb.sql_connection.TRN.execute_fetchflatten()]
        sql = ' UNION '.join(sql)
        qdb.sql_connection.TRN.add(sql)

        return qdb.sql_connection.TRN.execute_fetchindex()
