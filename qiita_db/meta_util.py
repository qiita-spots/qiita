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
            # admins have access all files
            return True

        sql = """SELECT
            (SELECT array_agg(artifact_id)
             FROM qiita.artifact_filepath
             WHERE filepath_id = {0}) AS artifact,
            (SELECT array_agg(study_id)
             FROM qiita.sample_template_filepath
             WHERE filepath_id = {0}) AS sample_info,
            (SELECT array_agg(prep_template_id)
             FROM qiita.prep_template_filepath
             WHERE filepath_id = {0}) AS prep_info,
            (SELECT array_agg(job_id)
             FROM qiita.job_results_filepath
             WHERE filepath_id = {0}) AS job_results,
            (SELECT array_agg(analysis_id)
             FROM qiita.analysis_filepath
             WHERE filepath_id = {0}) AS analysis""".format(filepath_id)
        TRN.add(sql)

        arid, sid, pid, jid, anid = TRN.execute_fetchflatten()

        # artifacts
        if arid:
            # [0] cause we should only have 1
            artifact = qdb.artifact.Artifact(arid[0])
            if artifact.visibility == 'public':
                return True
            else:
                # let's take the visibility via the Study
                return artifact.study.has_access(user)
        # sample info files
        elif sid:
            # the visibility of the sample info file is given by the
            # study visibility
            # [0] cause we should only have 1
            return qdb.study.Study(sid[0]).has_access(user)
        # prep info files
        elif pid:
            # the prep access is given by it's artifacts, if the user has
            # access to any artifact, it should have access to the prep
            # [0] cause we should only have 1
            a = qdb.metadata_template.prep_template.PrepTemplate(
                pid[0]).artifact
            if (a.visibility == 'public' or a.study.has_access(user)):
                return True
            else:
                for c in a.children:
                    if (c.visibility == 'public' or c.study.has_access(user)):
                        return True
            return False
        # analyses
        elif anid or jid:
            if jid:
                # [0] cause we should only have 1
                sql = """SELECT analysis_id FROM qiita.analysis_job
                         WHERE job_id = {0}""".format(jid[0])
                TRN.add(sql)
                aid = TRN.execute_fetchlast()
            else:
                aid = anid[0]
            # [0] cause we should only have 1
            analysis = qdb.analysis.Analysis(aid)
            if analysis.status == 'public':
                return True
            else:
                return analysis in (
                    user.private_analyses | user.shared_analyses)


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
