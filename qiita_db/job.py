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
from os.path import join
from time import strftime
from datetime import date
from functools import partial

from qiita_core.exceptions import IncompetentQiitaDeveloperError

from .base import QiitaStatusObject
from .util import insert_filepaths, convert_to_id, get_db_files_base_dir
from .sql_connection import SQLConnectionHandler
from .logger import LogEntry
from .exceptions import QiitaDBStatusError


class Job(QiitaStatusObject):
    """
    Job object to access to the Qiita Job information

    Attributes
    ----------
    datatype
    command
    options
    results
    error

    Methods
    -------
    set_error
    add_results
    """
    _table = "job"

    def _lock_job(self, conn_handler):
        """Raises QiitaDBStatusError if study is public"""
        if self.check_status(("completed", "error")):
            raise QiitaDBStatusError("Can't change status of finished job!")

    def _status_setter_checks(self, conn_handler):
        r"""Perform a check to make sure not setting status away from completed
        or errored
        """
        self._lock_job(conn_handler)

    @staticmethod
    def get_commands():
        """returns commands available with the options as well

        Returns
        -------
        list of command objects
        """
        return Command.create_list()

    @classmethod
    def exists(cls, datatype, command, options):
        """Checks if the given job already exists

        Parameters
        ----------
        datatype : str
            Datatype the job is operating on
        command : str
            The name of the command run on the data
        options : dict
            Options for the command in the format {option: value}

        Returns
        -------
        bool
            Whether the job exists or not
        """
        conn_handler = SQLConnectionHandler()
        datatype_id = convert_to_id(datatype, "data_type", conn_handler)
        sql = "SELECT command_id FROM qiita.command WHERE name = %s"
        command_id = conn_handler.execute_fetchone(sql, (command, ))[0]
        opts_json = dumps(options, sort_keys=True, separators=(',', ':'))
        sql = ("SELECT EXISTS(SELECT * FROM  qiita.{0} WHERE data_type_id = %s"
               " AND command_id = %s AND options = %s)".format(cls._table))
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
        # EXISTS IGNORED FOR DEMO, ISSUE #83
        # if cls.exists(datatype, command, options):
        #     raise QiitaDBDuplicateError(
        #         "Job", "datatype: %s, command: %s, options: %s"
        #         % (datatype, command, options))

        # Get the datatype and command ids from the strings
        conn_handler = SQLConnectionHandler()
        datatype_id = convert_to_id(datatype, "data_type", conn_handler)
        sql = "SELECT command_id FROM qiita.command WHERE name = %s"
        command_id = conn_handler.execute_fetchone(sql, (command, ))[0]

        # JSON the options dictionary
        opts_json = dumps(options, sort_keys=True, separators=(',', ':'))
        # Create the job and return it
        sql = ("INSERT INTO qiita.{0} (data_type_id, job_status_id, "
               "command_id, options) VALUES "
               "(%s, %s, %s, %s) RETURNING job_id").format(cls._table)
        job_id = conn_handler.execute_fetchone(sql, (datatype_id, 1,
                                               command_id, opts_json))[0]

        # add job to analysis
        sql = ("INSERT INTO qiita.analysis_job (analysis_id, job_id) VALUES "
               "(%s, %s)")
        conn_handler.execute(sql, (analysis.id, job_id))

        return cls(job_id)

    @property
    def datatype(self):
        sql = ("SELECT data_type from qiita.data_type WHERE data_type_id = "
               "(SELECT data_type_id from qiita.{0} WHERE "
               "job_id = %s)".format(self._table))
        conn_handler = SQLConnectionHandler()
        return conn_handler.execute_fetchone(sql, (self._id, ))[0]

    @property
    def command(self):
        """Returns the command of the job as (name, command)

        Returns
        -------
        str
            command run by the job
        """
        sql = ("SELECT name, command from qiita.command WHERE command_id = "
               "(SELECT command_id from qiita.{0} WHERE "
               "job_id = %s)".format(self._table))
        conn_handler = SQLConnectionHandler()
        return conn_handler.execute_fetchone(sql, (self._id, ))

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
        try:
            opts = loads(conn_handler.execute_fetchone(sql, (self._id, ))[0])
        except ValueError:
            raise IncompetentQiitaDeveloperError("Malformed options for job "
                                                 "id %d" % self._id)
        sql = ("SELECT command, output from qiita.command WHERE command_id = ("
               "SELECT command_id from qiita.{0} WHERE "
               "job_id = %s)".format(self._table))
        db_comm = conn_handler.execute_fetchone(sql, (self._id, ))
        out_opt = loads(db_comm[1])
        basedir = get_db_files_base_dir(conn_handler)
        join_f = partial(join, join(basedir, "job"))
        for k in out_opt:
            opts[k] = join_f("%s_%s_%s" % (self._id, db_comm[0], k.strip("-")))
        return opts

    @property
    def results(self):
        """List of job result filepaths

        Returns
        -------
        list
            Filepaths to the result files
        """
        # Copy files to working dir, untar if necessary, then return filepaths
        conn_handler = SQLConnectionHandler()
        results = conn_handler.execute_fetchall(
            "SELECT filepath FROM qiita.filepath WHERE filepath_id IN "
            "(SELECT filepath_id FROM qiita.job_results_filepath "
            "WHERE job_id = %s)",
            (self._id, ))
        # create new list, with relative paths from db base
        return [join("job", fp[0]) for fp in results]

    @property
    def error(self):
        """String with an error message, if the job failed

        Returns
        -------
        str or None
            error message/traceback for a job, or None if none exists
        """
        conn_handler = SQLConnectionHandler()
        sql = ("SELECT log_id FROM qiita.{0} "
               "WHERE job_id = %s".format(self._table))
        logging_id = conn_handler.execute_fetchone(sql, (self._id, ))[0]
        if logging_id is None:
            ret = None
        else:
            ret = LogEntry(logging_id)

        return ret

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
        conn_handler = SQLConnectionHandler()
        log_entry = LogEntry.create(severity, msg)
        self._lock_job(conn_handler)

        # attach the error to the job and set to error
        sql = ("UPDATE qiita.{0} SET log_id = %s, job_status_id = 4 WHERE "
               "job_id = %s".format(self._table))

        conn_handler.execute(sql, (log_entry.id, self._id))

    def add_results(self, results):
        """Adds a list of results to the results

        Parameters
        ----------
        results : list of tuples
            filepath information to add to job, in format
            [(filepath, type), ...]
            Where type is the filepath type of the filepath passed

        Notes
        -----
        Curently available file types are:
        biom, directory, plain_text
        """
        # add filepaths to the job
        conn_handler = SQLConnectionHandler()
        self._lock_job(conn_handler)
        # convert all file type text to file type ids
        res_ids = [(fp, convert_to_id(fptype, "filepath_type", conn_handler))
                   for fp, fptype in results]
        file_ids = insert_filepaths(res_ids, self._id, self._table,
                                    "filepath", conn_handler, move_files=False)

        # associate filepaths with job
        sql = ("INSERT INTO qiita.{0}_results_filepath (job_id, filepath_id) "
               "VALUES (%s, %s)".format(self._table))
        conn_handler.executemany(sql, [(self._id, fid) for fid in file_ids])


class Command(object):
    """Holds all information on the commands available

    This will be an in-memory representation because the command table is
    considerably more static than other objects tables, changing only with new
    QIIME releases.

    Attributes
    ----------
    name
    command
    input_opts
    required_opts
    optional_opts
    output_opts
    """
    @classmethod
    def create_list(cls):
        """Creates list of all available commands

        Returns
        -------
        list of Command objects
        """
        conn_handler = SQLConnectionHandler()
        commands = conn_handler.execute_fetchall("SELECT * FROM qiita.command")
        # create the list of command objects
        return [cls(c["name"], c["command"], c["input"], c["required"],
                c["optional"], c["output"]) for c in commands]

    def __eq__(self, other):
        if type(self) != type(other):
            return False
        if self.name != other.name:
            return False
        if self.command != other.command:
            return False
        if self.input_opts != other.input_opts:
            return False
        if self.output_opts != other.output_opts:
            return False
        if self.required_opts != other.required_opts:
            return False
        if self.optional_opts != other.optional_opts:
            return False
        return True

    def __ne__(self, other):
        return not self.__eq__(other)

    def __init__(self, name, command, input_opts, required_opts,
                 optional_opts, output_opts):
        """Creates the command object

        Parameters:
        name : str
            Name of the command
        command: str
            python command to run
        input_opts : str
            JSON of input options for the command
        required_opts : str
            JSON of required options for the command
        optional_opts : str
            JSON of optional options for the command
        output_opts : str
            JSON of output options for the command
        """
        self.name = name
        self.command = command
        self.input_opts = dumps(input_opts)
        self.required_opts = dumps(required_opts)
        self.optional_opts = dumps(optional_opts)
        self.output_opts = dumps(output_opts)
