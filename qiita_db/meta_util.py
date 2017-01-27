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


def validate_filepath_access_by_user(user, filepath_id):
    """Validates if the user has access to the filepath_id

    Parameters
    ----------
    user : User object
        The user we are interested in
    filepath_id : int
        The filepath id

    Returns
    -------
    bool
        If the user has access or not to the filepath_id

    Notes
    -----
    Admins have access to all files so True is always returned
    """
    TRN = qdb.sql_connection.TRN
    with TRN:
        if user.level == "admin":
            return True
            # admins have access all files

        access = False
        sql = """SELECT
            (SELECT count(*) FROM qiita.artifact_filepath
             WHERE filepath_id = {0}) AS artifact,
            (SELECT count(*) FROM qiita.sample_template_filepath
             WHERE filepath_id = {0}) AS sample_info,
            (SELECT count(*) FROM qiita.prep_template_filepath
             WHERE filepath_id = {0}) AS prep_info,
            (SELECT count(*) FROM qiita.job_results_filepath
             WHERE filepath_id = {0}) AS job_results,
            (SELECT count(*) FROM qiita.analysis_filepath
             WHERE filepath_id = {0}) AS analysis""".format(filepath_id)
        TRN.add(sql)

        arid, sid, pid, jid, anid = TRN.execute_fetchflatten()

        # artifacts
        if arid:
            # check the public artifacts
            public_artifacts = qdb.artifact.Artifact.iter_public()
            for artifact in public_artifacts:
                if filepath_id in [fid for fid, _, _ in artifact.filepaths]:
                    access = True
                    break
            # if not found check the user artifacts from their studies
            if not access:
                user_studies = user.user_studies | user.shared_studies
                for s in user_studies:
                    if s.sample_template:
                        for a in s.artifacts():
                            if filepath_id in [fid[0] for fid in a.filepaths]:
                                access = True
                                break
                        # just avoiding extra loops if found
                        if access:
                            break
        # sample info files
        elif sid:
            # check private and shared studies with the user
            user_studies = user.user_studies | user.shared_studies
            for s in user_studies:
                st = s.sample_template
                if st is not None:
                    # sample info files
                    if filepath_id in [fid for fid, _ in st.get_filepaths()]:
                        access = True
                        break
            # if that didn't work let's check the public sample info files
            if not access:
                public_studies = qdb.study.Study.get_by_status('public')
                for s in public_studies:
                    st = s.sample_template
                    if st is not None:
                        if filepath_id in [fid[0] for fid in
                                           st.get_filepaths()]:
                            access = True
                            break
        # prep info files
        elif pid:
            # check private and shared studies with the user
            user_studies = user.user_studies | user.shared_studies
            for s in user_studies:
                for pt in s.prep_templates():
                    # sample info files
                    if filepath_id in [fid for fid, _ in pt.get_filepaths()]:
                        access = True
                        break
            # if that didn't work let's check the public prep info files
            if not access:
                public_studies = qdb.study.Study.get_by_status('public')
                for s in public_studies:
                    for pt in s.prep_templates():
                        if filepath_id in [fid[0]
                                           for fid in pt.get_filepaths()]:
                            access = True
                            break
        # next analyses
        elif anid or jid:
            analyses = qdb.analysis.Analysis.get_by_status('public') | \
                user.private_analyses | user.shared_analyses
            for analysis in analyses:
                if filepath_id in analysis.all_associated_filepath_ids:
                    access = True
                    break

        return access


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
                '       CAST(longitude AS FLOAT) '
                'FROM qiita.%s '
                'WHERE isnumeric(latitude) AND isnumeric(latitude)' % s)
               for s in qdb.sql_connection.TRN.execute_fetchflatten()]
        sql = ' UNION '.join(sql)
        qdb.sql_connection.TRN.add(sql)

        return qdb.sql_connection.TRN.execute_fetchindex()
