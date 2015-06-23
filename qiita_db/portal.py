# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

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

    def add_study_to_portal(study, portal):
        """Adds study to given portal

        Parameters
        ----------
        portal : str
            Portal to associate with.
        """
        portal_id = convert_to_id(portal, 'portal_type', 'portal')
        sql = """INSERT INTO qiita.study_portal (study_id, portal_type_id)
                 VALUES (%s, %s)"""
        conn_handler = SQLConnectionHandler()
        conn_handler.execute(sql, [study.id, portal_id])

    def remove_study_from_portal(study, portal):
        """Adds study to given portal

        Parameters
        ----------
        portal : str
            Portal to associate with.
        """
        if portal == "QIITA":
            raise ValueError('Can not remove from main QIITA portal!')
        portal_id = convert_to_id(portal, 'portal_type', 'portal')
        sql = """DELETE FROM qiita.study_portal WHERE study_id = %s
                 AND portal_type_id = %s"""
        conn_handler = SQLConnectionHandler()
        conn_handler.execute(sql, [study.id, portal_id])
