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
from collections import defaultdict
from itertools import product
from os.path import join

from future.utils import viewitems
from biom import load_table
from biom.util import biom_open
import pandas as pd
from skbio.util import find_duplicates

from qiita_core.exceptions import IncompetentQiitaDeveloperError
from .sql_connection import SQLConnectionHandler
from .base import QiitaStatusObject
from .data import ProcessedData
from .study import Study
from .exceptions import QiitaDBStatusError, QiitaDBError, QiitaDBUnknownIDError
from .util import (convert_to_id, get_work_base_dir,
                   get_mountpoint, insert_filepaths)


class Analysis(QiitaStatusObject):
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
    _analysis_id_column = 'analysis_id'

    def _lock_check(self, conn_handler):
        """Raises QiitaDBStatusError if analysis is not in_progress"""
        if self.check_status({"queued", "running", "public", "completed",
                              "error"}):
            raise QiitaDBStatusError("Analysis is locked!")

    def _status_setter_checks(self):
        r"""Perform a check to make sure not setting status away from public
        """
        if self.check_status({"public"}):
            raise QiitaDBStatusError("Can't set status away from public!")

    @classmethod
    def get_by_status(cls, status):
        """Returns analysis ids for all Analyses with given status

        Parameters
        ----------
        status : str
            Status to search analyses for

        Returns
        -------
        set of int
            All analyses in the database with the given status
        """
        conn_handler = SQLConnectionHandler()
        sql = ("SELECT analysis_id FROM qiita.{0} a JOIN qiita.{0}_status ans "
               "ON a.analysis_status_id = ans.analysis_status_id WHERE "
               "ans.status = %s".format(cls._table))
        return {x[0] for x in conn_handler.execute_fetchall(sql, (status,))}

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
        queue = "create_analysis"
        conn_handler = SQLConnectionHandler()
        conn_handler.create_queue(queue)
        # TODO after demo: if exists()
        # Needed since issue #292 exists
        status_id = conn_handler.execute_fetchone(
            "SELECT analysis_status_id from qiita.analysis_status WHERE "
            "status = 'in_construction'")[0]
        if from_default:
            # insert analysis and move samples into that new analysis
            dflt_id = owner.default_analysis
            sql = """INSERT INTO qiita.{0}
                    (email, name, description, analysis_status_id)
                    VALUES (%s, %s, %s, %s)
                    RETURNING analysis_id""".format(cls._table)
            conn_handler.add_to_queue(queue, sql, (owner.id, name,
                                                   description, status_id))
            # MAGIC NUMBER 3: command selection step
            # needed so we skip the sample selection step
            sql = """INSERT INTO qiita.analysis_workflow
                    (analysis_id, step) VALUES (%s, %s)
                    RETURNING %s"""
            conn_handler.add_to_queue(queue, sql, ['{0}', 3, '{0}'])
            sql = """UPDATE qiita.analysis_sample
                     SET analysis_id = %s
                     WHERE analysis_id = %s RETURNING %s"""
            conn_handler.add_to_queue(queue, sql, ['{0}', dflt_id, '{0}'])
        else:
            # insert analysis information into table as "in construction"
            sql = """INSERT INTO qiita.{0}
                  (email, name, description, analysis_status_id)
                  VALUES (%s, %s, %s, %s)
                  RETURNING analysis_id""".format(cls._table)
            conn_handler.add_to_queue(
                queue, sql, (owner.id, name, description, status_id))

        # add parent if necessary
        if parent:
            sql = ("INSERT INTO qiita.analysis_chain (parent_id, child_id) "
                   "VALUES (%s, %s) RETURNING child_id")
            conn_handler.add_to_queue(queue, sql, [parent.id, '{0}'])

        a_id = conn_handler.execute_queue(queue)[0]
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
        # check if the analysis exist
        if not cls.exists(_id):
            raise QiitaDBUnknownIDError(_id, "analysis")

        queue = "delete_analysis_%d" % _id
        conn_handler = SQLConnectionHandler()
        conn_handler.create_queue(queue)

        sql = ("DELETE FROM qiita.analysis_filepath WHERE "
               "{0} = {1}".format(cls._analysis_id_column, _id))
        conn_handler.add_to_queue(queue, sql)

        sql = ("DELETE FROM qiita.analysis_workflow WHERE "
               "{0} = {1}".format(cls._analysis_id_column, _id))
        conn_handler.add_to_queue(queue, sql)

        sql = ("DELETE FROM qiita.analysis_sample WHERE "
               "{0} = {1}".format(cls._analysis_id_column, _id))
        conn_handler.add_to_queue(queue, sql)

        sql = ("DELETE FROM qiita.collection_analysis WHERE "
               "{0} = {1}".format(cls._analysis_id_column, _id))
        conn_handler.add_to_queue(queue, sql)

        # TODO: issue #1176

        sql = ("DELETE FROM qiita.{0} WHERE "
               "{1} = {2}".format(cls._table, cls._analysis_id_column, _id))
        conn_handler.add_to_queue(queue, sql)

        conn_handler.execute_queue(queue)

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
        conn_handler = SQLConnectionHandler()

        return conn_handler.execute_fetchone(
            "SELECT EXISTS(SELECT * FROM qiita.{0} WHERE "
            "{1}=%s)".format(cls._table, cls._analysis_id_column),
            (analysis_id, ))[0]

    # ---- Properties ----
    @property
    def owner(self):
        """The owner of the analysis

        Returns
        -------
        str
            Name of the Analysis
        """
        conn_handler = SQLConnectionHandler()
        sql = ("SELECT email FROM qiita.{0} WHERE "
               "analysis_id = %s".format(self._table))
        return conn_handler.execute_fetchone(sql, (self._id, ))[0]

    @property
    def name(self):
        """The name of the analysis

        Returns
        -------
        str
            Name of the Analysis
        """
        conn_handler = SQLConnectionHandler()
        sql = ("SELECT name FROM qiita.{0} WHERE "
               "analysis_id = %s".format(self._table))
        return conn_handler.execute_fetchone(sql, (self._id, ))[0]

    @property
    def timestamp(self):
        """The timestamp of the analysis

        Returns
        -------
        datetime
            Timestamp of the Analysis
        """
        conn_handler = SQLConnectionHandler()
        sql = ("SELECT timestamp FROM qiita.{0} WHERE "
               "analysis_id = %s".format(self._table))
        return conn_handler.execute_fetchone(sql, (self._id, ))[0]

    @property
    def description(self):
        """Returns the description of the analysis"""
        conn_handler = SQLConnectionHandler()
        sql = ("SELECT description FROM qiita.{0} WHERE "
               "analysis_id = %s".format(self._table))
        return conn_handler.execute_fetchone(sql, (self._id, ))[0]

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
        conn_handler = SQLConnectionHandler()
        self._lock_check(conn_handler)
        sql = ("UPDATE qiita.{0} SET description = %s WHERE "
               "analysis_id = %s".format(self._table))
        conn_handler.execute(sql, (description, self._id))

    @property
    def samples(self):
        """The processed data and samples attached to the analysis

        Returns
        -------
        dict
            Format is {processed_data_id: [sample_id, sample_id, ...]}
        """
        conn_handler = SQLConnectionHandler()
        sql = ("SELECT processed_data_id, sample_id FROM qiita.analysis_sample"
               " WHERE analysis_id = %s ORDER BY processed_data_id")
        ret_samples = defaultdict(list)
        # turn into dict of samples keyed to processed_data_id
        for pid, sample in conn_handler.execute_fetchall(sql, (self._id, )):
            ret_samples[pid].append(sample)
        return ret_samples

    @property
    def dropped_samples(self):
        """The samples that were selected but dropped in processing

        Returns
        -------
        dict of sets
            Format is {processed_data_id: {sample_id, sample_id, ...}, ...}
        """
        bioms = self.biom_tables
        if not bioms:
            return {}

        # get all samples selected for the analysis, converting lists to
        # sets for fast searching. Overhead less this way for large analyses
        all_samples = {k: set(v) for k, v in viewitems(self.samples)}

        for biom, filepath in viewitems(bioms):
            table = load_table(filepath)
            # remove the samples from the sets as they are found in the table
            proc_data_ids = set(sample['Processed_id']
                                for sample in table.metadata())
            ids = set(table.ids())
            for proc_data_id in proc_data_ids:
                all_samples[proc_data_id] = all_samples[proc_data_id] - ids

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
        sql = ("SELECT DISTINCT data_type from qiita.data_type d JOIN "
               "qiita.processed_data p ON p.data_type_id = d.data_type_id "
               "JOIN qiita.analysis_sample a ON p.processed_data_id = "
               "a.processed_data_id WHERE a.analysis_id = %s ORDER BY "
               "data_type")
        conn_handler = SQLConnectionHandler()
        return [x[0] for x in conn_handler.execute_fetchall(sql, (self._id, ))]

    @property
    def shared_with(self):
        """The user the analysis is shared with

        Returns
        -------
        list of int
            User ids analysis is shared with
        """
        conn_handler = SQLConnectionHandler()
        sql = ("SELECT email FROM qiita.analysis_users WHERE "
               "analysis_id = %s")
        return [u[0] for u in conn_handler.execute_fetchall(sql, (self._id, ))]

    @property
    def all_associated_filepath_ids(self):
        """Get all associated filepath_ids

        Returns
        -------
        list
        """
        conn_handler = SQLConnectionHandler()
        sql = """SELECT f.filepath_id
              FROM qiita.filepath f JOIN
              qiita.analysis_filepath af ON f.filepath_id = af.filepath_id
              WHERE af.analysis_id = %s"""
        filepaths = {row[0]
                     for row in conn_handler.execute_fetchall(sql, [self._id])}

        sql = """SELECT fp.filepath_id
              FROM qiita.analysis_job aj
                JOIN qiita.job j ON aj.job_id = j.job_id
                JOIN qiita.job_results_filepath jrfp ON aj.job_id = jrfp.job_id
                JOIN qiita.filepath fp ON jrfp.filepath_id = fp.filepath_id
              WHERE aj.analysis_id = %s"""

        job_filepaths = {row[0]
                         for row in conn_handler.execute_fetchall(sql,
                                                                  [self._id])}

        filepaths = filepaths.union(job_filepaths)

        return filepaths

    @property
    def biom_tables(self):
        """The biom tables of the analysis

        Returns
        -------
        dict
            Dictonary in the form {data_type: full BIOM filepath}
        """
        conn_handler = SQLConnectionHandler()
        fptypeid = convert_to_id("biom", "filepath_type")
        sql = ("SELECT dt.data_type, f.filepath FROM qiita.filepath f JOIN "
               "qiita.analysis_filepath af ON f.filepath_id = af.filepath_id "
               "JOIN qiita.data_type dt ON dt.data_type_id = af.data_type_id "
               "WHERE af.analysis_id = %s AND f.filepath_type_id = %s")
        tables = conn_handler.execute_fetchall(sql, (self._id, fptypeid))
        if not tables:
            return {}
        ret_tables = {}
        _, base_fp = get_mountpoint(self._table)[0]
        for fp in tables:
            ret_tables[fp[0]] = join(base_fp, fp[1])
        return ret_tables

    @property
    def mapping_file(self):
        """Returns the mapping file for the analysis

        Returns
        -------
        str or None
            full filepath to the mapping file or None if not generated
        """
        conn_handler = SQLConnectionHandler()
        fptypeid = convert_to_id("plain_text", "filepath_type")
        sql = ("SELECT f.filepath FROM qiita.filepath f JOIN "
               "qiita.analysis_filepath af ON f.filepath_id = af.filepath_id "
               "WHERE af.analysis_id = %s AND f.filepath_type_id = %s")
        mapping_fp = conn_handler.execute_fetchone(sql, (self._id, fptypeid))
        if not mapping_fp:
            return None

        _, base_fp = get_mountpoint(self._table)[0]
        return join(base_fp, mapping_fp[0])

    @property
    def step(self):
        conn_handler = SQLConnectionHandler()
        self._lock_check(conn_handler)
        sql = "SELECT step from qiita.analysis_workflow WHERE analysis_id = %s"
        try:
            return conn_handler.execute_fetchone(sql, (self._id,))[0]
        except TypeError:
            raise ValueError("Step not set yet!")

    @step.setter
    def step(self, value):
        conn_handler = SQLConnectionHandler()
        self._lock_check(conn_handler)
        sql = ("SELECT EXISTS(SELECT analysis_id from qiita.analysis_workflow "
               "WHERE analysis_id = %s)")
        step_exists = conn_handler.execute_fetchone(sql, (self._id,))[0]

        if step_exists:
            sql = ("UPDATE qiita.analysis_workflow SET step = %s WHERE "
                   "analysis_id = %s")
        else:
            sql = ("INSERT INTO qiita.analysis_workflow (step, analysis_id) "
                   "VALUES (%s, %s)")
        conn_handler.execute(sql, (value, self._id))

    @property
    def jobs(self):
        """A list of jobs included in the analysis

        Returns
        -------
        list of ints
            Job ids for jobs in analysis. Empty list if no jobs attached.
        """
        conn_handler = SQLConnectionHandler()
        sql = ("SELECT job_id FROM qiita.analysis_job WHERE "
               "analysis_id = %s".format(self._table))
        job_ids = conn_handler.execute_fetchall(sql, (self._id, ))
        return [job_id[0] for job_id in job_ids]

    @property
    def pmid(self):
        """Returns pmid attached to the analysis

        Returns
        -------
        str or None
            returns the PMID or None if none is attached
        """
        conn_handler = SQLConnectionHandler()
        sql = ("SELECT pmid FROM qiita.{0} WHERE "
               "analysis_id = %s".format(self._table))
        pmid = conn_handler.execute_fetchone(sql, (self._id, ))[0]
        return pmid

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
        conn_handler = SQLConnectionHandler()
        self._lock_check(conn_handler)
        sql = ("UPDATE qiita.{0} SET pmid = %s WHERE "
               "analysis_id = %s".format(self._table))
        conn_handler.execute(sql, (pmid, self._id))

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
        # if admin or superuser, just return true
        if user.level in {'superuser', 'admin'}:
            return True

        return self._id in Analysis.get_by_status('public') | \
            user.private_analyses | user.shared_analyses

    def summary_data(self):
        """Return number of studies, processed data, and samples selected

        Returns
        -------
        dict
            counts keyed to their relevant type
        """
        sql = """SELECT COUNT(DISTINCT study_id) as studies,
                COUNT(DISTINCT processed_data_id) as processed_data,
                COUNT(DISTINCT sample_id) as samples
                FROM qiita.study_processed_data
                JOIN qiita.analysis_sample USING (processed_data_id)
                WHERE analysis_id = %s"""
        conn_handler = SQLConnectionHandler()
        return dict(conn_handler.execute_fetchone(sql, [self._id]))

    def share(self, user):
        """Share the analysis with another user

        Parameters
        ----------
        user: User object
            The user to share the analysis with
        """
        conn_handler = SQLConnectionHandler()
        self._lock_check(conn_handler)

        # Make sure the analysis is not already shared with the given user
        if user.id in self.shared_with:
            return

        sql = ("INSERT INTO qiita.analysis_users (analysis_id, email) VALUES "
               "(%s, %s)")

        conn_handler.execute(sql, (self._id, user.id))

    def unshare(self, user):
        """Unshare the analysis with another user

        Parameters
        ----------
        user: User object
            The user to unshare the analysis with
        """
        conn_handler = SQLConnectionHandler()
        self._lock_check(conn_handler)

        sql = ("DELETE FROM qiita.analysis_users WHERE analysis_id = %s AND "
               "email = %s")

        conn_handler.execute(sql, (self._id, user.id))

    def add_samples(self, samples):
        """Adds samples to the analysis

        Parameters
        ----------
        samples : dictionary of lists
            samples and the processed data id they come from in form
            {processed_data_id: [sample1, sample2, ...], ...}
        """
        conn_handler = SQLConnectionHandler()
        self._lock_check(conn_handler)

        for pid, samps in viewitems(samples):
            # get previously selected samples  for pid and filter them out
            sql = """SELECT sample_id FROM qiita.analysis_sample
                WHERE processed_data_id = %s and analysis_id = %s"""
            prev_selected = [x[0] for x in
                             conn_handler.execute_fetchall(sql,
                                                           (pid, self._id))]

            select = set(samps).difference(prev_selected)
            sql = ("INSERT INTO qiita.analysis_sample "
                   "(analysis_id, processed_data_id, sample_id) VALUES "
                   "({}, %s, %s)".format(self._id))
            conn_handler.executemany(sql, [x for x in product([pid], select)])

    def remove_samples(self, proc_data=None, samples=None):
        """Removes samples from the analysis

        Parameters
        ----------
        proc_data : list, optional
            processed data ids to remove, default None
        samples : list, optional
            sample ids to remove, default None

        Notes
        -----
        When only a list of samples given, the samples will be removed from all
        processed data ids it is associated with

        When only a list of proc_data given, all samples associated with that
        processed data are removed

        If both are passed, the given samples are removed from the given
        processed data ids
        """
        conn_handler = SQLConnectionHandler()
        self._lock_check(conn_handler)
        if proc_data and samples:
            sql = ("DELETE FROM qiita.analysis_sample WHERE analysis_id = %s "
                   "AND processed_data_id = %s AND sample_id = %s")
            remove = []
            # build tuples for what samples to remove from what processed data
            for proc_id in proc_data:
                for sample_id in samples:
                    remove.append((self._id, proc_id, sample_id))
        elif proc_data:
            sql = ("DELETE FROM qiita.analysis_sample WHERE analysis_id = %s "
                   "AND processed_data_id = %s")
            remove = [(self._id, p) for p in proc_data]
        elif samples:
            sql = ("DELETE FROM qiita.analysis_sample WHERE analysis_id = %s "
                   "AND sample_id = %s")
            remove = [(self._id, s) for s in samples]
        else:
            raise IncompetentQiitaDeveloperError(
                "Must provide list of samples and/or proc_data for removal!")

        conn_handler.executemany(sql, remove)

    def build_files(self, rarefaction_depth=None):
        """Builds biom and mapping files needed for analysis

        Parameters
        ----------
        rarefaction_depth : int, optional
            Defaults to ``None``. If ``None``, do not rarefy. Otherwise, rarefy
            all samples to this number of observations

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
        if rarefaction_depth is not None:
            if type(rarefaction_depth) is not int:
                raise TypeError("rarefaction_depth must be in integer")
            if rarefaction_depth <= 0:
                raise ValueError("rarefaction_depth must be greater than 0")

        samples = self._get_samples()
        self._build_mapping_file(samples)
        self._build_biom_tables(samples, rarefaction_depth)

    def _get_samples(self):
        """Retrieves dict of samples to proc_data_id for the analysis"""
        conn_handler = SQLConnectionHandler()
        sql = ("SELECT processed_data_id, array_agg(sample_id ORDER BY "
               "sample_id) FROM qiita.analysis_sample WHERE analysis_id = %s "
               "GROUP BY processed_data_id")
        return dict(conn_handler.execute_fetchall(sql, [self._id]))

    def _build_biom_tables(self, samples, rarefaction_depth):
        """Build tables and add them to the analysis"""
        # filter and combine all study BIOM tables needed for each data type
        new_tables = {dt: None for dt in self.data_types}
        base_fp = get_work_base_dir()
        for pid, samps in viewitems(samples):
            # one biom table attached to each processed data object
            proc_data = ProcessedData(pid)
            proc_data_fp = proc_data.get_filepaths()[0][1]
            table_fp = join(base_fp, proc_data_fp)
            table = load_table(table_fp)
            # HACKY WORKAROUND FOR DEMO. Issue # 246
            # make sure samples not in biom table are not filtered for
            table_samps = set(table.ids())
            filter_samps = table_samps.intersection(samps)
            # add the metadata column for study the samples come from
            study_meta = {'Study': Study(proc_data.study).title,
                          'Processed_id': proc_data.id}
            samples_meta = {sid: study_meta for sid in filter_samps}
            # filter for just the wanted samples and merge into new table
            # this if/else setup avoids needing a blank table to start merges
            table.filter(filter_samps, axis='sample', inplace=True)
            table.add_metadata(samples_meta, axis='sample')
            data_type = proc_data.data_type()
            if new_tables[data_type] is None:
                new_tables[data_type] = table
            else:
                new_tables[data_type] = new_tables[data_type].merge(table)

        # add the new tables to the analysis
        _, base_fp = get_mountpoint(self._table)[0]
        for dt, biom_table in viewitems(new_tables):
            # rarefy, if specified
            if rarefaction_depth is not None:
                biom_table = biom_table.subsample(rarefaction_depth)
            # write out the file
            biom_fp = join(base_fp, "%d_analysis_%s.biom" % (self._id, dt))
            with biom_open(biom_fp, 'w') as f:
                biom_table.to_hdf5(f, "Analysis %s Datatype %s" %
                                   (self._id, dt))
            self._add_file("%d_analysis_%s.biom" % (self._id, dt),
                           "biom", data_type=dt)

    def _build_mapping_file(self, samples):
        """Builds the combined mapping file for all samples
           Code modified slightly from qiime.util.MetadataMap.__add__"""
        conn_handler = SQLConnectionHandler()
        all_sample_ids = set()
        sql = """SELECT filepath_id, filepath
                 FROM qiita.filepath
                    JOIN qiita.prep_template_filepath USING (filepath_id)
                    JOIN qiita.prep_template_preprocessed_data
                        USING (prep_template_id)
                    JOIN qiita.preprocessed_processed_data
                        USING (preprocessed_data_id)
                    JOIN qiita.filepath_type USING (filepath_type_id)
                 WHERE processed_data_id = %s
                    AND filepath_type = 'qiime_map'
                 ORDER BY filepath_id DESC"""
        _id, fp = get_mountpoint('templates')[0]
        to_concat = []

        for pid, samples in viewitems(samples):
            if len(samples) != len(set(samples)):
                duplicates = find_duplicates(samples)
                raise QiitaDBError("Duplicate sample ids found: %s"
                                   % ', '.join(duplicates))
            # Get the QIIME mapping file
            qiime_map_fp = conn_handler.execute_fetchall(sql, (pid,))[0][1]
            # Parse the mapping file
            qiime_map = pd.read_csv(
                join(fp, qiime_map_fp), sep='\t', keep_default_na=False,
                na_values=['unknown'], index_col=False,
                converters=defaultdict(lambda: str))
            qiime_map.set_index('#SampleID', inplace=True, drop=True)
            qiime_map = qiime_map.loc[samples]

            duplicates = all_sample_ids.intersection(qiime_map.index)
            if duplicates or len(samples) != len(set(samples)):
                # Duplicate samples so raise error
                raise QiitaDBError("Duplicate sample ids found: %s"
                                   % ', '.join(duplicates))
            all_sample_ids.update(qiime_map.index)
            to_concat.append(qiime_map)

        merged_map = pd.concat(to_concat)

        cols = merged_map.columns.values.tolist()
        cols.remove('BarcodeSequence')
        cols.remove('LinkerPrimerSequence')
        cols.remove('Description')
        new_cols = ['BarcodeSequence', 'LinkerPrimerSequence']
        new_cols.extend(cols)
        new_cols.append('Description')
        merged_map = merged_map[new_cols]

        # Save the mapping file
        _, base_fp = get_mountpoint(self._table)[0]
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
        conn_handler = SQLConnectionHandler()

        filetype_id = convert_to_id(filetype, 'filepath_type')
        _, mp = get_mountpoint('analysis')[0]
        fpid = insert_filepaths([
            (join(mp, filename), filetype_id)], -1, 'analysis', 'filepath',
            conn_handler, move_files=False)[0]

        col = ""
        dtid = ""
        if data_type:
            col = ",data_type_id"
            dtid = ",%d" % convert_to_id(data_type, "data_type")

        sql = ("INSERT INTO qiita.analysis_filepath (analysis_id, filepath_id"
               "{0}) VALUES (%s, %s{1})".format(col, dtid))
        conn_handler.execute(sql, (self._id, fpid))


class Collection(QiitaStatusObject):
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
            raise QiitaDBStatusError("Illegal operation on public collection!")

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
        conn_handler = SQLConnectionHandler()

        sql = ("INSERT INTO qiita.{0} (email, name, description) "
               "VALUES (%s, %s, %s)".format(cls._table))
        conn_handler.execute(sql, [owner.id, name, description])

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
        conn_handler = SQLConnectionHandler()
        if cls(id_).status == "public":
            raise QiitaDBStatusError("Can't delete public collection!")

        queue = "remove_collection_%d" % id_
        conn_handler.create_queue(queue)

        for table in (cls._analysis_table, cls._highlight_table,
                      cls._share_table, cls._table):
            conn_handler.add_to_queue(
                queue, "DELETE FROM qiita.{0} WHERE "
                "collection_id = %s".format(table), [id_])

        conn_handler.execute_queue(queue)

    # --- Properties ---
    @property
    def name(self):
        sql = ("SELECT name FROM qiita.{0} WHERE "
               "collection_id = %s".format(self._table))
        conn_handler = SQLConnectionHandler()
        return conn_handler.execute_fetchone(sql, [self._id])[0]

    @name.setter
    def name(self, value):
        conn_handler = SQLConnectionHandler()
        self._status_setter_checks()

        sql = ("UPDATE qiita.{0} SET name = %s WHERE "
               "collection_id = %s".format(self._table))
        conn_handler.execute(sql, [value, self._id])

    @property
    def description(self):
        sql = ("SELECT description FROM qiita.{0} WHERE "
               "collection_id = %s".format(self._table))
        conn_handler = SQLConnectionHandler()
        return conn_handler.execute_fetchone(sql, [self._id])[0]

    @description.setter
    def description(self, value):
        conn_handler = SQLConnectionHandler()
        self._status_setter_checks()

        sql = ("UPDATE qiita.{0} SET description = %s WHERE "
               "collection_id = %s".format(self._table))
        conn_handler.execute(sql, [value, self._id])

    @property
    def owner(self):
        sql = ("SELECT email FROM qiita.{0} WHERE "
               "collection_id = %s".format(self._table))
        conn_handler = SQLConnectionHandler()
        return conn_handler.execute_fetchone(sql, [self._id])[0]

    @property
    def analyses(self):
        sql = ("SELECT analysis_id FROM qiita.{0} WHERE "
               "collection_id = %s".format(self._analysis_table))
        conn_handler = SQLConnectionHandler()
        return [x[0] for x in conn_handler.execute_fetchall(sql, [self._id])]

    @property
    def highlights(self):
        sql = ("SELECT job_id FROM qiita.{0} WHERE "
               "collection_id = %s".format(self._highlight_table))
        conn_handler = SQLConnectionHandler()
        return [x[0] for x in conn_handler.execute_fetchall(sql, [self._id])]

    @property
    def shared_with(self):
        sql = ("SELECT email FROM qiita.{0} WHERE "
               "collection_id = %s".format(self._share_table))
        conn_handler = SQLConnectionHandler()
        return [x[0] for x in conn_handler.execute_fetchall(sql, [self._id])]

    # --- Functions ---
    def add_analysis(self, analysis):
        """Adds an analysis to the collection object

        Parameters
        ----------
        analysis : Analysis object
        """
        conn_handler = SQLConnectionHandler()
        self._status_setter_checks()

        sql = ("INSERT INTO qiita.{0} (analysis_id, collection_id) "
               "VALUES (%s, %s)".format(self._analysis_table))
        conn_handler.execute(sql, [analysis.id, self._id])

    def remove_analysis(self, analysis):
        """Remove an analysis from the collection object

        Parameters
        ----------
        analysis : Analysis object
        """
        conn_handler = SQLConnectionHandler()
        self._status_setter_checks()

        sql = ("DELETE FROM qiita.{0} WHERE analysis_id = %s AND "
               "collection_id = %s".format(self._analysis_table))
        conn_handler = SQLConnectionHandler()
        conn_handler.execute(sql, [analysis.id, self._id])

    def highlight_job(self, job):
        """Marks a job as important to the collection

        Parameters
        ----------
        job : Job object
        """
        conn_handler = SQLConnectionHandler()
        self._status_setter_checks()

        sql = ("INSERT INTO qiita.{0} (job_id, collection_id) "
               "VALUES (%s, %s)".format(self._highlight_table))
        conn_handler = SQLConnectionHandler()
        conn_handler.execute(sql, [job.id, self._id])

    def remove_highlight(self, job):
        """Removes job importance from the collection

        Parameters
        ----------
        job : Job object
        """
        conn_handler = SQLConnectionHandler()
        self._status_setter_checks()

        sql = ("DELETE FROM qiita.{0} WHERE job_id = %s AND "
               "collection_id = %s".format(self._highlight_table))
        conn_handler = SQLConnectionHandler()
        conn_handler.execute(sql, [job.id, self._id])

    def share(self, user):
        """Shares the collection with another user

        Parameters
        ----------
        user : User object
        """
        conn_handler = SQLConnectionHandler()
        self._status_setter_checks()

        sql = ("INSERT INTO qiita.{0} (email, collection_id) "
               "VALUES (%s, %s)".format(self._share_table))
        conn_handler = SQLConnectionHandler()
        conn_handler.execute(sql, [user.id, self._id])

    def unshare(self, user):
        """Unshares the collection with another user

        Parameters
        ----------
        user : User object
        """
        conn_handler = SQLConnectionHandler()
        self._status_setter_checks()

        sql = ("DELETE FROM qiita.{0} WHERE "
               "email = %s AND collection_id = %s".format(self._share_table))
        conn_handler = SQLConnectionHandler()
        conn_handler.execute(sql, [user.id, self._id])
