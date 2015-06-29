# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
import warnings

from .sql_connection import SQLConnectionHandler
from .util import convert_to_id
from .exceptions import QiitaDBError
from qiita_core.qiita_settings import qiita_config

# Only make functions available for main portal
if qiita_config.portal == "QIITA":
    def get_studies_by_portal(portal):
        """Returns study id for all Studies belonging to a portal

        Parameters
        ----------
        portal : str
           Portal to check studies belong to

        Returns
        -------
        set of int
            All study ids in the database that match the given portal
        """
        conn_handler = SQLConnectionHandler()
        portal_id = convert_to_id(portal, 'portal_type', 'portal')
        sql = """SELECT study_id FROM qiita.study_portal
                 WHERE portal_type_id = %s"""
        return {x[0] for x in
                conn_handler.execute_fetchall(sql, [portal_id])}

    def _check_studies(studies):
        conn_handler = SQLConnectionHandler()
        # Check if any study IDs given do not exist.
        sql = "SELECT study_id from qiita.study WHERE study_id IN %s"
        existing = [x[0] for x in conn_handler.execute_fetchall(
            sql, [tuple(studies)])]
        if len(existing) != len(studies):
            bad = map(str, (set(studies).difference(existing)))
            raise QiitaDBError("The following studies do not exist: %s" %
                               ", ".join(bad))

    def add_studies_to_portal(portal, studies):
        """Adds studies to given portal

        Parameters
        ----------
        studies : list of int
            Study ids to attach to portal
        portal : str
            Portal to associate with.
        """
        _check_studies(studies)

        portal_id = convert_to_id(portal, 'portal_type', 'portal')
        conn_handler = SQLConnectionHandler()
        # Clean list of studies down to ones not associated with portal already
        sql = """SELECT study_id from qiita.study_portal
                 WHERE portal_type_id != %s AND study_id IN %s"""
        clean_studies = [x[0] for x in conn_handler.execute_fetchall(
                         sql, [portal_id, tuple(studies)])]

        if len(clean_studies) != len(studies):
            rem = map(str, set(studies).difference(clean_studies))
            warnings.warn("The following studies area already part of %s: %s" %
                          (portal, ', '.join(rem)))

        # Add cleaned list to the portal
        portal_id = convert_to_id(portal, 'portal_type', 'portal')
        conn_handler = SQLConnectionHandler()
        sql = """INSERT INTO qiita.study_portal (study_id, portal_type_id)
                 VALUES (%s, %s)"""
        conn_handler.executemany(sql, [(s, portal_id) for s in clean_studies])

    def remove_studies_from_portal(portal, studies):
        """Removes studies to given portal

        Parameters
        ----------
        studies : list of int
            Study ids to remove from portal
        portal : str
            Portal to associate with.

        Raises
        ------
        ValueError
            Try and delete from QIITA portal
        """
        if portal == "QIITA":
            raise ValueError('Can not remove from main QIITA portal!')
        _check_studies(studies)

        conn_handler = SQLConnectionHandler()
        # Clean list of studies down to ones associated with portal already
        portal_id = convert_to_id(portal, 'portal_type', 'portal')
        conn_handler = SQLConnectionHandler()
        sql = """SELECT study_id from qiita.study_portal
                 WHERE portal_type_id = %s AND study_id IN %s"""
        clean_studies = [x[0] for x in conn_handler.execute_fetchall(
                         sql, [portal_id, tuple(studies)])]

        if len(clean_studies) != len(studies):
            rem = map(str, set(studies).difference(clean_studies))
            warnings.warn("The following studies are not part of %s: %s" %
                          (portal, ', '.join(rem)))

        sql = """DELETE FROM qiita.study_portal
                 WHERE study_id IN %s AND portal_type_id = %s"""
        if len(clean_studies) != 0:
            conn_handler.execute(sql, [tuple(studies), portal_id])

    def get_analyses_by_portal(portal):
        """Returns analysis id for all Analyses belonging to a portal

        Parameters
        ----------
        portal : str
           Portal to check analyses belong to

        Returns
        -------
        set of int
            All analysis ids in the database that match the given portal
        """
        conn_handler = SQLConnectionHandler()
        portal_id = convert_to_id(portal, 'portal_type', 'portal')
        sql = """SELECT analysis_id FROM qiita.analysis_portal
                 WHERE portal_type_id = %s"""
        return {x[0] for x in
                conn_handler.execute_fetchall(sql, [portal_id])}

    def _check_analyses(analyses):
        conn_handler = SQLConnectionHandler()
        # Check if any analysis IDs given do not exist.
        sql = "SELECT analysis_id from qiita.analysis WHERE analysis_id IN %s"
        existing = [x[0] for x in conn_handler.execute_fetchall(
            sql, [tuple(analyses)])]
        if len(existing) != len(analyses):
            bad = map(str, set(analyses).difference(existing))
            raise QiitaDBError("The following analyses do not exist: %s" %
                               ", ".join(bad))

        # Check if any analyses given are default
        sql = ("SELECT analysis_id from qiita.analysis WHERE analysis_id IN %s"
               " AND dflt = True")
        default = [x[0] for x in conn_handler.execute_fetchall(
            sql, [tuple(analyses)])]
        if len(default) > 0:
            bad = map(str, set(analyses).difference(default))
            raise QiitaDBError("The following analyses are default: %s" %
                               ", ".join(bad))

    def add_analyses_to_portal(portal, analyses):
        """Adds analyses to given portal

        Parameters
        ----------
        analyses : list of int
            Analysis ids to attach to portal
        portal : str
            Portal to associate with.
        """
        _check_analyses(analyses)

        portal_id = convert_to_id(portal, 'portal_type', 'portal')
        conn_handler = SQLConnectionHandler()
        # Clean list of analyses to ones not already associated with portal
        sql = """SELECT analysis_id from qiita.analysis_portal
                 JOIN qiita.analysis USING (analysis_id)
                 WHERE portal_type_id != %s AND analysis_id IN %s
                 AND dflt != TRUE"""
        clean_analyses = [x[0] for x in conn_handler.execute_fetchall(
            sql, [portal_id, tuple(analyses)])]

        if len(clean_analyses) != len(analyses):
            rem = map(str, set(analyses).difference(clean_analyses))
            warnings.warn("The following analyses are already part of %s: %s" %
                          (portal, ', '.join(rem)))

        sql = """INSERT INTO qiita.analysis_portal
                 (analysis_id, portal_type_id)
                 VALUES (%s, %s)"""
        portal_id = convert_to_id(portal, 'portal_type', 'portal')
        conn_handler = SQLConnectionHandler()
        conn_handler.executemany(sql, [(a, portal_id) for a in clean_analyses])

    def remove_analyses_from_portal(portal, analyses):
        """Removes  analyses from given portal

        Parameters
        ----------
        analyses : list of int
            Analysis ids to remove from portal
        portal : str
            Portal to associate with.

        Raises
        ------
        ValueError
            Try and delete from QIITA portal
        """
        if portal == "QIITA":
            raise ValueError('Can not remove from main QIITA portal!')
        _check_analyses(analyses)

        conn_handler = SQLConnectionHandler()
        # Clean list of analyses to ones already associated with portal
        sql = """SELECT analysis_id from qiita.analysis_portal
                 JOIN qiita.analysis USING (analysis_id)
                 WHERE portal_type_id = %s AND analysis_id IN %s
                 AND dflt != TRUE"""
        portal_id = convert_to_id(portal, 'portal_type', 'portal')
        clean_analyses = [x[0] for x in conn_handler.execute_fetchall(
            sql, [portal_id, tuple(analyses)])]

        if len(clean_analyses) != len(analyses):
            rem = map(str, set(analyses).difference(clean_analyses))
            warnings.warn("The following analyses are not part of %s: %s" %
                          (portal, ', '.join(rem)))

        sql = """DELETE FROM qiita.analysis_portal
                 WHERE analysis_id IN %s AND portal_type_id = %s"""
        if len(clean_analyses) != 0:
            conn_handler = SQLConnectionHandler()
            conn_handler.execute(sql, [tuple(clean_analyses), portal_id])
