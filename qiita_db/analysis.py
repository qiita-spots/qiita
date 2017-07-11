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
from os.path import join

from future.utils import viewitems
from biom import load_table
from biom.util import biom_open
from re import sub
import pandas as pd

from qiita_core.exceptions import IncompetentQiitaDeveloperError
from qiita_core.qiita_settings import qiita_config
import qiita_db as qdb


class Analysis(qdb.base.QiitaObject):
    """
    Analysis object to access to the Qiita Analysis information

    Attributes
    ----------
    owner
    name
    description
    samples
    data_types
    artifacts
    shared_with
    jobs
    pmid

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
    add_artifact
    set_error
    """

    _table = "analysis"
    _portal_table = "analysis_portal"
    _analysis_id_column = 'analysis_id'

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
            # Sandboxed analyses are the analyses that have not been started
            # and hence they don't have an artifact yet
            if status == 'sandbox':
                sql = """SELECT DISTINCT analysis
                         FROM qiita.analysis
                            JOIN qiita.analysis_portal USING (analysis_id)
                            JOIN qiita.portal_type USING (portal_type_id)
                         WHERE portal = %s AND analysis_id NOT IN (
                            SELECT analysis_id
                            FROM qiita.analysis_artifact)"""
                qdb.sql_connection.TRN.add(sql, [qiita_config.portal])
            else:
                sql = """SELECT DISTINCT analysis_id
                         FROM qiita.analysis_artifact
                            JOIN qiita.artifact USING (artifact_id)
                            JOIN qiita.visibility USING (visibility_id)
                            JOIN qiita.analysis_portal USING (analysis_id)
                            JOIN qiita.portal_type USING (portal_type_id)
                         WHERE visibility = %s AND portal = %s"""
                qdb.sql_connection.TRN.add(sql, [status, qiita_config.portal])

            return set(
                cls(aid)
                for aid in qdb.sql_connection.TRN.execute_fetchflatten())

    @classmethod
    def create(cls, owner, name, description, from_default=False,
               merge_duplicated_sample_ids=False):
        """Creates a new analysis on the database

        Parameters
        ----------
        owner : User object
            The analysis' owner
        name : str
            Name of the analysis
        description : str
            Description of the analysis
        from_default : bool, optional
            If True, use the default analysis to populate selected samples.
            Default False.
        merge_duplicated_sample_ids : bool, optional
            If the duplicated sample ids in the selected studies should be
            merged or prepended with the artifact ids. False (default) prepends
            the artifact id

        Returns
        -------
        qdb.analysis.Analysis
            The newly created analysis
        """
        with qdb.sql_connection.TRN:
            portal_id = qdb.util.convert_to_id(
                qiita_config.portal, 'portal_type', 'portal')

            # Create the row in the analysis table
            sql = """INSERT INTO qiita.{0}
                        (email, name, description)
                    VALUES (%s, %s, %s)
                    RETURNING analysis_id""".format(cls._table)
            qdb.sql_connection.TRN.add(
                sql, [owner.id, name, description])
            a_id = qdb.sql_connection.TRN.execute_fetchlast()

            if from_default:
                # Move samples into that new analysis
                dflt_id = owner.default_analysis.id
                sql = """UPDATE qiita.analysis_sample
                         SET analysis_id = %s
                         WHERE analysis_id = %s"""
                qdb.sql_connection.TRN.add(sql, [a_id, dflt_id])

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

            instance = cls(a_id)

            # Once the analysis is created, we can create the mapping file and
            # the initial set of artifacts
            plugin = qdb.software.Software.from_name_and_version(
                'Qiita', 'alpha')
            cmd = plugin.get_command('build_analysis_files')
            params = qdb.software.Parameters.load(
                cmd, values_dict={
                    'analysis': a_id,
                    'merge_dup_sample_ids': merge_duplicated_sample_ids})
            job = qdb.processing_job.ProcessingJob.create(
                owner, params)
            sql = """INSERT INTO qiita.analysis_processing_job
                        (analysis_id, processing_job_id)
                     VALUES (%s, %s)"""
            qdb.sql_connection.TRN.add(sql, [a_id, job.id])
            qdb.sql_connection.TRN.execute()

        # Doing the submission outside of the transaction
        job.submit()
        return instance

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

            # Check if the analysis has any artifact
            sql = """SELECT EXISTS(SELECT *
                                   FROM qiita.analysis_artifact
                                   WHERE analysis_id = %s)"""
            qdb.sql_connection.TRN.add(sql, [_id])
            if qdb.sql_connection.TRN.execute_fetchlast():
                raise qdb.exceptions.QiitaDBOperationNotPermittedError(
                    "Can't delete analysis %d, has artifacts attached"
                    % _id)

            sql = "DELETE FROM qiita.analysis_filepath WHERE {0} = %s".format(
                cls._analysis_id_column)
            args = [_id]
            qdb.sql_connection.TRN.add(sql, args)

            sql = "DELETE FROM qiita.analysis_portal WHERE {0} = %s".format(
                cls._analysis_id_column)
            qdb.sql_connection.TRN.add(sql, args)

            sql = "DELETE FROM qiita.analysis_sample WHERE {0} = %s".format(
                cls._analysis_id_column)
            qdb.sql_connection.TRN.add(sql, args)

            sql = """DELETE FROM qiita.analysis_processing_job
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
    def artifacts(self):
        with qdb.sql_connection.TRN:
            sql = """SELECT artifact_id
                     FROM qiita.analysis_artifact
                     WHERE analysis_id = %s"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            return [qdb.artifact.Artifact(aid)
                    for aid in qdb.sql_connection.TRN.execute_fetchflatten()]

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
    def jobs(self):
        """The jobs generating the initial artifacts for the analysis

        Returns
        -------
        list of qiita_db.processing_job.Processing_job
            Job ids for jobs in analysis. Empty list if no jobs attached.
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT processing_job_id
                     FROM qiita.analysis_processing_job
                     WHERE analysis_id = %s"""
            qdb.sql_connection.TRN.add(sql, [self._id])
            return [qdb.processing_job.ProcessingJob(jid)
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
            sql = """UPDATE qiita.{0} SET pmid = %s
                     WHERE analysis_id = %s""".format(self._table)
            qdb.sql_connection.TRN.add(sql, [pmid, self._id])
            qdb.sql_connection.TRN.execute()

    @property
    def can_be_publicized(self):
        """Returns whether the analysis can be made public

        Returns
        -------
        bool
            Whether the analysis can be publicized or not
        """
        # The analysis can be made public if all the artifacts used
        # to get the samples from are public
        with qdb.sql_connection.TRN:
            sql = """SELECT DISTINCT artifact_id
                     FROM qiita.analysis_sample
                     WHERE analysis_id = %s"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            return all(
                [qdb.artifact.Artifact(aid).visibility == 'public'
                 for aid in qdb.sql_connection.TRN.execute_fetchflatten()])

    def add_artifact(self, artifact):
        """Adds an artifact to the analysis

        Parameters
        ----------
        artifact : qiita_db.artifact.Artifact
            The artifact to be added
        """
        with qdb.sql_connection.TRN:
            sql = """INSERT INTO qiita.analysis_artifact
                        (analysis_id, artifact_id)
                     SELECT %s, %s
                     WHERE NOT EXISTS(SELECT *
                                      FROM qiita.analysis_artifact
                                      WHERE analysis_id = %s
                                        AND artifact_id = %s)"""
            qdb.sql_connection.TRN.add(sql, [self.id, artifact.id,
                                             self.id, artifact.id])

    def set_error(self, error_msg):
        """Sets the analysis error

        Parameters
        ----------
        error_msg : str
            The error message
        """
        with qdb.sql_connection.TRN:
            le = qdb.logger.LogEntry.create('Runtime', error_msg)
            sql = """UPDATE qiita.analysis
                     SET logging_id = %s
                     WHERE analysis_id = %s"""
            qdb.sql_connection.TRN.add(sql, [le.id, self.id])
            qdb.sql_connection.TRN.execute()

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

    def can_edit(self, user):
        """Returns whether the given user can edit the analysis

        Parameters
        ----------
        user : User object
            User we are checking edit permissions for

        Returns
        -------
        bool
            Whether user can edit the study or not
        """
        # The analysis is editable only if the user is the owner, is in the
        # shared list or the user is an admin
        return (user.level in {'superuser', 'admin'} or self.owner == user or
                user in self.shared_with)

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
        # Make sure the analysis is not already shared with the given user
        if user.id == self.owner or user.id in self.shared_with:
            return

        with qdb.sql_connection.TRN:
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
            sql = """DELETE FROM qiita.analysis_users
                     WHERE analysis_id = %s AND email = %s"""
            qdb.sql_connection.TRN.add(sql, [self._id, user.id])
            qdb.sql_connection.TRN.execute()

    def _lock_samples(self):
        """Only dflt analyses can have samples added/removed

        Raises
        ------
        qiita_db.exceptions.QiitaDBOperationNotPermittedError
            If the analysis is not a default analysis
        """
        with qdb.sql_connection.TRN:
            sql = "SELECT dflt FROM qiita.analysis WHERE analysis_id = %s"
            qdb.sql_connection.TRN.add(sql, [self.id])
            if not qdb.sql_connection.TRN.execute_fetchlast():
                raise qdb.exceptions.QiitaDBOperationNotPermittedError(
                    "Can't add/remove samples from this analysis")

    def add_samples(self, samples):
        """Adds samples to the analysis

        Parameters
        ----------
        samples : dictionary of lists
            samples and the artifact id they come from in form
            {artifact_id: [sample1, sample2, ...], ...}
        """
        with qdb.sql_connection.TRN:
            self._lock_samples()

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
            self._lock_samples()
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

    def build_files(self, merge_duplicated_sample_ids):
        """Builds biom and mapping files needed for analysis

        Parameters
        ----------
        merge_duplicated_sample_ids : bool
            If the duplicated sample ids in the selected studies should be
            merged or prepended with the artifact ids. If false prepends
            the artifact id

        Notes
        -----
        Creates biom tables for each requested data type
        Creates mapping file for requested samples
        """
        with qdb.sql_connection.TRN:
            # in practice we could retrieve samples in each of the following
            # calls but this will mean calling the DB multiple times and will
            # make testing much harder as we will need to have analyses at
            # different stages and possible errors.
            samples = self.samples
            # gettin the info of all the artifacts to save SQL time
            bioms_info = qdb.util.get_artifacts_bioms_information(
                samples.keys())

            # figuring out if we are going to have duplicated samples, again
            # doing it here cause it's computational cheaper
            # 1. merge samples per: data_type, reference used and
            # the command id
            # Note that grouped_samples is basically how many biom tables we
            # are going to create
            rename_dup_samples = False
            grouped_samples = {}
            for aid, asamples in viewitems(samples):
                # find the artifat info, [0] there should be only 1 info
                ainfo = [bi for bi in bioms_info
                         if bi['artifact_id'] == aid][0]

                data_type = ainfo['data_type']
                # algorithm is: processing_method | parent_processing, just
                # keeping processing_method
                algorithm = ainfo['algorithm'].split('|')[0].strip()
                files = ainfo['files']

                l = "%s || %s" % (data_type, algorithm)
                # deblur special case, we need to account for file name
                if 'deblur-workflow' in algorithm:
                    # [0] there is always just one biom
                    l += " || %s" % [f for f in files
                                     if f.endswith('.biom')][0]
                else:
                    l += " ||"

                if l not in grouped_samples:
                    grouped_samples[l] = []
                grouped_samples[l].append((aid, asamples))
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
            biom_files = self._build_biom_tables(
                grouped_samples, rename_dup_samples)

            return biom_files

    def _build_biom_tables(self, grouped_samples, rename_dup_samples=False):
        """Build tables and add them to the analysis"""
        with qdb.sql_connection.TRN:
            base_fp = qdb.util.get_work_base_dir()

            biom_files = []
            for label, tables in viewitems(grouped_samples):
                data_type, algorithm, files = [
                    l.strip() for l in label.split('||')]

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

                # write out the file
                data_type = sub('[^0-9a-zA-Z]+', '', data_type)
                algorithm = sub('[^0-9a-zA-Z]+', '', algorithm)
                files = sub('[^0-9a-zA-Z]+', '', files)
                info = "%s_%s_%s" % (data_type, algorithm, files)
                fn = "%d_analysis_%s.biom" % (self._id, info)
                biom_fp = join(base_fp, fn)
                with biom_open(biom_fp, 'w') as f:
                    new_table.to_hdf5(
                        f, "Generated by Qiita, analysis id: %d, info: %s" % (
                            self._id, label))
                biom_files.append((data_type, biom_fp))
        return biom_files

    def _build_mapping_file(self, samples, rename_dup_samples=False):
        """Builds the combined mapping file for all samples
           Code modified slightly from qiime.util.MetadataMap.__add__"""
        with qdb.sql_connection.TRN:
            all_ids = set()
            to_concat = []
            for aid, samps in viewitems(samples):
                qiime_map_fp = qdb.artifact.Artifact(
                    aid).prep_templates[0].qiime_map_fp

                # Parse the mapping file
                qm = qdb.metadata_template.util.load_template_to_dataframe(
                    qiime_map_fp, index='#SampleID')

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
                              na_rep='unknown', sep='\t', encoding='utf-8')

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
