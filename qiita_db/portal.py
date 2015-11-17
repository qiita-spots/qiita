# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
import warnings

import qiita_db as qdb


class Portal(qdb.base.QiitaObject):
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
        with qdb.sql_connection.TRN:
            self.portal = portal
            portal_id = qdb.util.convert_to_id(portal, 'portal_type', 'portal')
            super(Portal, self).__init__(portal_id)

    @staticmethod
    def list_portals():
        """Returns list of non-default portals available in system

        Returns
        -------
        list of str
            List of portal names for the system

        Notes
        -----
        This does not return the QIITA portal in the list, as it is a required
        portal that can not be edited.
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT portal
                     FROM qiita.portal_type
                     WHERE portal != 'QIITA'
                     ORDER BY portal"""
            qdb.sql_connection.TRN.add(sql)
            return qdb.sql_connection.TRN.execute_fetchflatten()

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
        with qdb.sql_connection.TRN:
            if cls.exists(portal):
                raise qdb.exceptions.QiitaDBDuplicateError("Portal", portal)

            # Add portal and default analyses for all users
            sql = """DO $do$
                DECLARE
                    pid bigint;
                    eml varchar;
                    aid bigint;
                BEGIN
                    INSERT INTO qiita.portal_type (portal, portal_description)
                    VALUES (%s, %s)
                    RETURNING portal_type_id INTO pid;

                    FOR eml IN
                        SELECT email FROM qiita.qiita_user
                    LOOP
                        INSERT INTO qiita.analysis
                            (email, name, description, dflt,
                             analysis_status_id)
                        VALUES (eml, eml || '-dflt', 'dflt', true, 1)
                        RETURNING analysis_id INTO aid;

                        INSERT INTO qiita.analysis_workflow (analysis_id, step)
                        VALUES (aid, 2);

                        INSERT INTO qiita.analysis_portal
                            (analysis_id, portal_type_id)
                        VALUES (aid, pid);
                    END LOOP;
                END $do$;"""
            qdb.sql_connection.TRN.add(sql, [portal, desc])
            qdb.sql_connection.TRN.execute()

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
        with qdb.sql_connection.TRN:
            # Check if attached to any studies
            portal_id = qdb.util.convert_to_id(portal, 'portal_type', 'portal')
            sql = """SELECT study_id
                     FROM qiita.study_portal
                     WHERE portal_type_id = %s"""
            qdb.sql_connection.TRN.add(sql, [portal_id])
            studies = qdb.sql_connection.TRN.execute_fetchflatten()
            if studies:
                raise qdb.exceptions.QiitaDBError(
                    " Cannot delete portal '%s', studies still attached: %s" %
                    (portal, ', '.join(map(str, studies))))

            # Check if attached to any analyses
            sql = """SELECT analysis_id
                     FROM qiita.analysis_portal
                        JOIN qiita.analysis USING (analysis_id)
                     WHERE portal_type_id = %s AND dflt = FALSE"""
            qdb.sql_connection.TRN.add(sql, [portal_id])
            analyses = qdb.sql_connection.TRN.execute_fetchflatten()
            if analyses:
                raise qdb.exceptions.QiitaDBError(
                    " Cannot delete portal '%s', analyses still attached: %s" %
                    (portal, ', '.join(map(str, analyses))))

            # Remove portal and default analyses for all users
            sql = """DO $do$
                DECLARE
                    aid bigint;
                BEGIN
                    FOR aid IN
                        SELECT analysis_id
                        FROM qiita.analysis_portal
                            JOIN qiita.analysis USING (analysis_id)
                        WHERE portal_type_id = %s AND dflt = True
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
                    DELETE FROM qiita.portal_type WHERE portal_type_id = %s;
                END $do$;"""
            qdb.sql_connection.TRN.add(sql, [portal_id] * 2)
            qdb.sql_connection.TRN.execute()

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
            qdb.util.convert_to_id(portal, 'portal_type', 'portal')
        except qdb.exceptions.QiitaDBLookupError:
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
        with qdb.sql_connection.TRN:
            sql = """SELECT study_id FROM qiita.study_portal
                     WHERE portal_type_id = %s"""
            qdb.sql_connection.TRN.add(sql, [self._id])
            return set(qdb.sql_connection.TRN.execute_fetchflatten())

    def _check_studies(self, studies):
        with qdb.sql_connection.TRN:
            # Check if any study IDs given do not exist.
            sql = "SELECT study_id FROM qiita.study WHERE study_id IN %s"
            qdb.sql_connection.TRN.add(sql, [tuple(studies)])
            existing = qdb.sql_connection.TRN.execute_fetchflatten()
            if len(existing) != len(studies):
                bad = map(str, set(studies).difference(existing))
                raise qdb.exceptions.QiitaDBError(
                    "The following studies do not exist: %s" % ", ".join(bad))

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
        with qdb.sql_connection.TRN:
            self._check_studies(studies)

            # Clean list of studies down to ones not associated
            # with portal already
            sql = """SELECT study_id
                     FROM qiita.study_portal
                     WHERE portal_type_id = %s AND study_id IN %s"""
            qdb.sql_connection.TRN.add(sql, [self._id, tuple(studies)])
            duplicates = qdb.sql_connection.TRN.execute_fetchflatten()

            if len(duplicates) > 0:
                warnings.warn(
                    "The following studies are already part of %s: %s"
                    % (self.portal, ', '.join(map(str, duplicates))),
                    qdb.exceptions.QiitaDBWarning)

            # Add cleaned list to the portal
            clean_studies = set(studies).difference(duplicates)
            sql = """INSERT INTO qiita.study_portal (study_id, portal_type_id)
                     VALUES (%s, %s)"""
            if len(clean_studies) != 0:
                qdb.sql_connection.TRN.add(
                    sql, [[s, self._id] for s in clean_studies], many=True)
            qdb.sql_connection.TRN.execute()

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
            Some studies are already used in an analysis on the portal
        QiitaDBWarning
            Some studies already do not exist in the given portal
        """
        if self.portal == "QIITA":
            raise ValueError('Can not remove from main QIITA portal!')

        with qdb.sql_connection.TRN:
            self._check_studies(studies)

            # Make sure study not used in analysis in portal
            sql = """SELECT DISTINCT study_id
                     FROM qiita.study_processed_data
                        JOIN qiita.analysis_sample USING (processed_data_id)
                        JOIN qiita.analysis_portal USING (analysis_id)
                     WHERE portal_type_id = %s AND study_id IN %s"""
            qdb.sql_connection.TRN.add(sql, [self.id, tuple(studies)])
            analysed = qdb.sql_connection.TRN.execute_fetchflatten()
            if analysed:
                raise qdb.exceptions.QiitaDBError(
                    "The following studies are used in an analysis on portal "
                    "%s and can't be removed: %s"
                    % (self.portal, ", ".join(map(str, analysed))))

            # Clean list of studies down to ones associated with portal already
            sql = """SELECT study_id
                     FROM qiita.study_portal
                     WHERE portal_type_id = %s AND study_id IN %s"""
            qdb.sql_connection.TRN.add(sql, [self._id, tuple(studies)])
            clean_studies = qdb.sql_connection.TRN.execute_fetchflatten()

            if len(clean_studies) != len(studies):
                rem = map(str, set(studies).difference(clean_studies))
                warnings.warn(
                    "The following studies are not part of %s: %s"
                    % (self.portal, ', '.join(rem)),
                    qdb.exceptions.QiitaDBWarning)

            sql = """DELETE FROM qiita.study_portal
                     WHERE study_id IN %s AND portal_type_id = %s"""
            if len(clean_studies) != 0:
                qdb.sql_connection.TRN.add(sql, [tuple(studies), self._id])
            qdb.sql_connection.TRN.execute()

    def get_analyses(self):
        """Returns analysis id for all Analyses belonging to a portal

        Returns
        -------
        set of int
            All analysis ids in the database that match the given portal
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT analysis_id
                     FROM qiita.analysis_portal
                     WHERE portal_type_id = %s"""
            qdb.sql_connection.TRN.add(sql, [self._id])
            return set(qdb.sql_connection.TRN.execute_fetchflatten())

    def _check_analyses(self, analyses):
        with qdb.sql_connection.TRN:
            # Check if any analysis IDs given do not exist.
            sql = """SELECT analysis_id
                     FROM qiita.analysis
                     WHERE analysis_id IN %s"""
            qdb.sql_connection.TRN.add(sql, [tuple(analyses)])
            existing = qdb.sql_connection.TRN.execute_fetchflatten()
            if len(existing) != len(analyses):
                bad = map(str, set(analyses).difference(existing))
                raise qdb.exceptions.QiitaDBError(
                    "The following analyses do not exist: %s" % ", ".join(bad))

            # Check if any analyses given are default
            sql = """SELECT analysis_id
                     FROM qiita.analysis
                     WHERE analysis_id IN %s AND dflt = True"""
            qdb.sql_connection.TRN.add(sql, [tuple(analyses)])
            default = qdb.sql_connection.TRN.execute_fetchflatten()
            if len(default) > 0:
                bad = map(str, set(analyses).difference(default))
                raise qdb.exceptions.QiitaDBError(
                    "The following analyses are default and can't be deleted "
                    "or assigned to another portal: %s" % ", ".join(bad))

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
            Portal does not contain all studies used in analyses
        QiitaDBWarning
            Some analyses already exist in the given portal
        """
        with qdb.sql_connection.TRN:
            self._check_analyses(analyses)

            if self.portal != "QIITA":
                # Make sure new portal has access to all studies in analysis
                sql = """SELECT DISTINCT analysis_id
                         FROM qiita.analysis_sample
                            JOIN qiita.study_processed_data
                                USING (processed_data_id)
                         WHERE study_id NOT IN (
                            SELECT study_id
                            FROM qiita.study_portal
                            WHERE portal_type_id = %s)
                         AND analysis_id IN %s
                         ORDER BY analysis_id"""
                qdb.sql_connection.TRN.add(sql, [self._id, tuple(analyses)])
                missing_info = qdb.sql_connection.TRN.execute_fetchflatten()
                if missing_info:
                    raise qdb.exceptions.QiitaDBError(
                        "Portal %s is mising studies used in the following "
                        "analyses: %s"
                        % (self.portal, ", ".join(map(str, missing_info))))

            # Clean list of analyses to ones not already associated with portal
            sql = """SELECT analysis_id
                     FROM qiita.analysis_portal
                        JOIN qiita.analysis USING (analysis_id)
                     WHERE portal_type_id = %s AND analysis_id IN %s
                        AND dflt != TRUE"""
            qdb.sql_connection.TRN.add(sql, [self._id, tuple(analyses)])
            duplicates = qdb.sql_connection.TRN.execute_fetchflatten()

            if len(duplicates) > 0:
                warnings.warn(
                    "The following analyses are already part of %s: %s"
                    % (self.portal, ', '.join(map(str, duplicates))),
                    qdb.exceptions.QiitaDBWarning)

            sql = """INSERT INTO qiita.analysis_portal
                        (analysis_id, portal_type_id)
                     VALUES (%s, %s)"""
            clean_analyses = set(analyses).difference(duplicates)
            if len(clean_analyses) != 0:
                qdb.sql_connection.TRN.add(
                    sql, [[a, self._id] for a in clean_analyses], many=True)
            qdb.sql_connection.TRN.execute()

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
        with qdb.sql_connection.TRN:
            self._check_analyses(analyses)
            if self.portal == "QIITA":
                raise ValueError('Can not remove from main QIITA portal!')

            # Clean list of analyses to ones already associated with portal
            sql = """SELECT analysis_id
                     FROM qiita.analysis_portal
                        JOIN qiita.analysis USING (analysis_id)
                     WHERE portal_type_id = %s AND analysis_id IN %s
                        AND dflt != TRUE"""
            qdb.sql_connection.TRN.add(sql, [self._id, tuple(analyses)])
            clean_analyses = qdb.sql_connection.TRN.execute_fetchflatten()

            if len(clean_analyses) != len(analyses):
                rem = map(str, set(analyses).difference(clean_analyses))
                warnings.warn(
                    "The following analyses are not part of %s: %s"
                    % (self.portal, ', '.join(rem)),
                    qdb.exceptions.QiitaDBWarning)

            sql = """DELETE FROM qiita.analysis_portal
                     WHERE analysis_id IN %s AND portal_type_id = %s"""
            if len(clean_analyses) != 0:
                qdb.sql_connection.TRN.add(
                    sql, [tuple(clean_analyses), self._id])
            qdb.sql_connection.TRN.execute()
