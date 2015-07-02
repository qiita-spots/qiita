r"""
Data objects (:mod: `qiita_db.data`)
====================================

..currentmodule:: qiita_db.data

This module provides functionality for creating, running, and storing results
of jobs in an analysis. It also provides the ability to query what commmands
are available for jobs, as well as the options for these commands.

Classes
-------

..autosummary::
    :toctree: generated/

    Job
    Command
"""
# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from __future__ import division
from json import loads
from os.path import join, relpath
from os import remove
from glob import glob
from shutil import rmtree
from functools import partial
from collections import defaultdict

from .base import QiitaStatusObject
from .util import (insert_filepaths, convert_to_id, get_db_files_base_dir,
                   params_dict_to_json, get_mountpoint)
from .sql_connection import SQLConnectionHandler
from .logger import LogEntry
from .exceptions import QiitaDBStatusError, QiitaDBDuplicateError


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

    def _lock_job(self):
        """Raises QiitaDBStatusError if study is public"""
        if self.check_status(("completed", "error")):
            raise QiitaDBStatusError("Can't change status of finished job!")

    def _status_setter_checks(self):
        r"""Perform a check to make sure not setting status away from completed
        or errored
        """
        self._lock_job()

    @staticmethod
    def get_commands():
        """returns commands available with the options as well

        Returns
        -------
        list of command objects
        """
        return Command.create_list()

    @classmethod
    def exists(cls, datatype, command, options, analysis,
               return_existing=False):
        """Checks if the given job already exists

        Parameters
        ----------
        datatype : str
            Datatype the job is operating on
        command : str
            The name of the command run on the data
        options : dict
            Options for the command in the format {option: value}
        analysis : Analysis object
            The analysis the job will be attached to on creation
        return_existing : bool, optional
            If True, function will return the instatiated Job object for the
            matching job. Default False

        Returns
        -------
        bool
            Whether the job exists or not
        Job or None, optional
            If return_existing is True, the Job object of the matching job or
            None if none exists
        """
        conn_handler = SQLConnectionHandler()
        # check passed arguments and grab analyses for matching jobs
        datatype_id = convert_to_id(datatype, "data_type")
        sql = "SELECT command_id FROM qiita.command WHERE name = %s"
        command_id = conn_handler.execute_fetchone(sql, (command, ))[0]
        opts_json = params_dict_to_json(options)
        sql = ("SELECT DISTINCT aj.analysis_id, aj.job_id FROM "
               "qiita.analysis_job aj JOIN qiita.{0} j ON aj.job_id = j.job_id"
               " WHERE j.data_type_id = %s AND j.command_id = %s "
               "AND j.options = %s".format(cls._table))
        analyses = conn_handler.execute_fetchall(
            sql, (datatype_id, command_id, opts_json))
        if not analyses and return_existing:
            # stop looking since we have no possible matches
            return False, None
        elif not analyses:
            return False

        # build the samples dict as list of samples keyed to their proc_data_id
        sql = ("SELECT processed_data_id, array_agg(sample_id ORDER BY "
               "sample_id) FROM qiita.analysis_sample WHERE analysis_id = %s "
               "GROUP BY processed_data_id")
        samples = dict(conn_handler.execute_fetchall(sql, [analysis.id]))
        # check passed analyses' samples dict against all found analyses
        matched_job = None
        for aid, jid in analyses:
            # build the samples dict for a found analysis
            comp_samples = dict(conn_handler.execute_fetchall(sql, [aid]))
            # compare samples and stop checking if a match is found
            matched_samples = True if samples == comp_samples else False
            if matched_samples:
                matched_job = jid
                break

        if return_existing:
            return matched_samples, (cls(matched_job) if matched_job else None)
        return matched_samples

    @classmethod
    def delete(cls, jobid):
        """Removes a job and all files attached to it

        Parameters
        ----------
        jobid : int
            ID of the job to delete

        Notes
        -----
        This function will remove a job from all analyses it is attached to in
        analysis_job table, as well as the job itself from the job table. All
        files and references to files for the job will be removed from the
        filepath and job_results_filepath tables. All the job's files on the
        filesystem will also be removed.
        """
        conn_handler = SQLConnectionHandler()
        # store filepath info for later use
        sql = ("SELECT f.filepath, f.filepath_id FROM qiita.filepath f JOIN "
               "qiita.job_results_filepath jf ON jf.filepath_id = "
               "f.filepath_id WHERE jf.job_id = %s")
        filepaths = conn_handler.execute_fetchall(sql, [jobid])

        # remove fiepath links in DB
        conn_handler.execute("DELETE FROM qiita.job_results_filepath WHERE "
                             "job_id = %s", [jobid])
        sql = "DELETE FROM qiita.filepath WHERE"
        for x in range(len(filepaths)):
            sql = ' '.join((sql, "filepath_id = %s"))
        conn_handler.execute(sql, [fp[1] for fp in filepaths])

        # remove job
        conn_handler.execute("DELETE FROM qiita.analysis_job WHERE "
                             "job_id = %s", [jobid])
        conn_handler.execute("DELETE FROM qiita.collection_job WHERE "
                             "job_id = %s", [jobid])
        conn_handler.execute("DELETE FROM qiita.job WHERE job_id = %s",
                             [jobid])

        # remove files/folders attached to job
        _, basedir = get_mountpoint("job")[0]
        for fp in filepaths:
            try:
                rmtree(join(basedir, fp[0]))
            except OSError:
                remove(join(basedir, fp[0]))

    @classmethod
    def create(cls, datatype, command, options, analysis,
               return_existing=False):
        """Creates a new job on the database

        Parameters
        ----------
        datatype : str
            The datatype in which this job applies
        command : str
            The name of the command executed in this job
        analysis : Analysis object
            The analysis which this job belongs to
        return_existing : bool, optional
            If True, returns an instantiated Job object pointing to an already
            existing job with the given parameters. Default False

        Returns
        -------
        Job object
            The newly created job

        Raises
        ------
        QiitaDBDuplicateError
            return_existing is False and an exact duplicate of the job already
            exists in the DB.
        """
        analysis_sql = ("INSERT INTO qiita.analysis_job (analysis_id, job_id) "
                        "VALUES (%s, %s)")
        exists, job = cls.exists(datatype, command, options, analysis,
                                 return_existing=True)
        conn_handler = SQLConnectionHandler()
        if exists:
            if return_existing:
                # add job to analysis
                conn_handler.execute(analysis_sql, (analysis.id, job.id))
                return job
            else:
                raise QiitaDBDuplicateError(
                    "Job", "datatype: %s, command: %s, options: %s, "
                    "analysis: %s" % (datatype, command, options, analysis.id))

        # Get the datatype and command ids from the strings
        datatype_id = convert_to_id(datatype, "data_type")
        sql = "SELECT command_id FROM qiita.command WHERE name = %s"
        command_id = conn_handler.execute_fetchone(sql, (command, ))[0]
        opts_json = params_dict_to_json(options)

        # Create the job and return it
        sql = ("INSERT INTO qiita.{0} (data_type_id, job_status_id, "
               "command_id, options) VALUES "
               "(%s, %s, %s, %s) RETURNING job_id").format(cls._table)
        job_id = conn_handler.execute_fetchone(sql, (datatype_id, 1,
                                               command_id, opts_json))[0]

        # add job to analysis
        conn_handler.execute(analysis_sql, (analysis.id, job_id))

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
        db_opts = conn_handler.execute_fetchone(sql, (self._id, ))[0]
        opts = loads(db_opts) if db_opts else {}
        sql = ("SELECT command, output from qiita.command WHERE command_id = ("
               "SELECT command_id from qiita.{0} WHERE "
               "job_id = %s)".format(self._table))
        db_comm = conn_handler.execute_fetchone(sql, (self._id, ))
        out_opt = loads(db_comm[1])
        basedir = get_db_files_base_dir()
        join_f = partial(join, join(basedir, "job"))
        for k in out_opt:
            opts[k] = join_f("%s_%s_%s" % (self._id, db_comm[0], k.strip("-")))
        return opts

    @options.setter
    def options(self, opts):
        """ Sets the options for the job

        Parameters
        ----------
        opts: dict
            The options for the command in format {option: value}
        """
        conn_handler = SQLConnectionHandler()
        # make sure job is editable
        self._lock_job()

        # JSON the options dictionary
        opts_json = params_dict_to_json(opts)
        # Add the options to the job
        sql = ("UPDATE qiita.{0} SET options = %s WHERE "
               "job_id = %s").format(self._table)
        conn_handler.execute(sql, (opts_json, self._id))

    @property
    def results(self):
        """List of job result filepaths

        Returns
        -------
        list
            Filepaths to the result files
        """
        # Select results filepaths and filepath types from the database
        conn_handler = SQLConnectionHandler()
        _, basedir = get_mountpoint('job')[0]
        results = conn_handler.execute_fetchall(
            "SELECT fp.filepath, fpt.filepath_type FROM qiita.filepath fp "
            "JOIN qiita.filepath_type fpt ON fp.filepath_type_id = "
            "fpt.filepath_type_id JOIN qiita.job_results_filepath jrfp ON "
            "fp.filepath_id = jrfp.filepath_id WHERE jrfp.job_id = %s",
            (self._id, ))

        def add_html(basedir, check_dir, result_fps):
            for res in glob(join(basedir, check_dir, "*.htm")) + \
                    glob(join(basedir, check_dir, "*.html")):
                result_fps.append(relpath(res, basedir))

        # create new list, with relative paths from db base
        result_fps = []
        for fp in results:
            if fp[1] == "directory":
                # directory, so all html files in it are results
                # first, see if we have any in the main directory
                add_html(basedir, fp[0], result_fps)
                # now do all subdirectories
                add_html(basedir, join(fp[0], "*"), result_fps)
            else:
                # result is exact filepath given
                result_fps.append(fp[0])
        return result_fps

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
    def set_error(self, msg):
        """Logs an error for the job

        Parameters
        ----------
        msg : str
            Error message/stacktrace if available
        """
        conn_handler = SQLConnectionHandler()
        log_entry = LogEntry.create('Runtime', msg,
                                    info={'job': self._id})
        self._lock_job()
        err_id = conn_handler.execute_fetchone(
            "SELECT job_status_id FROM qiita.job_status WHERE "
            "status = 'error'")[0]
        # attach the error to the job and set to error
        sql = ("UPDATE qiita.{0} SET log_id = %s, job_status_id = %s WHERE "
               "job_id = %s".format(self._table))

        conn_handler.execute(sql, (log_entry.id, err_id, self._id))

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
        self._lock_job()
        # convert all file type text to file type ids
        res_ids = [(fp, convert_to_id(fptype, "filepath_type"))
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

    @classmethod
    def get_commands_by_datatype(cls, datatypes=None):
        """Returns the commands available for all or a subset of the datatypes

        Parameters
        ----------
        datatypes : list of str, optional
            List of the datatypes to get commands for. Default is all datatypes

        Returns
        -------
        dict of lists of Command objects
            Returns commands in the format {datatype: [com name1, com name2]}

        Notes
        -----
        If no datatypes are passed, the function will default to returning all
        datatypes available.
        """
        conn_handler = SQLConnectionHandler()
        # get the ids of the datatypes to get commands for
        if datatypes is not None:
            datatype_info = [(convert_to_id(dt, "data_type"), dt)
                             for dt in datatypes]
        else:
            datatype_info = conn_handler.execute_fetchall(
                "SELECT data_type_id, data_type from qiita.data_type")

        commands = defaultdict(list)
        # get commands for each datatype
        sql = ("SELECT C.* FROM qiita.command C JOIN qiita.command_data_type "
               "CD on C.command_id = CD.command_id WHERE CD.data_type_id = %s")
        for dt_id, dt in datatype_info:
            comms = conn_handler.execute_fetchall(sql, (dt_id, ))
            for comm in comms:
                commands[dt].append(cls(comm["name"], comm["command"],
                                        comm["input"],
                                        comm["required"],
                                        comm["optional"],
                                        comm["output"]))
        return commands

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
        self.input_opts = loads(input_opts)
        self.required_opts = loads(required_opts)
        self.optional_opts = loads(optional_opts)
        self.output_opts = loads(output_opts)
