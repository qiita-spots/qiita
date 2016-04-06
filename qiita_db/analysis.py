"""
Objects for dealing with Qiita analyses

This module provides the implementation of the Analysis and Collection classes.

Classes
-------
- `Analysis` -- A Qiita Analysis class
- `Collection` -- A Qiita Collection class for grouping multiple analyses
"""

# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from __future__ import division
from itertools import product
from os.path import join, basename
from tarfile import open as taropen

from future.utils import viewitems
from biom import load_table
from biom.util import biom_open
import pandas as pd

from qiita_core.exceptions import IncompetentQiitaDeveloperError
from qiita_core.qiita_settings import qiita_config
import qiita_db as qdb


class Analysis(qdb.base.QiitaStatusObject):
    """
    Analysis object to access to the Qiita Analysis information

    Attributes
    ----------
    owner
    name
    description
    samples
    dropped_samples
    data_types
    biom_tables
    step
    shared_with
    jobs
    pmid
    parent
    children

    Methods
    -------
    has_access
    add_samples
    remove_samples
    share
    unshare
    build_files
    summary_data
    exists
    create
    delete
    """

    _table = "analysis"
    _portal_table = "analysis_portal"
    _analysis_id_column = 'analysis_id'

    def _lock_check(self):
        """Raises QiitaDBStatusError if analysis is not in_progress"""
        if self.check_status({"queued", "running", "public", "completed",
                              "error"}):
            raise qdb.exceptions.QiitaDBStatusError("Analysis is locked!")

    def _status_setter_checks(self):
        r"""Perform a check to make sure not setting status away from public
        """
        if self.check_status({"public"}):
            raise qdb.exceptions.QiitaDBStatusError(
                "Can't set status away from public!")

    @classmethod
    def get_by_status(cls, status):
        """Returns all Analyses with given status

        Parameters
        ----------
        status : str
            Status to search analyses for

        Returns
        -------
        set of Analysis
            All analyses in the database with the given status
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT analysis_id
                     FROM qiita.{0}
                        JOIN qiita.{0}_status USING (analysis_status_id)
                        JOIN qiita.analysis_portal USING (analysis_id)
                        JOIN qiita.portal_type USING (portal_type_id)
                     WHERE status = %s AND portal = %s""".format(cls._table)
            qdb.sql_connection.TRN.add(sql, [status, qiita_config.portal])
            return set(
                cls(aid)
                for aid in qdb.sql_connection.TRN.execute_fetchflatten())

    @classmethod
    def create(cls, owner, name, description, parent=None, from_default=False):
        """Creates a new analysis on the database

        Parameters
        ----------
        owner : User object
            The analysis' owner
        name : str
            Name of the analysis
        description : str
            Description of the analysis
        parent : Analysis object, optional
            The analysis this one was forked from
        from_default : bool, optional
            If True, use the default analysis to populate selected samples.
            Default False.
        """
        with qdb.sql_connection.TRN:
            status_id = qdb.util.convert_to_id(
                'in_construction', 'analysis_status', 'status')
            portal_id = qdb.util.convert_to_id(
                qiita_config.portal, 'portal_type', 'portal')

            if from_default:
                # insert analysis and move samples into that new analysis
                dflt_id = owner.default_analysis.id

                sql = """INSERT INTO qiita.{0}
                            (email, name, description, analysis_status_id)
                        VALUES (%s, %s, %s, %s)
                        RETURNING analysis_id""".format(cls._table)
                qdb.sql_connection.TRN.add(
                    sql, [owner.id, name, description, status_id])
                a_id = qdb.sql_connection.TRN.execute_fetchlast()
                # MAGIC NUMBER 3: command selection step
                # needed so we skip the sample selection step
                sql = """INSERT INTO qiita.analysis_workflow
                            (analysis_id, step)
                        VALUES (%s, %s)"""
                qdb.sql_connection.TRN.add(sql, [a_id, 3])

                sql = """UPDATE qiita.analysis_sample
                         SET analysis_id = %s
                         WHERE analysis_id = %s"""
                qdb.sql_connection.TRN.add(sql, [a_id, dflt_id])
            else:
                # insert analysis information into table as "in construction"
                sql = """INSERT INTO qiita.{0}
                            (email, name, description, analysis_status_id)
                         VALUES (%s, %s, %s, %s)
                         RETURNING analysis_id""".format(cls._table)
                qdb.sql_connection.TRN.add(
                    sql, [owner.id, name, description, status_id])
                a_id = qdb.sql_connection.TRN.execute_fetchlast()

            # Add to both QIITA and given portal (if not QIITA)
            sql = """INSERT INTO qiita.analysis_portal
                        (analysis_id, portal_type_id)
                     VALUES (%s, %s)"""
            args = [[a_id, portal_id]]

            if qiita_config.portal != 'QIITA':
                qp_id = qdb.util.convert_to_id(
                    'QIITA', 'portal_type', 'portal')
                args.append([a_id, qp_id])
            qdb.sql_connection.TRN.add(sql, args, many=True)

            # add parent if necessary
            if parent:
                sql = """INSERT INTO qiita.analysis_chain
                            (parent_id, child_id)
                         VALUES (%s, %s)"""
                qdb.sql_connection.TRN.add(sql, [parent.id, a_id])

            return cls(a_id)

    @classmethod
    def delete(cls, _id):
        """Deletes an analysis

        Parameters
        ----------
        _id : int
            The analysis id

        Raises
        ------
        QiitaDBUnknownIDError
            If the analysis id doesn't exist
        """
        with qdb.sql_connection.TRN:
            # check if the analysis exist
            if not cls.exists(_id):
                raise qdb.exceptions.QiitaDBUnknownIDError(_id, "analysis")

            sql = "DELETE FROM qiita.analysis_filepath WHERE {0} = %s".format(
                cls._analysis_id_column)
            args = [_id]
            qdb.sql_connection.TRN.add(sql, args)

            sql = "DELETE FROM qiita.analysis_workflow WHERE {0} = %s".format(
                cls._analysis_id_column)
            qdb.sql_connection.TRN.add(sql, args)

            sql = "DELETE FROM qiita.analysis_portal WHERE {0} = %s".format(
                cls._analysis_id_column)
            qdb.sql_connection.TRN.add(sql, args)

            sql = "DELETE FROM qiita.analysis_sample WHERE {0} = %s".format(
                cls._analysis_id_column)
            qdb.sql_connection.TRN.add(sql, args)

            sql = """DELETE FROM qiita.collection_analysis
                     WHERE {0} = %s""".format(cls._analysis_id_column)
            qdb.sql_connection.TRN.add(sql, args)

            # TODO: issue #1176

            sql = """DELETE FROM qiita.{0} WHERE {1} = %s""".format(
                cls._table, cls._analysis_id_column)
            qdb.sql_connection.TRN.add(sql, args)

            qdb.sql_connection.TRN.execute()

    @classmethod
    def exists(cls, analysis_id):
        r"""Checks if the given analysis _id exists

        Parameters
        ----------
        analysis_id : int
            The id of the analysis we are searching for

        Returns
        -------
        bool
            True if exists, false otherwise.
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT EXISTS(
                        SELECT *
                        FROM qiita.{0}
                            JOIN qiita.analysis_portal USING (analysis_id)
                            JOIN qiita.portal_type USING (portal_type_id)
                        WHERE {1}=%s
                            AND portal=%s)""".format(cls._table,
                                                     cls._analysis_id_column)
            qdb.sql_connection.TRN.add(sql, [analysis_id, qiita_config.portal])
            return qdb.sql_connection.TRN.execute_fetchlast()

    # ---- Properties ----
    @property
    def owner(self):
        """The owner of the analysis

        Returns
        -------
        qiita_db.user.User
            The owner of the Analysis
        """
        with qdb.sql_connection.TRN:
            sql = "SELECT email FROM qiita.{0} WHERE analysis_id = %s".format(
                self._table)
            qdb.sql_connection.TRN.add(sql, [self._id])
            return qdb.user.User(qdb.sql_connection.TRN.execute_fetchlast())

    @property
    def name(self):
        """The name of the analysis

        Returns
        -------
        str
            Name of the Analysis
        """
        with qdb.sql_connection.TRN:
            sql = "SELECT name FROM qiita.{0} WHERE analysis_id = %s".format(
                self._table)
            qdb.sql_connection.TRN.add(sql, [self._id])
            return qdb.sql_connection.TRN.execute_fetchlast()

    @property
    def _portals(self):
        """The portals used to create the analysis

        Returns
        -------
        str
            Name of the portal
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT portal
                     FROM qiita.analysis_portal
                        JOIN qiita.portal_type USING (portal_type_id)
                     WHERE analysis_id = %s""".format(self._table)
            qdb.sql_connection.TRN.add(sql, [self._id])
            return qdb.sql_connection.TRN.execute_fetchflatten()

    @property
    def timestamp(self):
        """The timestamp of the analysis

        Returns
        -------
        datetime
            Timestamp of the Analysis
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT timestamp FROM qiita.{0}
                     WHERE analysis_id = %s""".format(self._table)
            qdb.sql_connection.TRN.add(sql, [self._id])
            return qdb.sql_connection.TRN.execute_fetchlast()

    @property
    def description(self):
        """Returns the description of the analysis"""
        with qdb.sql_connection.TRN:
            sql = """SELECT description FROM qiita.{0}
                     WHERE analysis_id = %s""".format(self._table)
            qdb.sql_connection.TRN.add(sql, [self._id])
            return qdb.sql_connection.TRN.execute_fetchlast()

    @description.setter
    def description(self, description):
        """Changes the description of the analysis

        Parameters
        ----------
        description : str
            New description for the analysis

        Raises
        ------
        QiitaDBStatusError
            Analysis is public
        """
        with qdb.sql_connection.TRN:
            self._lock_check()
            sql = """UPDATE qiita.{0} SET description = %s
                     WHERE analysis_id = %s""".format(self._table)
            qdb.sql_connection.TRN.add(sql, [description, self._id])
            qdb.sql_connection.TRN.execute()

    @property
    def samples(self):
        """The artifact and samples attached to the analysis

        Returns
        -------
        dict
            Format is {artifact_id: [sample_id, sample_id, ...]}
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT artifact_id, array_agg(
                        sample_id ORDER BY sample_id)
                     FROM qiita.analysis_sample
                     WHERE analysis_id = %s
                     GROUP BY artifact_id"""
            qdb.sql_connection.TRN.add(sql, [self._id])
            return dict(qdb.sql_connection.TRN.execute_fetchindex())

    @property
    def dropped_samples(self):
        """The samples that were selected but dropped in processing

        Returns
        -------
        dict of sets
            Format is {artifact_id: {sample_id, sample_id, ...}, ...}
        """
        with qdb.sql_connection.TRN:
            bioms = self.biom_tables
            if not bioms:
                return {}

            # get all samples selected for the analysis, converting lists to
            # sets for fast searching. Overhead less this way
            # for large analyses
            all_samples = {k: set(v) for k, v in viewitems(self.samples)}

            for biom, filepath in viewitems(bioms):
                table = load_table(filepath)
                ids = set(table.ids())
                for k in all_samples:
                    all_samples[k] = all_samples[k] - ids

            # what's left are unprocessed samples, so return
            return all_samples

    @property
    def data_types(self):
        """Returns all data types used in the analysis

        Returns
        -------
        list of str
            Data types in the analysis
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT DISTINCT data_type
                     FROM qiita.data_type
                        JOIN qiita.artifact USING (data_type_id)
                        JOIN qiita.analysis_sample USING (artifact_id)
                     WHERE analysis_id = %s
                     ORDER BY data_type"""
            qdb.sql_connection.TRN.add(sql, [self._id])
            return qdb.sql_connection.TRN.execute_fetchflatten()

    @property
    def shared_with(self):
        """The user the analysis is shared with

        Returns
        -------
        list of int
            User ids analysis is shared with
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT email FROM qiita.analysis_users
                     WHERE analysis_id = %s"""
            qdb.sql_connection.TRN.add(sql, [self._id])
            return [qdb.user.User(uid)
                    for uid in qdb.sql_connection.TRN.execute_fetchflatten()]

    @property
    def all_associated_filepath_ids(self):
        """Get all associated filepath_ids

        Returns
        -------
        list
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT filepath_id
                     FROM qiita.filepath
                        JOIN qiita.analysis_filepath USING (filepath_id)
                     WHERE analysis_id = %s"""
            qdb.sql_connection.TRN.add(sql, [self._id])
            filepaths = set(qdb.sql_connection.TRN.execute_fetchflatten())

            sql = """SELECT filepath_id
                     FROM qiita.analysis_job
                        JOIN qiita.job USING (job_id)
                        JOIN qiita.job_results_filepath USING (job_id)
                        JOIN qiita.filepath USING (filepath_id)
                     WHERE analysis_id = %s"""
            qdb.sql_connection.TRN.add(sql, [self._id])
            return filepaths.union(
                qdb.sql_connection.TRN.execute_fetchflatten())

    @property
    def biom_tables(self):
        """The biom tables of the analysis

        Returns
        -------
        dict
            Dictonary in the form {data_type: full BIOM filepath}
        """
        fps = [(_id, fp) for _id, fp, ftype in qdb.util.retrieve_filepaths(
            "analysis_filepath", "analysis_id", self._id)
            if ftype == 'biom']

        if fps:
            fps_ids = [f[0] for f in fps]
            with qdb.sql_connection.TRN:
                sql = """SELECT filepath_id, data_type FROM qiita.filepath
                            JOIN qiita.analysis_filepath USING (filepath_id)
                            JOIN qiita.data_type USING (data_type_id)
                            WHERE filepath_id IN %s"""
                qdb.sql_connection.TRN.add(sql, [tuple(fps_ids)])
                data_types = dict(qdb.sql_connection.TRN.execute_fetchindex())

            return {data_types[_id]: f for _id, f in fps}
        else:
            return {}

    @property
    def mapping_file(self):
        """Returns the mapping file for the analysis

        Returns
        -------
        str or None
            full filepath to the mapping file or None if not generated
        """
        fp = [fp for _, fp, fp_type in qdb.util.retrieve_filepaths(
            "analysis_filepath", "analysis_id", self._id)
            if fp_type == 'plain_text']

        if fp:
            # returning the actual path vs. an array
            return fp[0]
        else:
            return None

    @property
    def tgz(self):
        """Returns the tgz file of the analysis

        Returns
        -------
        str or None
            full filepath to the mapping file or None if not generated
        """
        fp = [fp for _, fp, fp_type in qdb.util.retrieve_filepaths(
            "analysis_filepath", "analysis_id", self._id)
            if fp_type == 'tgz']

        if fp:
            # returning the actual path vs. an array
            return fp[0]
        else:
            return None

    @property
    def step(self):
        """Returns the current step of the analysis

        Returns
        -------
        str
            The current step of the analysis

        Raises
        ------
        ValueError
            If the step is not set up
        """
        with qdb.sql_connection.TRN:
            self._lock_check()
            sql = """SELECT step FROM qiita.analysis_workflow
                     WHERE analysis_id = %s"""
            qdb.sql_connection.TRN.add(sql, [self._id])
            try:
                return qdb.sql_connection.TRN.execute_fetchlast()
            except IndexError:
                raise ValueError("Step not set yet!")

    @step.setter
    def step(self, value):
        with qdb.sql_connection.TRN:
            self._lock_check()
            sql = """SELECT EXISTS(
                        SELECT analysis_id
                        FROM qiita.analysis_workflow
                        WHERE analysis_id = %s)"""
            qdb.sql_connection.TRN.add(sql, [self._id])
            step_exists = qdb.sql_connection.TRN.execute_fetchlast()

            if step_exists:
                sql = """UPDATE qiita.analysis_workflow SET step = %s
                         WHERE analysis_id = %s"""
            else:
                sql = """INSERT INTO qiita.analysis_workflow
                            (step, analysis_id)
                         VALUES (%s, %s)"""
            qdb.sql_connection.TRN.add(sql, [value, self._id])
            qdb.sql_connection.TRN.execute()

    @property
    def jobs(self):
        """A list of jobs included in the analysis

        Returns
        -------
        list of qiita_db.job.Job
            Job ids for jobs in analysis. Empty list if no jobs attached.
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT job_id FROM qiita.analysis_job
                     WHERE analysis_id = %s""".format(self._table)
            qdb.sql_connection.TRN.add(sql, [self._id])
            return [qdb.job.Job(jid)
                    for jid in qdb.sql_connection.TRN.execute_fetchflatten()]

    @property
    def pmid(self):
        """Returns pmid attached to the analysis

        Returns
        -------
        str or None
            returns the PMID or None if none is attached
        """
        with qdb.sql_connection.TRN:
            sql = "SELECT pmid FROM qiita.{0} WHERE analysis_id = %s".format(
                self._table)
            qdb.sql_connection.TRN.add(sql, [self._id])
            return qdb.sql_connection.TRN.execute_fetchlast()

    @pmid.setter
    def pmid(self, pmid):
        """adds pmid to the analysis

        Parameters
        ----------
        pmid: str
            pmid to set for study

        Raises
        ------
        QiitaDBStatusError
            Analysis is public

        Notes
        -----
        An analysis should only ever have one PMID attached to it.
        """
        with qdb.sql_connection.TRN:
            self._lock_check()
            sql = """UPDATE qiita.{0} SET pmid = %s
                     WHERE analysis_id = %s""".format(self._table)
            qdb.sql_connection.TRN.add(sql, [pmid, self._id])
            qdb.sql_connection.TRN.execute()

    # @property
    # def parent(self):
    #     """Returns the id of the parent analysis this was forked from"""
    #     return QiitaDBNotImplementedError()

    # @property
    # def children(self):
    #     return QiitaDBNotImplementedError()

    # ---- Functions ----
    def has_access(self, user):
        """Returns whether the given user has access to the analysis

        Parameters
        ----------
        user : User object
            User we are checking access for

        Returns
        -------
        bool
            Whether user has access to analysis or not
        """
        with qdb.sql_connection.TRN:
            # if admin or superuser, just return true
            if user.level in {'superuser', 'admin'}:
                return True

            return self in Analysis.get_by_status('public') | \
                user.private_analyses | user.shared_analyses

    def summary_data(self):
        """Return number of studies, artifacts, and samples selected

        Returns
        -------
        dict
            counts keyed to their relevant type
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT
                        COUNT(DISTINCT study_id) as studies,
                        COUNT(DISTINCT artifact_id) as artifacts,
                        COUNT(DISTINCT sample_id) as samples
                    FROM qiita.study_artifact
                        JOIN qiita.analysis_sample USING (artifact_id)
                    WHERE analysis_id = %s"""
            qdb.sql_connection.TRN.add(sql, [self._id])
            return dict(qdb.sql_connection.TRN.execute_fetchindex()[0])

    def share(self, user):
        """Share the analysis with another user

        Parameters
        ----------
        user: User object
            The user to share the analysis with
        """
        with qdb.sql_connection.TRN:
            self._lock_check()

            # Make sure the analysis is not already shared with the given user
            if user.id in self.shared_with:
                return

            sql = """INSERT INTO qiita.analysis_users (analysis_id, email)
                     VALUES (%s, %s)"""
            qdb.sql_connection.TRN.add(sql, [self._id, user.id])
            qdb.sql_connection.TRN.execute()

    def unshare(self, user):
        """Unshare the analysis with another user

        Parameters
        ----------
        user: User object
            The user to unshare the analysis with
        """
        with qdb.sql_connection.TRN:
            self._lock_check()

            sql = """DELETE FROM qiita.analysis_users
                     WHERE analysis_id = %s AND email = %s"""
            qdb.sql_connection.TRN.add(sql, [self._id, user.id])
            qdb.sql_connection.TRN.execute()

    def add_samples(self, samples):
        """Adds samples to the analysis

        Parameters
        ----------
        samples : dictionary of lists
            samples and the artifact id they come from in form
            {artifact_id: [sample1, sample2, ...], ...}
        """
        with qdb.sql_connection.TRN:
            self._lock_check()

            for aid, samps in viewitems(samples):
                # get previously selected samples for aid and filter them out
                sql = """SELECT sample_id
                         FROM qiita.analysis_sample
                         WHERE artifact_id = %s AND analysis_id = %s"""
                qdb.sql_connection.TRN.add(sql, [aid, self._id])
                prev_selected = qdb.sql_connection.TRN.execute_fetchflatten()

                select = set(samps).difference(prev_selected)
                sql = """INSERT INTO qiita.analysis_sample
                            (analysis_id, artifact_id, sample_id)
                         VALUES (%s, %s, %s)"""
                args = [[self._id, aid, s] for s in select]
                qdb.sql_connection.TRN.add(sql, args, many=True)
                qdb.sql_connection.TRN.execute()

    def remove_samples(self, artifacts=None, samples=None):
        """Removes samples from the analysis

        Parameters
        ----------
        artifacts : list, optional
            Artifacts to remove, default None
        samples : list, optional
            sample ids to remove, default None

        Notes
        -----
         - When only a list of samples given, the samples will be removed from
           all artifacts it is associated with
        - When only a list of artifacts is given, all samples associated with
          that artifact are removed
        - If both are passed, the given samples are removed from the given
          artifacts
        """
        with qdb.sql_connection.TRN:
            self._lock_check()
            if artifacts and samples:
                sql = """DELETE FROM qiita.analysis_sample
                         WHERE analysis_id = %s
                            AND artifact_id = %s
                            AND sample_id = %s"""
                # Build the SQL arguments to remove the samples of the
                # given artifacts.
                args = [[self._id, a.id, s]
                        for a, s in product(artifacts, samples)]
            elif artifacts:
                sql = """DELETE FROM qiita.analysis_sample
                         WHERE analysis_id = %s AND artifact_id = %s"""
                args = [[self._id, a.id] for a in artifacts]
            elif samples:
                sql = """DELETE FROM qiita.analysis_sample
                         WHERE analysis_id = %s AND sample_id = %s"""
                args = [[self._id, s] for s in samples]
            else:
                raise IncompetentQiitaDeveloperError(
                    "Must provide list of samples and/or proc_data for "
                    "removal")

            qdb.sql_connection.TRN.add(sql, args, many=True)
            qdb.sql_connection.TRN.execute()

    def generate_tgz(self):
        fps_ids = self.all_associated_filepath_ids
        with qdb.sql_connection.TRN:
            sql = """SELECT filepath, data_directory_id FROM qiita.filepath
                        WHERE filepath_id IN %s"""
            qdb.sql_connection.TRN.add(sql, [tuple(fps_ids)])

            full_fps = [join(qdb.util.get_mountpoint_path_by_id(mid), f)
                        for f, mid in
                        qdb.sql_connection.TRN.execute_fetchindex()]

            _, analysis_mp = qdb.util.get_mountpoint('analysis')[0]
            tgz = join(analysis_mp, '%d_files.tgz' % self.id)
            try:
                with taropen(tgz, "w:gz") as tar:
                    for f in full_fps:
                        tar.add(f, arcname=basename(f))
                error_txt = ''
                return_value = 0
            except Exception as e:
                error_txt = str(e)
                return_value = 1

            if return_value == 0:
                self._add_file(tgz, 'tgz')

        return '', error_txt, return_value

    def build_files(self,
                    rarefaction_depth=None,
                    merge_duplicated_sample_ids=False):
        """Builds biom and mapping files needed for analysis

        Parameters
        ----------
        rarefaction_depth : int, optional
            Defaults to ``None``. If ``None``, do not rarefy. Otherwise, rarefy
            all samples to this number of observations
        merge_duplicated_sample_ids : bool, optional
            If the duplicated sample ids in the selected studies should be
            merged or prepended with the artifact ids. False (default) prepends
            the artifact id

        Raises
        ------
        TypeError
            If `rarefaction_depth` is not an integer
        ValueError
            If `rarefaction_depth` is less than or equal to zero

        Notes
        -----
        Creates biom tables for each requested data type
        Creates mapping file for requested samples
        """
        with qdb.sql_connection.TRN:
            if rarefaction_depth is not None:
                if type(rarefaction_depth) is not int:
                    raise TypeError("rarefaction_depth must be in integer")
                if rarefaction_depth <= 0:
                    raise ValueError(
                        "rarefaction_depth must be greater than 0")

            # in practice we could retrieve samples in each of the following
            # calls but this will mean calling the DB multiple times and will
            # make testing much harder as we will need to have analyses at
            # different stages and possible errors.
            samples = self.samples

            # figuring out if we are going to have duplicated samples, again
            # doing it here cause it's computational cheaper
            # 1. merge samples per data_type, reference used and the command id
            #    if not one of the tables is not 'Pick closed-reference OTUs'
            #    it's safer to always rename. Note that grouped_samples is
            #    basically how many biom tables we are going to create
            rename_dup_samples = False
            grouped_samples = {}
            for k, v in viewitems(samples):
                a = qdb.artifact.Artifact(k)
                p = a.processing_parameters
                c = p.command
                if c.name != 'Pick closed-reference OTUs':
                    rename_dup_samples = True
                    break
                l = "%s.%d.%d" % (a.data_type, p.values['reference'], c.id)
                if l not in grouped_samples:
                    grouped_samples[l] = []
                grouped_samples[l].append((k, v))
            # 2. if rename_dup_samples is still False, make sure that we don't
            #    need to rename samples by checking that there are not
            #    duplicated samples per group
            if not rename_dup_samples:
                for _, t in viewitems(grouped_samples):
                    # this element only has one table, continue
                    if len(t) == 1:
                        continue
                    dup_samples = set()
                    for _, s in t:
                        # this set is not to make the samples unique, cause
                        # they already are, but cast it as a set so we can
                        # perform the following operations
                        s = set(s)
                        if dup_samples & s:
                            rename_dup_samples = merge_duplicated_sample_ids
                            break
                        dup_samples = dup_samples | s

            self._build_mapping_file(samples, rename_dup_samples)
            self._build_biom_tables(grouped_samples, rarefaction_depth,
                                    rename_dup_samples)

    def _build_biom_tables(self, grouped_samples, rarefaction_depth=None,
                           rename_dup_samples=False):
        """Build tables and add them to the analysis"""
        with qdb.sql_connection.TRN:
            base_fp = qdb.util.get_work_base_dir()

            _, base_fp = qdb.util.get_mountpoint(self._table)[0]
            for label, tables in viewitems(grouped_samples):
                data_type, reference_id, command_id = label.split('.')
                new_table = None
                artifact_ids = []
                for aid, samples in tables:
                    artifact = qdb.artifact.Artifact(aid)
                    artifact_ids.append(str(aid))

                    # the next loop is assuming that an artifact can have only
                    # one biom, which is a safe assumption until we generate
                    # artifacts from multiple bioms and even then we might
                    # only have one biom
                    biom_table_fp = None
                    for _, fp, fp_type in artifact.filepaths:
                        if fp_type == 'biom':
                            biom_table_fp = fp
                            break
                    if not biom_table_fp:
                        raise RuntimeError(
                            "Artifact %s does not have a biom table associated"
                            % aid)

                    # loading the found biom table
                    biom_table = load_table(biom_table_fp)
                    # filtering samples to keep those selected by the user
                    biom_table_samples = set(biom_table.ids())
                    selected_samples = biom_table_samples.intersection(samples)
                    biom_table.filter(selected_samples, axis='sample',
                                      inplace=True)
                    if len(biom_table.ids()) == 0:
                        continue

                    if rename_dup_samples:
                        ids_map = {_id: "%d.%s" % (aid, _id)
                                   for _id in biom_table.ids()}
                        biom_table.update_ids(ids_map, 'sample', True, True)

                    if new_table is None:
                        new_table = biom_table
                    else:
                        new_table = new_table.merge(biom_table)

                if not new_table or len(new_table.ids()) == 0:
                    # if we get to this point the only reason for failure is
                    # rarefaction
                    raise RuntimeError("All samples filtered out from "
                                       "analysis due to rarefaction level")

                # add the metadata column for study the samples come from,
                # this is useful in case the user download the bioms
                study_md = {'study': artifact.study.title,
                            'artifact_ids': ', '.join(artifact_ids),
                            'reference_id': reference_id,
                            'command_id': command_id}
                samples_md = {sid: study_md for sid in new_table.ids()}
                new_table.add_metadata(samples_md, axis='sample')

                if rarefaction_depth is not None:
                    new_table = new_table.subsample(rarefaction_depth)
                    if len(new_table.ids()) == 0:
                        raise RuntimeError(
                            "All samples filtered out due to rarefacion level")

                # write out the file
                fn = "%d_analysis_dt-%s_r-%s_c-%s.biom" % (
                    self._id, data_type, reference_id, command_id)
                biom_fp = join(base_fp, fn)
                with biom_open(biom_fp, 'w') as f:
                    new_table.to_hdf5(
                        f, "Generated by Qiita. Analysis %d Datatype %s "
                        "Reference %s Command %s" % (self._id, data_type,
                                                     reference_id, command_id))
                self._add_file(fn, "biom", data_type=data_type)

    def _build_mapping_file(self, samples, rename_dup_samples=False):
        """Builds the combined mapping file for all samples
           Code modified slightly from qiime.util.MetadataMap.__add__"""
        with qdb.sql_connection.TRN:
            # query to get the latest qiime mapping file
            sql = """SELECT filepath
                     FROM qiita.filepath
                        JOIN qiita.prep_template_filepath USING (filepath_id)
                        JOIN qiita.prep_template USING (prep_template_id)
                        JOIN qiita.filepath_type USING (filepath_type_id)
                     WHERE filepath_type = 'qiime_map'
                        AND artifact_id IN (SELECT *
                                            FROM qiita.find_artifact_roots(%s))
                     ORDER BY filepath_id DESC LIMIT 1"""
            _, fp = qdb.util.get_mountpoint('templates')[0]

            all_ids = set()
            to_concat = []
            for aid, samps in viewitems(samples):
                qdb.sql_connection.TRN.add(sql, [aid])
                qm_fp = qdb.sql_connection.TRN.execute_fetchindex()[0][0]

                # Parse the mapping file
                qm = qdb.metadata_template.util.load_template_to_dataframe(
                    join(fp, qm_fp), index='#SampleID')

                # if we are not going to merge the duplicated samples
                # append the aid to the sample name
                if rename_dup_samples:
                    qm['original_SampleID'] = qm.index
                    qm['#SampleID'] = "%d." % aid + qm.index
                    qm['qiita_aid'] = aid
                    samps = set(['%d.%s' % (aid, _id) for _id in samps])
                    qm.set_index('#SampleID', inplace=True, drop=True)
                else:
                    samps = set(samps) - all_ids
                    all_ids.update(samps)

                # appending study metadata to the analysis
                study = qdb.artifact.Artifact(aid).study
                study_owner = study.owner
                study_info = study.info
                pi = study_info['principal_investigator']
                qm['qiita_study_title'] = study.title
                qm['qiita_study_alias'] = study.info['study_alias']
                qm['qiita_owner'] = study_owner.info['name']
                qm['qiita_principal_investigator'] = pi.name

                qm = qm.loc[samps]
                to_concat.append(qm)

            merged_map = pd.concat(to_concat)

            # forcing QIIME column order
            cols = merged_map.columns.values.tolist()
            cols.remove('BarcodeSequence')
            cols.remove('LinkerPrimerSequence')
            cols.remove('Description')
            cols = (['BarcodeSequence', 'LinkerPrimerSequence'] + cols +
                    ['Description'])
            merged_map = merged_map[cols]

            # Save the mapping file
            _, base_fp = qdb.util.get_mountpoint(self._table)[0]
            mapping_fp = join(base_fp, "%d_analysis_mapping.txt" % self._id)
            merged_map.to_csv(mapping_fp, index_label='#SampleID',
                              na_rep='unknown', sep='\t')

            self._add_file("%d_analysis_mapping.txt" % self._id, "plain_text")

    def _add_file(self, filename, filetype, data_type=None):
        """adds analysis item to database

        Parameters
        ----------
        filename : str
            filename to add to analysis
        filetype : {plain_text, biom}
        data_type : str, optional
        """
        with qdb.sql_connection.TRN:
            filetype_id = qdb.util.convert_to_id(filetype, 'filepath_type')
            _, mp = qdb.util.get_mountpoint('analysis')[0]
            fpid = qdb.util.insert_filepaths([
                (join(mp, filename), filetype_id)], -1, 'analysis', 'filepath',
                move_files=False)[0]

            col = ""
            dtid = ""
            if data_type:
                col = ", data_type_id"
                dtid = ", %d" % qdb.util.convert_to_id(data_type, "data_type")

            sql = """INSERT INTO qiita.analysis_filepath
                        (analysis_id, filepath_id{0})
                     VALUES (%s, %s{1})""".format(col, dtid)
            qdb.sql_connection.TRN.add(sql, [self._id, fpid])
            qdb.sql_connection.TRN.execute()


class Collection(qdb.base.QiitaStatusObject):
    """
    Analysis overview object to track a multi-analysis collection.

    Attributes
    ----------
    name: str
        Name of the Collection
    description: str
        Description of what the collection is investigating
    owner: User object
        Owner of the Collection
    analyses: list of Analysis Objects
        all analyses that are part of the collection
    highlights : list of Job objects
        Important job results related to the collection

    Methods
    -------
    add_analysis
    remove_analysis
    highlight_job
    remove_highlight
    share
    unshare
    """
    _table = "collection"
    _analysis_table = "collection_analysis"
    _highlight_table = "collection_job"
    _share_table = "collection_users"

    def _status_setter_checks(self):
        r"""Perform a check to make sure not setting status away from public
        """
        if self.check_status(("public", )):
            raise qdb.exceptions.QiitaDBStatusError(
                "Illegal operation on public collection!")

    @classmethod
    def create(cls, owner, name, description=None):
        """Creates a new collection on the database

        Parameters
        ----------
        owner : User object
            Owner of the collection
        name : str
            Name of the collection
        description : str, optional
            Brief description of the collecton's overarching goal
        """
        with qdb.sql_connection.TRN:
            sql = """INSERT INTO qiita.{0} (email, name, description)
                     VALUES (%s, %s, %s)""".format(cls._table)
            qdb.sql_connection.TRN.add(sql, [owner.id, name, description])
            qdb.sql_connection.TRN.execute()

    @classmethod
    def delete(cls, id_):
        """Deletes a collection from the database

        Parameters
        ----------
        id_ : int
            ID of the collection to delete

        Raises
        ------
        QiitaDBStatusError
            Trying to delete a public collection
        """
        with qdb.sql_connection.TRN:
            if cls(id_).status == "public":
                raise qdb.exceptions.QiitaDBStatusError(
                    "Can't delete public collection!")

            sql = "DELETE FROM qiita.{0} WHERE collection_id = %s"
            for table in (cls._analysis_table, cls._highlight_table,
                          cls._share_table, cls._table):
                qdb.sql_connection.TRN.add(sql.format(table), [id_])

            qdb.sql_connection.TRN.execute()

    # --- Properties ---
    @property
    def name(self):
        with qdb.sql_connection.TRN:
            sql = "SELECT name FROM qiita.{0} WHERE collection_id = %s".format(
                self._table)
            qdb.sql_connection.TRN.add(sql, [self._id])
            return qdb.sql_connection.TRN.execute_fetchlast()

    @name.setter
    def name(self, value):
        with qdb.sql_connection.TRN:
            self._status_setter_checks()

            sql = """UPDATE qiita.{0} SET name = %s
                     WHERE collection_id = %s""".format(self._table)
            qdb.sql_connection.TRN.add(sql, [value, self._id])
            qdb.sql_connection.TRN.execute()

    @property
    def description(self):
        with qdb.sql_connection.TRN:
            sql = """SELECT description FROM qiita.{0}
                     WHERE collection_id = %s""".format(self._table)
            qdb.sql_connection.TRN.add(sql, [self._id])
            return qdb.sql_connection.TRN.execute_fetchlast()

    @description.setter
    def description(self, value):
        with qdb.sql_connection.TRN:
            self._status_setter_checks()

            sql = """UPDATE qiita.{0} SET description = %s
                     WHERE collection_id = %s""".format(self._table)
            qdb.sql_connection.TRN.add(sql, [value, self._id])
            qdb.sql_connection.TRN.execute()

    @property
    def owner(self):
        with qdb.sql_connection.TRN:
            sql = """SELECT email FROM qiita.{0}
                     WHERE collection_id = %s""".format(self._table)
            qdb.sql_connection.TRN.add(sql, [self._id])
            return qdb.user.User(qdb.sql_connection.TRN.execute_fetchlast())

    @property
    def analyses(self):
        with qdb.sql_connection.TRN:
            sql = """SELECT analysis_id FROM qiita.{0}
                     WHERE collection_id = %s""".format(self._analysis_table)
            qdb.sql_connection.TRN.add(sql, [self._id])
            return [Analysis(aid)
                    for aid in qdb.sql_connection.TRN.execute_fetchflatten()]

    @property
    def highlights(self):
        with qdb.sql_connection.TRN:
            sql = """SELECT job_id FROM qiita.{0}
                     WHERE collection_id = %s""".format(self._highlight_table)
            qdb.sql_connection.TRN.add(sql, [self._id])
            return [qdb.job.Job(jid)
                    for jid in qdb.sql_connection.TRN.execute_fetchflatten()]

    @property
    def shared_with(self):
        with qdb.sql_connection.TRN:
            sql = """SELECT email FROM qiita.{0}
                     WHERE collection_id = %s""".format(self._share_table)
            qdb.sql_connection.TRN.add(sql, [self._id])
            return [qdb.user.User(uid)
                    for uid in qdb.sql_connection.TRN.execute_fetchflatten()]

    # --- Functions ---
    def add_analysis(self, analysis):
        """Adds an analysis to the collection object

        Parameters
        ----------
        analysis : Analysis object
        """
        with qdb.sql_connection.TRN:
            self._status_setter_checks()

            sql = """INSERT INTO qiita.{0} (analysis_id, collection_id)
                     VALUES (%s, %s)""".format(self._analysis_table)
            qdb.sql_connection.TRN.add(sql, [analysis.id, self._id])
            qdb.sql_connection.TRN.execute()

    def remove_analysis(self, analysis):
        """Remove an analysis from the collection object

        Parameters
        ----------
        analysis : Analysis object
        """
        with qdb.sql_connection.TRN:
            self._status_setter_checks()

            sql = """DELETE FROM qiita.{0}
                     WHERE analysis_id = %s
                        AND collection_id = %s""".format(self._analysis_table)
            qdb.sql_connection.TRN.add(sql, [analysis.id, self._id])
            qdb.sql_connection.TRN.execute()

    def highlight_job(self, job):
        """Marks a job as important to the collection

        Parameters
        ----------
        job : Job object
        """
        with qdb.sql_connection.TRN:
            self._status_setter_checks()

            sql = """INSERT INTO qiita.{0} (job_id, collection_id)
                     VALUES (%s, %s)""".format(self._highlight_table)
            qdb.sql_connection.TRN.add(sql, [job.id, self._id])
            qdb.sql_connection.TRN.execute()

    def remove_highlight(self, job):
        """Removes job importance from the collection

        Parameters
        ----------
        job : Job object
        """
        with qdb.sql_connection.TRN:
            self._status_setter_checks()

            sql = """DELETE FROM qiita.{0}
                     WHERE job_id = %s
                        AND collection_id = %s""".format(self._highlight_table)
            qdb.sql_connection.TRN.add(sql, [job.id, self._id])
            qdb.sql_connection.TRN.execute()

    def share(self, user):
        """Shares the collection with another user

        Parameters
        ----------
        user : User object
        """
        with qdb.sql_connection.TRN:
            self._status_setter_checks()

            sql = """INSERT INTO qiita.{0} (email, collection_id)
                     VALUES (%s, %s)""".format(self._share_table)
            qdb.sql_connection.TRN.add(sql, [user.id, self._id])
            qdb.sql_connection.TRN.execute()

    def unshare(self, user):
        """Unshares the collection with another user

        Parameters
        ----------
        user : User object
        """
        with qdb.sql_connection.TRN:
            self._status_setter_checks()

            sql = """DELETE FROM qiita.{0}
                     WHERE email = %s
                        AND collection_id = %s""".format(self._share_table)
            qdb.sql_connection.TRN.add(sql, [user.id, self._id])
            qdb.sql_connection.TRN.execute()
