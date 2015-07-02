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
from .base import QiitaObject
from .exceptions import QiitaDBError, QiitaDBDuplicateError, QiitaDBWarning
from qiita_core.exceptions import IncompetentQiitaDeveloperError


class Portal(QiitaObject):
    r"""Portal object to create and maintain portals in the system

    Attributes
    ----------
    portal

    Methods
    -------
    get_studies
    add_studies
    remove_studies
    get_analyses
    add_analyses
    remove_analyses
    """
    _table = 'portal_type'

    def __init__(self, portal):
        self.portal = portal
        portal_id = convert_to_id(portal, 'portal_type', 'portal')
        super(Portal, self).__init__(portal_id)

    @staticmethod
    def list_portals():
        """Returns list of portals available in system
        Returns
        -------
        list of str
            List of portal names for the system
        Notes
        -----
        This does not return the QIITA portal in the list, as it is a required
        portal that can not be edited.
        """
        sql = """SELECT portal FROM qiita.portal_type WHERE portal != 'QIITA'
              ORDER BY portal"""
        conn_handler = SQLConnectionHandler()
        return [x[0] for x in conn_handler.execute_fetchall(sql)]

    @classmethod
    def create(cls, portal, desc):
        """Creates a new portal and its default analyses on the system

        Parameters
        ----------
        portal : str
            The name of the portal to add
        desc : str
            Description of the portal

        Raises
        ------
        QiitaDBDuplicateError
            Portal name already exists
        """
        if cls.exists(portal):
            raise QiitaDBDuplicateError("Portal", portal)

        # Add portal and default analyses for all users
        sql = """DO $do$
            DECLARE
                pid bigint;
                eml varchar;
                aid bigint;
            BEGIN
                INSERT INTO qiita.portal_type (portal, portal_description)
                VALUES (%s, %s) RETURNING portal_type_id INTO pid;

                FOR eml IN
                    SELECT email FROM qiita.qiita_user
                LOOP
                    INSERT INTO qiita.analysis
                    (email, name, description, dflt, analysis_status_id)
                    VALUES (eml, eml || '-dflt', 'dflt', true, 1) RETURNING
                    analysis_id INTO aid;

                    INSERT INTO qiita.analysis_workflow (analysis_id, step)
                    VALUES (aid, 2);

                    INSERT INTO qiita.analysis_portal
                    (analysis_id, portal_type_id)
                    VALUES (aid, pid);
                END LOOP;
            END $do$;"""
        conn_handler = SQLConnectionHandler()
        conn_handler.execute(sql, [portal, desc])

        return cls(portal)

    @staticmethod
    def delete(portal):
        """Removes a portal and its default analyses from the system

        Parameters
        ----------
        portal : str
            The name of the portal to add

        Raises
        ------
        QiitaDBError
            Portal has analyses or studies attached to it
        """
        conn_handler = SQLConnectionHandler()
        # Check if attached to any studies
        portal_id = convert_to_id(portal, 'portal_type', 'portal')
        sql = """SELECT study_id from qiita.study_portal
                 WHERE portal_type_id = %s"""
        studies = conn_handler.execute_fetchall(sql, [portal_id])
        if studies:
            raise QiitaDBError(
                " Cannot delete portal '%s', studies still attached: %s" %
                (portal, ', '.join([str(s[0]) for s in studies])))

        # Check if attached to any analyses
        sql = """SELECT analysis_id from qiita.analysis_portal
                 JOIN qiita.analysis USING (analysis_id)
                 WHERE portal_type_id = %s and dflt = FALSE"""
        analyses = conn_handler.execute_fetchall(sql, [portal_id])
        if studies:
            raise QiitaDBError(
                " Cannot delete portal '%s', analyses still attached: %s" %
                (portal, ', '.join([str(a[0]) for a in analyses])))

        # Remove portal and default analyses for all users, unlink others
        sql = """DO $do$
            DECLARE
                pid bigint;
                aid bigint;
            BEGIN
                FOR aid IN
                    SELECT analysis_id FROM qiita.analysis_portal
                    JOIN qiita.analysis USING (analysis_id)
                    WHERE portal_type_id = %s and dflt = True
                LOOP
                    DELETE FROM qiita.analysis_portal
                    WHERE analysis_id = aid;

                    DELETE FROM qiita.analysis_workflow
                    WHERE analysis_id = aid;

                    DELETE FROM qiita.analysis_sample
                    WHERE analysis_id = aid;

                    DELETE FROM qiita.analysis
                    WHERE analysis_id = aid;
                END LOOP;

                DELETE FROM qiita.analysis_portal
                WHERE portal_type_id = %s;

                DELETE FROM qiita.portal_type WHERE portal_type_id = %s;
            END $do$;"""
        conn_handler = SQLConnectionHandler()
        conn_handler.execute(sql, [portal_id] * 3)

    @staticmethod
    def exists(portal):
        """Returns whether the portal name already exists on the system

        Parameters
        ----------
        portal : str
            Name of portal to check

        Returns
        -------
        bool
            Whether the portal exists or not
        """
        try:
            convert_to_id(portal, 'portal_type', 'portal')
        except IncompetentQiitaDeveloperError:
            return False
        else:
            return True

    def get_studies(self):
        """Returns study id for all Studies belonging to the portal

        Returns
        -------
        set of int
            All study ids in the database that match the given portal
        """
        conn_handler = SQLConnectionHandler()
        sql = """SELECT study_id FROM qiita.study_portal
                 WHERE portal_type_id = %s"""
        return {x[0] for x in
                conn_handler.execute_fetchall(sql, [self._id])}

    def _check_studies(self, studies):
        conn_handler = SQLConnectionHandler()
        # Check if any study IDs given do not exist.
        sql = "SELECT study_id from qiita.study WHERE study_id IN %s"
        existing = [x[0] for x in conn_handler.execute_fetchall(
            sql, [tuple(studies)])]
        if len(existing) != len(studies):
            bad = map(str, set(studies).difference(existing))
            raise QiitaDBError("The following studies do not exist: %s" %
                               ", ".join(bad))

    def add_studies(self, studies):
        """Adds studies to given portal

        Parameters
        ----------
        studies : iterable of int
            Study ids to attach to portal

        Raises
        ------
        QiitaDBError
            Some studies given do not exist in the system
        QiitaDBWarning
            Some studies already exist in the given portal
        """
        self._check_studies(studies)

        conn_handler = SQLConnectionHandler()
        # Clean list of studies down to ones not associated with portal already
        sql = """SELECT study_id from qiita.study_portal
                 WHERE portal_type_id = %s AND study_id IN %s"""
        duplicates = [x[0] for x in conn_handler.execute_fetchall(
                      sql, [self._id, tuple(studies)])]

        if len(duplicates) > 0:
            warnings.warn("The following studies area already part of %s: %s" %
                          (self.portal, ', '.join(map(str, duplicates))),
                          QiitaDBWarning)

        # Add cleaned list to the portal
        clean_studies = set(studies).difference(duplicates)
        sql = """INSERT INTO qiita.study_portal (study_id, portal_type_id)
                 VALUES (%s, %s)"""
        conn_handler.executemany(sql, [(s, self._id) for s in clean_studies])

    def remove_studies(self, studies):
        """Removes studies from given portal

        Parameters
        ----------
        studies : iterable of int
            Study ids to remove from portal

        Raises
        ------
        ValueError
            Trying to delete from QIITA portal
        QiitaDBError
            Some studies given do not exist in the system
        QiitaDBWarning
            Some studies already do not exist in the given portal
        """
        if self.portal == "QIITA":
            raise ValueError('Can not remove from main QIITA portal!')
        self._check_studies(studies)

        # Clean list of studies down to ones associated with portal already
        conn_handler = SQLConnectionHandler()
        sql = """SELECT study_id from qiita.study_portal
                 WHERE portal_type_id = %s AND study_id IN %s"""
        clean_studies = [x[0] for x in conn_handler.execute_fetchall(
                         sql, [self._id, tuple(studies)])]

        if len(clean_studies) != len(studies):
            rem = map(str, set(studies).difference(clean_studies))
            warnings.warn("The following studies are not part of %s: %s" %
                          (self.portal, ', '.join(rem)), QiitaDBWarning)

        sql = """DELETE FROM qiita.study_portal
                 WHERE study_id IN %s AND portal_type_id = %s"""
        if len(clean_studies) != 0:
            conn_handler.execute(sql, [tuple(studies), self._id])

    def get_analyses(self):
        """Returns analysis id for all Analyses belonging to a portal

        Returns
        -------
        set of int
            All analysis ids in the database that match the given portal
        """
        conn_handler = SQLConnectionHandler()
        sql = """SELECT analysis_id FROM qiita.analysis_portal
                 WHERE portal_type_id = %s"""
        return {x[0] for x in
                conn_handler.execute_fetchall(sql, [self._id])}

    def _check_analyses(self, analyses):
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
            raise QiitaDBError(
                "The following analyses are default and can't be deleted or "
                "assigned to another portal: %s" % ", ".join(bad))

    def add_analyses(self, analyses):
        """Adds analyses to given portal

        Parameters
        ----------
        analyses : iterable of int
            Analysis ids to attach to portal

        Raises
        ------
        QiitaDBError
            Some given analyses do not exist in the system,
            or are default analyses
        QiitaDBWarning
            Some analyses already exist in the given portal
        """
        self._check_analyses(analyses)

        conn_handler = SQLConnectionHandler()
        # Clean list of analyses to ones not already associated with portal
        sql = """SELECT analysis_id from qiita.analysis_portal
                 JOIN qiita.analysis USING (analysis_id)
                 WHERE portal_type_id = %s AND analysis_id IN %s
                 AND dflt != TRUE"""
        duplicates = [x[0] for x in conn_handler.execute_fetchall(
            sql, [self._id, tuple(analyses)])]

        if len(duplicates) > 0:
            warnings.warn("The following analyses are already part of %s: %s" %
                          (self.portal, ', '.join(map(str, duplicates))),
                          QiitaDBWarning)

        sql = """INSERT INTO qiita.analysis_portal
                 (analysis_id, portal_type_id)
                 VALUES (%s, %s)"""
        clean_analyses = set(analyses).difference(duplicates)
        conn_handler.executemany(sql, [(a, self._id) for a in clean_analyses])

    def remove_analyses(self, analyses):
        """Removes analyses from given portal

        Parameters
        ----------
        analyses : iterable of int
            Analysis ids to remove from portal

        Raises
        ------
        ValueError
            Trying to delete from QIITA portal
        QiitaDBWarning
            Some analyses already do not exist in the given portal
        """
        self._check_analyses(analyses)
        if self.portal == "QIITA":
            raise ValueError('Can not remove from main QIITA portal!')
        conn_handler = SQLConnectionHandler()
        # Clean list of analyses to ones already associated with portal
        sql = """SELECT analysis_id from qiita.analysis_portal
                 JOIN qiita.analysis USING (analysis_id)
                 WHERE portal_type_id = %s AND analysis_id IN %s
                 AND dflt != TRUE"""
        clean_analyses = [x[0] for x in conn_handler.execute_fetchall(
            sql, [self._id, tuple(analyses)])]

        if len(clean_analyses) != len(analyses):
            rem = map(str, set(analyses).difference(clean_analyses))
            warnings.warn("The following analyses are not part of %s: %s" %
                          (self.portal, ', '.join(rem)), QiitaDBWarning)

        sql = """DELETE FROM qiita.analysis_portal
                 WHERE analysis_id IN %s AND portal_type_id = %s"""
        if len(clean_analyses) != 0:
            conn_handler.execute(sql, [tuple(clean_analyses), self._id])
