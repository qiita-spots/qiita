"""
Objects for dealing with Qiita analyses

This module provides the implementation of the Analysis class.

Classes
-------
- `Analysis` -- A Qiita Analysis class
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
from os.path import join

from future.utils import viewitems
from biom import load_table
from biom.table import Table

from qiita_core.exceptions import IncompetentQiitaDeveloperError
from .sql_connection import SQLConnectionHandler
from .base import QiitaStatusObject
from .exceptions import QiitaDBNotImplementedError, QiitaDBStatusError
from .util import convert_to_id, get_work_base_dir, get_table_cols


class Analysis(QiitaStatusObject):
    """
    Analysis object to access to the Qiita Analysis information

    Attributes
    ----------
    owner
    name
    description
    samples
    data_types
    biom_tables
    shared_with
    jobs
    pmid
    parent
    children

    Methods
    -------
    add_samples
    remove_samples
    build_biom_table
    add_biom_tables
    remove_biom_tables
    add_jobs
    share
    unshare
    """

    _table = "analysis"

    def _lock_check(self, conn_handler):
        """Raises QiitaDBStatusError if analysis is public"""
        if self.check_status({"public", "completed", "error"}):
            raise QiitaDBStatusError("Analysis is locked!")

    def _status_setter_checks(self, conn_handler):
        r"""Perform a check to make sure not setting status away from public
        """
        self._lock_check(conn_handler)

    @classmethod
    def get_public(cls):
        """Returns analysis id for all public Analyses

        Returns
        -------
        list of int
            All public analysses in the database
        """
        conn_handler = SQLConnectionHandler()
        sql = ("SELECT analysis_id FROM qiita.{0} WHERE "
               "{0}_status_id = %s".format(cls._table))
        # MAGIC NUMBER 6: status id for a public study
        return [x[0] for x in conn_handler.execute_fetchall(sql, (6,))]

    @classmethod
    def create(cls, owner, name, description, parent=None):
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
        """
        conn_handler = SQLConnectionHandler()
        # TODO after demo: if exists()

        # insert analysis information into table with "in construction" status
        sql = ("INSERT INTO qiita.{0} (email, name, description, "
               "analysis_status_id) VALUES (%s, %s, %s, 1) "
               "RETURNING analysis_id".format(cls._table))
        a_id = conn_handler.execute_fetchone(
            sql, (owner.id, name, description))[0]

        # add parent if necessary
        if parent:
            sql = ("INSERT INTO qiita.analysis_chain (parent_id, child_id) "
                   "VALUES (%s, %s)")
            conn_handler.execute(sql, (parent.id, a_id))

        return cls(a_id)

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
    def biom_tables(self):
        """The biom tables of the analysis

        Returns
        -------
        list of int or None
            ProcessedData ids of the biom tables or None if no tables generated
        """
        conn_handler = SQLConnectionHandler()
        # magic number 6 is biom file type
        sql = ("SELECT af.filepath_id FROM qiita.analysis_filepath af JOIN "
               "qiita.filepath f USE(filepath_id) WHERE af.analysis_id = %s"
               "AND f.filepath_type_id = 6")
        tables = conn_handler.execute_fetchall(sql, (self._id, ))
        if tables == []:
            return None
        return [table[0] for table in tables]

    @property
    def mapping_file(self):
        """The mapping table of the analysis

        Returns
        -------
        int or None
            ProcessedData id of the mapping file or None if no mapping file
        """
        conn_handler = SQLConnectionHandler()
        # magic number 8 is biom file type
        sql = ("SELECT af.filepath_id FROM qiita.analysis_filepath af JOIN "
               "qiita.filepath f USE(filepath_id) WHERE af.analysis_id = %s"
               "AND f.filepath_type_id = 8")
        if tables == []:
            return None
        return [table[0] for table in tables]

    @property
    def jobs(self):
        """A list of jobs included in the analysis

        Returns
        -------
        list of ints
            Job ids for jobs in analysis
        """
        conn_handler = SQLConnectionHandler()
        sql = ("SELECT job_id FROM qiita.analysis_job WHERE "
               "analysis_id = %s".format(self._table))
        job_ids = conn_handler.execute_fetchall(sql, (self._id, ))
        if job_ids == []:
            return None
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
    def share(self, user):
        """Share the analysis with another user

        Parameters
        ----------
        user: User object
            The user to share the study with
        """
        conn_handler = SQLConnectionHandler()
        self._lock_check(conn_handler)

        sql = ("INSERT INTO qiita.analysis_users (analysis_id, email) VALUES "
               "(%s, %s)")
        conn_handler.execute(sql, (self._id, user.id))

    def unshare(self, user):
        """Unshare the analysis with another user

        Parameters
        ----------
        user: User object
            The user to unshare the study with
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
        samples : list of tuples
            samples and the processed data id they come from in form
            [(processed_data_id, sample_id), ...]
        """
        conn_handler = SQLConnectionHandler()
        self._lock_check(conn_handler)
        sql = ("INSERT INTO qiita.analysis_sample (analysis_id, sample_id, "
               "processed_data_id) VALUES (%s, %s, %s)")
        conn_handler.executemany(sql, [(self._id, s[1], s[0])
                                       for s in samples])

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

    def build_biom_table_mapping_file(self):
        """Creates BIOM tables and mapping files for samples in analysis

        Notes
        -----
        Seperate BIOM tables and mapping files are created for each data type.
        """
        # build the samples dict as list of samples keyed to their proc_data_id
        conn_handler = SQLConnectionHandler()
        sql = ("SELECT processed_data_id, array_agg(sample_id ORDER BY "
               "sample_id) FROM qiita.analysis_sample WHERE analysis_id = %s "
               "GROUP BY processed_data_id")
        samples = dict(conn_handler.execute_fetchall(sql, [self._id]))

        _build_biom_tables(samples)
        _build_mapping_files(samples, conn_handler)

    def _build_biom_tables(self, samples):
        """Build tables and add them to the analysis"""
        # filter and combine all study BIOM tables needed for each data type
        new_tables = {dt: None for dt in self.data_types}
        base_fp = get_work_base_dir()
        for pid, samps in viewitems(samps):
            # one biom table attached to each processed data object
            proc_data = ProcessedData(pid)
            proc_data_fp = proc_data.get_filepaths()[0]
            # make sure we're getting a biom filetype (magic number 6)
            if proc_data_fp[1] != 6:
                raise ValueError("ProcessedData %s not a biom formatted file!"
                                 % pid)
            table_fp = join(base_fp, proc_data_fp[0])
            table = load_table(table_fp)
            # filter for just the wanted samples and merge into new table
            # this if/else setup avoids needing a blank table to start merges
            table.filter(samps, axis='sample', inplace=True)
            if new_tables[proc_data.data_type] is None:
                new_tables[proc_data.data_type] = table
            else:
                new_tables[proc_data.data_type].merge(table)

        # add the new tables to the analysis
        processed_data = []
        for proc_data, table in viewitems(new_tables):
            biom_fp = join(base_fp, "processed_data/analysis_%i_%s.biom" %
                           (self._id, proc_data))
            with open(biom_fp, 'w') as f:
                new_table.to_hdf5(f, "Combined samples for analysis %d and "
                                  "data_type %s" % (self._id, proc_data))
            processed_data.append(ProcessedData.create(
                "processed_params_analysis", 1, (biom_fp, 6),
                data_type=proc_data))

        self.add_processed_data(processed_data)

    def _build_mapping_file(self, samples, conn_handler):
        """Builds the mapping file for all samples
           Code modified slightly from qiime.util.MetadataMap.__add__"""
        # We will keep track of all unique sample_ids and metadata headers
        # we have seen as we go, as well as studies already seen
        all_sample_ids = set()
        all_headers = set()
        all_studies = set()

        merged_data = defaultdict(lambda: defaultdict(lambda: None))
        for pid, samples in viewitems(samples):
            study = ProcesseData(pid).study
            if study in all_studies:
                # samples already added by other processed data file in study
                continue
            all_studies.add(study)
            # query out the combined table of metadata for all samples
            headers = get_table_cols("sample_%d" % study, conn_handler)
            sql = ("SELECT rs.sample_type, rs.collection_timestamp, "
                   "rs.host_subject_id,rs.description,{0},rs.sample_id "
                   "FROM qiita.required_sample_info rs JOIN qiita.sample_{1} "
                   "ss USING(sample_id) WHERE rs.sample_id IN %s AND "
                   "rs.study_id = %s".format(",".join(
                       ["ss.%s" % h for h in headers]), study))
            metadata = conn_handler.execute_fetchall(sql, (samples, study))
            headers = ["sample_type", "collection_timestamp",
                       "host_subject_id", "description"] + headers
            all_headers = all_headers.update(headers)
            # add all the metadata to merged_data
            for data in metadata:
                sample_id = data.pop()
                if sample_id not in all_sample_ids:
                    all_sample_ids.add(sample_id)
                else:
                    raise ValueError("Duplicate sample id found: %s" %
                                     sample_id)

                for header, value in zip(headers, data):
                    merged_data[sample_id][header] = value

        # write mapping file out
        all_headers = sorted(list(all_headers))
        base_fp = get_work_base_dir()
        mapping_fp = join(base_fp, "processed_data/analysis_%i_mapping.txt" %
                          (self._id, proc_data))

        with open(mapping_fp, 'w') as f:
            f.write("#SampleID\t%s\n" % '\t'.join(all_headers))
            for sample, metadata in viewitems(merged_data):
                data = []
                for header in all_headers:
                    data.append(metadata[header] if
                                metadata[header] is not None else "")
                f.write("%s\t%s\n" % (sample, "\t".join(data)))

        # create PreprocessedData for file.  8 is plain text filetype
        processed_data = ProcessedData.create(
            "processed_params_analysis", 1, (mapping_fp, 8),
            data_type=proc_data)

        self.add_processed_data([processed_data])

    def add_processed_data(self, proc_data):
        """Adds processed data to the analysis

        Parameters
        ----------
        proc_data : list of ProcessedData objects
            processed data to attach to analysis
        """
        conn_handler = SQLConnectionHandler()
        self._lock_check(conn_handler)
        file_ids = []
        for data in proc_data:
            file_ids.extend(data.get_filepath_ids())
        sql = ("INSERT INTO qiita.analysis_filepath (analysis_id, filepath_id)"
               " VALUES (%s, %s)")
        conn_handler.executemany(sql, [(self._id, f) for f in file_ids])

    def remove_processed_data(self, proc_data):
        """Removes processed_data from the analysis

        Parameters
        ----------
        proc_data : list of ProcessedData objects
            processed data to remove from analysis
        """
        conn_handler = SQLConnectionHandler()
        self._lock_check(conn_handler)
        file_ids = []
        for data in proc_data:
            file_ids.extend(data.get_filepath_ids())
        sql = ("DELETE FROM qiita.analysis_filepath WHERE analysis_id = %s "
               "AND filepath_id = %s")
        conn_handler.executemany(sql, [(self._id, f) for f in file_ids])

    def add_jobs(self, jobs):
        """Adds a list of jobs to the analysis

        Parameters
        ----------
            jobs : list of Job objects
        """
        conn_handler = SQLConnectionHandler()
        self._lock_check(conn_handler)
        sql = ("INSERT INTO qiita.analysis_job (analysis_id, job_id) "
               "VALUES (%s, %s)")
        conn_handler.executemany(sql, [(self._id, job.id) for job in jobs])
