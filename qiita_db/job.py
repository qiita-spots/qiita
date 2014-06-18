"""
Objects for dealing with Qiita jobs

This module provides the implementation of the Job class.

Classes
-------
- `Job` -- A Qiita Job class
"""
# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from __future__ import division
from json import dumps, loads
from os import remove
from os.path import basename, join, commonprefix
from shutil import copy
from time import strftime
from datetime import date
from tarfile import open as taropen

from .base import QiitaStatusObject
from .util import (insert_filepaths, get_db_files_base_dir, get_work_base_dir,
                   convert_to_id)
from .exceptions import QiitaDBDuplicateError
from .sql_connection import SQLConnectionHandler


class Job(QiitaStatusObject):
    """
    Job object to access to the Qiita Job information

    Attributes
    ----------
    datatype
    command
    options
    results
    error_msg

    Methods
    -------
    set_error
    add_results
    """
    _table = "job"

    @classmethod
    def exists(cls, datatype, command, options):
        """Checks if the given job already exists

        Parameters
        ----------
        datatype : str
            Datatype the job is operating on
        command : str
            The command run on the data
        options : dict
            Options for the command in the format {option: value}

        Returns
        -------
        bool
            Whether the job exists or not
        """
        sql = ("SELECT EXISTS(SELECT * FROM  qiita.{0} WHERE data_type_id = %s"
               " AND command_id = %s AND options = %s)".format(cls._table))
        conn_handler = SQLConnectionHandler()
        datatype_id = convert_to_id(datatype, "data_type", conn_handler)
        command_id = convert_to_id(command, "command", conn_handler)
        opts_json = dumps(options, sort_keys=True, separators=(',', ':'))
        return conn_handler.execute_fetchone(
            sql, (datatype_id, command_id, opts_json))[0]

    @classmethod
    def create(cls, datatype, command, options, analysis):
        """Creates a new job on the database

        Parameters
        ----------
        datatype : str
            The datatype in which this job applies
        command : str
            The identifier of the command executed in this job
        options: dict
            The options for the command in format {option: value}
        analysis : Analysis object
            The analysis which this job belongs to

        Returns
        -------
        Job object
            The newly created job
        """
        if cls.exists(datatype, command, options):
            raise QiitaDBDuplicateError(
                "Job", "datatype: %s, command: %s, options: %s"
                % (datatype, command, options))

        # Get the datatype and command ids from the strings
        conn_handler = SQLConnectionHandler()
        datatype_id = convert_to_id(datatype, "data_type", conn_handler)
        command_id = convert_to_id(command, "command", conn_handler)

        # JSON the options dictionary
        opts_json = dumps(options, sort_keys=True, separators=(',', ':'))
        # Create the job and return it
        sql = ("INSERT INTO qiita.{0} (data_type_id, job_status_id, "
               "command_id, options) VALUES "
               "(%s, %s, %s, %s) RETURNING job_id").format(cls._table)
        job_id = conn_handler.execute_fetchone(sql, (datatype_id, command_id,
                                               1, opts_json))[0]

        # add job to analysis
        sql = ("INSERT INTO qiita.analysis_job (analysis_id, job_id) VALUES "
               "(%s, %s)")
        conn_handler.execute(sql, (analysis.id, job_id))

        return cls(job_id)

    @property
    def datatype(self):
        """Returns the datatype of the job

        Returns
        -------
        str
            datatype of the job
        """
        sql = ("SELECT data_type from qiita.data_type WHERE data_type_id = "
               "(SELECT data_type_id from qiita.{0} WHERE "
               "job_id = %s)".format(self._table))
        conn_handler = SQLConnectionHandler()
        return conn_handler.execute_fetchone(sql, (self._id, ))[0]

    @property
    def command(self):
        """Returns the command of the job

        Returns
        -------
        str
            command run by the job
        """
        sql = ("SELECT command from qiita.command WHERE command_id = "
               "(SELECT command_id from qiita.{0} WHERE "
               "job_id = %s)".format(self._table))
        conn_handler = SQLConnectionHandler()
        return conn_handler.execute_fetchone(sql, (self._id, ))[0]

    @property
    def options(self):
        """Options used in the job

        Returns
        -------
        dict
            options in the format {option: setting}
        """
        sql = ("SELECT options FROM qiita.{0} WHERE "
               "job_id = %s".format(self._table))
        conn_handler = SQLConnectionHandler()
        return loads(conn_handler.execute_fetchone(sql, (self._id, ))[0])

    @property
    def results(self):
        """List of job result filepaths

        Returns
        -------
        list
            Filepaths to the result files

        Notes
        -----
        All files are automatically copied into the working directory and
        untar-ed if necessary. The filepaths point to these files/folders in
        the working directory.
        """
        # Copy files to working dir, untar if necessary, then return filepaths
        sql = ("SELECT filepath, filepath_type_id FROM qiita.filepath WHERE "
               "filepath_id IN (SELECT filepath_id FROM "
               "qiita.job_results_filepath WHERE job_id = %s)")
        conn_handler = SQLConnectionHandler()
        results = conn_handler.execute_fetchall(sql, (self._id, ))
        # create new list, untaring as necessary
        results_untar = []
        outpath = get_work_base_dir()
        for fp, fp_type in results:
            if fp_type == 7:
                # untar to work directory
                with taropen(join(get_db_files_base_dir(),
                                  self._table, fp)) as tar:
                    base = commonprefix(tar.getnames())
                    tar.extractall(path=outpath)
            else:
                # copy to work directory
                copy(join(get_db_files_base_dir(), self._table, fp), outpath)
                base = fp
            results_untar.append(join(outpath, base))
        return results_untar

    @property
    def error_msg(self):
        """String with an error message, if the job failed

        Returns
        -------
        str or None
            error message/traceback for a job, or None if none exists
        """
        sql = ("SELECT msg FROM qiita.logging WHERE log_id = (SELECT log_id "
               "FROM qiita.{0} WHERE job_id = %s)".format(self._table))
        conn_handler = SQLConnectionHandler()
        msg = conn_handler.execute_fetchone(sql, (self._id, ))
        return msg if msg is None else msg[0]

# --- Functions ---
    def set_error(self, msg, severity):
        """Logs an error for the job

        Parameters
        ----------
        msg : str
            Error message/stacktrace if available
        severity: int
            Severity code of error
        """
        # insert the error into the logging table
        errtime = ' '.join((date.today().isoformat(), strftime("%H:%M:%S")))
        self._log_error(msg, severity, errtime)

    def _log_error(self, msg, severity, timestamp):
        sql = ("INSERT INTO qiita.logging (time, severity_id, msg) VALUES "
               "(%s, %s, %s) RETURNING log_id")
        conn_handler = SQLConnectionHandler()
        logid = conn_handler.execute_fetchone(sql, (timestamp,
                                                    severity, msg))[0]

        # attach the error to the job and set to error
        sql = ("UPDATE qiita.{0} SET log_id = %s, job_status_id = 4 WHERE "
               "job_id = %s".format(self._table))
        conn_handler.execute(sql, (logid, self._id))

    def add_results(self, results):
        """Adds a list of results to the results

        Parameters
        ----------
        results : list of tuples
            filepath information to add to job, in format
            [(filepath, type_id), ...]
            Where type_id is the filepath type id of the filepath passed

        Notes
        -----
        If your results are a folder of files, pass the base folder as the
        filepath and the type_id as 7 (tar). This function will automatically
        tar the folder before adding it.

        Reference
        ---------
        [1] http://stackoverflow.com/questions/2032403/
            how-to-create-full-compressed-tar-file-using-python
        """
        # go though the list and tar any folders if necessary
        cleanup = []
        addpaths = []
        for fp, fp_type in results:
            if fp_type == 7:
                outpath = join("/tmp", ''.join((basename(fp), ".tar")))
                with taropen(outpath, "w") as tar:
                    tar.add(fp)
                addpaths.append((outpath, 7))
                cleanup.append(outpath)
            else:
                addpaths.append((fp, fp_type))

        # add filepaths to the job
        conn_handler = SQLConnectionHandler()
        file_ids = insert_filepaths(addpaths, self._id, self._table,
                                    "filepath", conn_handler)

        # associate filepaths with job
        sql = ("INSERT INTO qiita.{0}_results_filepath (job_id, filepath_id) "
               "VALUES (%s, %s)".format(self._table))
        conn_handler.executemany(sql, [(self._id, fid) for fid in file_ids])

        # clean up the created tars from the temp directory
        map(remove, cleanup)
