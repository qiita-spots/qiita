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

    def add_studies_to_portal(portal, studies):
        """Adds studies to given portal

        Parameters
        ----------
        studies : list of int
            Study ids to attach to portal
        portal : str
            Portal to associate with.
        """
        portal_id = convert_to_id(portal, 'portal_type', 'portal')
        conn_handler = SQLConnectionHandler()
        sql = """SELECT study_id from qiita.study_portal
                 WHERE portal_type_id != %s AND study_id IN %s"""
        clean_studies = [x[0] for x in conn_handler.execute_fetchall(
                         sql, [portal_id, tuple(studies)])]

        if len(clean_studies) != len(studies):
            rem = map(str, set(studies).difference(clean_studies))
            warnings.warn("The following studies will not be added: %s" %
                          ', '.join(rem))

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

        portal_id = convert_to_id(portal, 'portal_type', 'portal')
        conn_handler = SQLConnectionHandler()
        sql = """SELECT study_id from qiita.study_portal
                 WHERE portal_type_id = %s AND study_id IN %s"""
        clean_studies = [x[0] for x in conn_handler.execute_fetchall(
                         sql, [portal_id, tuple(studies)])]

        if len(clean_studies) != len(studies):
            rem = map(str, set(studies).difference(clean_studies))
            warnings.warn("The following studies will not be removed: %s" %
                          ', '.join(rem))

        sql = """DELETE FROM qiita.study_portal
                 WHERE study_id IN %s AND portal_type_id = %s"""
        if len(clean_studies) != 0:
            conn_handler = SQLConnectionHandler()
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

    def add_analyses_to_portal(portal, analyses):
        """Adds analyses to given portal

        Parameters
        ----------
        analyses : list of int
            Analysis ids to attach to portal
        portal : str
            Portal to associate with.
        """
        portal_id = convert_to_id(portal, 'portal_type', 'portal')
        conn_handler = SQLConnectionHandler()
        sql = """SELECT analysis_id from qiita.analysis_portal
                 JOIN qiita.analysis USING (analysis_id)
                 WHERE portal_type_id != %s AND analysis_id IN %s
                 AND dflt != TRUE"""
        clean_analyses = [x[0] for x in conn_handler.execute_fetchall(
            sql, [portal_id, tuple(analyses)])]

        if len(clean_analyses) != len(analyses):
            rem = map(str, set(analyses).difference(clean_analyses))
            warnings.warn("The following analyses will not be added: %s" %
                          ', '.join(rem))

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

        portal_id = convert_to_id(portal, 'portal_type', 'portal')
        conn_handler = SQLConnectionHandler()
        sql = """SELECT analysis_id from qiita.analysis_portal
                 JOIN qiita.analysis USING (analysis_id)
                 WHERE portal_type_id = %s AND analysis_id IN %s
                 AND dflt != TRUE"""
        clean_analyses = [x[0] for x in conn_handler.execute_fetchall(
            sql, [portal_id, tuple(analyses)])]

        if len(clean_analyses) != len(analyses):
            rem = map(str, set(analyses).difference(clean_analyses))
            warnings.warn("The following analyses will not be removed: %s" %
                          ', '.join(rem))

        sql = """DELETE FROM qiita.analysis_portal
                 WHERE analysis_id IN %s AND portal_type_id = %s"""
        if len(clean_analyses) != 0:
            conn_handler = SQLConnectionHandler()
            conn_handler.execute(sql, [tuple(clean_analyses), portal_id])
