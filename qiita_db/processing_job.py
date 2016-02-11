# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from uuid import UUID
from datetime import datetime

from future.utils import viewitems

import qiita_db as qdb


class ProcessingJob(qdb.base.QiitaObject):
    r"""Models a job that executes a command in a set of artifacts

    Attributes
    ----------
    user
    command
    parameters
    status
    log
    heartbeat
    step

    Methods
    -------
    exists
    create
    """
    _table = 'processing_job'

    @classmethod
    def exists(cls, job_id):
        """Check if the job `job_id` exists

        Parameters
        ----------
        job_id : str
            The job id

        Returns
        -------
        bool
            True if the job `job_id` exists. False otherwise.
        """
        try:
            UUID(job_id)
        except ValueError:
            return False

        with qdb.sql_connection.TRN:
            sql = """SELECT EXISTS(SELECT *
                                   FROM qiita.processing_job
                                   WHERE processing_job_id = %s)"""
            qdb.sql_connection.TRN.add(sql, [job_id])
            return qdb.sql_connection.TRN.execute_fetchlast()

    @classmethod
    def create(cls, user, parameters):
        """Creates a new job in the system

        Parameters
        ----------
        user : qiita_db.user.User
            The user executing the job
        parameters : qiita_db.software.Parameters
            The parameters of the job being executed

        Returns
        -------
        qiita_db.processing_job.ProcessingJob
            The newly created job
        """
        with qdb.sql_connection.TRN:
            command = parameters.command
            sql = """INSERT INTO qiita.processing_job
                        (email, command_id, command_parameters,
                         processing_job_status_id)
                     VALUES (%s, %s, %s, %s)
                     RETURNING processing_job_id"""
            status = qdb.util.convert_to_id("queued", "processing_job_status")
            sql_args = [user.id, command.id,
                        parameters.dump(), status]
            qdb.sql_connection.TRN.add(sql, sql_args)
            job_id = qdb.sql_connection.TRN.execute_fetchlast()

            # Link the job with the input artifacts
            sql = """INSERT INTO qiita.artifact_processing_job
                        (artifact_id, processing_job_id)
                     VALUES (%s, %s)"""
            for pname, vals in command.parameters.items():
                if vals[0] == 'artifact':
                    qdb.sql_connection.TRN.add(
                        sql, [parameters.values[pname], job_id])
            qdb.sql_connection.TRN.execute()

            return cls(job_id)

    @property
    def user(self):
        """The user that launched the job

        Returns
        -------
        qiita_db.user.User
            The user that launched the job
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT email
                     FROM qiita.processing_job
                     WHERE processing_job_id = %s"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            email = qdb.sql_connection.TRN.execute_fetchlast()
            return qdb.user.User(email)

    @property
    def command(self):
        """The command that the job executes

        Returns
        -------
        qiita_db.software.Command
            The command that the job executes
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT command_id
                     FROM qiita.processing_job
                     WHERE processing_job_id = %s"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            cmd_id = qdb.sql_connection.TRN.execute_fetchlast()
            return qdb.software.Command(cmd_id)

    @property
    def parameters(self):
        """The parameters used in the job's command

        Returns
        -------
        qiita_db.software.Parameters
            The parameters used in the job's command
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT command_id, command_parameters
                     FROM qiita.processing_job
                     WHERE processing_job_id = %s"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            res = qdb.sql_connection.TRN.execute_fetchindex()[0]
            return qdb.software.Parameters.load(
                qdb.software.Command(res[0]), values_dict=res[1])

    @property
    def input_artifacts(self):
        """The artifacts used as input in the job

        Returns
        -------
        list of qiita_db.artifact.Artifact
            The artifacs used as input in the job
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT artifact_id
                     FROM qiita.artifact_processing_job
                     WHERE processing_job_id = %s
                     ORDER BY artifact_id"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            return [qdb.artifact.Artifact(aid)
                    for aid in qdb.sql_connection.TRN.execute_fetchflatten()]

    @property
    def status(self):
        """The status of the job

        Returns
        -------
        {'queued', 'running', 'success', 'error'}
            The current status of the job
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT processing_job_status
                     FROM qiita.processing_job_status
                        JOIN qiita.processing_job
                            USING (processing_job_status_id)
                     WHERE processing_job_id = %s"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            return qdb.sql_connection.TRN.execute_fetchlast()

    def _set_status(self, value):
        """Sets the status of the job

        Parameters
        ----------
        value : str, {'queued', 'running', 'success', 'error'}
            The new status of the job

        Raises
        ------
        qiita_db.exceptions.QiitaDBStatusError
            - If the current status of the job is 'success'
            - If the current status of the job is 'running' and `value` is
            'queued'
        """
        with qdb.sql_connection.TRN:
            current_status = self.status
            if current_status == 'success':
                raise qdb.exceptions.QiitaDBStatusError(
                    "Cannot change the status of a 'success' job")
            elif current_status == 'running' and value == 'queued':
                raise qdb.exceptions.QiitaDBStatusError(
                    "Cannot revert the status of a 'running' job to 'queued'")

            new_status = qdb.util.convert_to_id(
                value, "processing_job_status")
            sql = """UPDATE qiita.processing_job
                     SET processing_job_status_id = %s
                     WHERE processing_job_id = %s"""
            qdb.sql_connection.TRN.add(sql, [new_status, self.id])
            qdb.sql_connection.TRN.execute()

    def complete(self, success, artifacts_data=None, error=None):
        """Completes the job, either with a success or error status

        Parameters
        ----------
        success : bool
            Whether the job has completed successfully or not
        artifacts_data : dict of dicts
            The generated artifact information, keyed by output name.
            The format of each of the internal dictionaries must be
            {'filepaths': list of (str, str), 'artifact_type': str}
            where `filepaths` contains the list of filepaths and filepath types
            for the artifact and `artifact_type` the type of the artifact
        error : str, optional
            If the job was not successful, the error message

        Raises
        ------
        qiita_db.exceptions.QiitaDBOperationNotPermittedError
            If the job is not in running state
        """
        with qdb.sql_connection.TRN:
            if self.status != 'running':
                raise qdb.exceptions.QiitaDBOperationNotPermittedError(
                    "Can't complete job: not in a running state")
            if success:
                if artifacts_data:
                    artifact_ids = []
                    for out_name, a_data in viewitems(artifacts_data):
                        filepaths = a_data['filepaths']
                        atype = a_data['artifact_type']
                        parents = self.input_artifacts
                        params = self.parameters
                        a = qdb.artifact.Artifact.create(
                            filepaths, atype, parents=parents,
                            processing_parameters=params)
                        cmd_out_id = qdb.util.convert_to_id(
                            out_name, "command_output", "name")
                        artifact_ids.append((cmd_out_id, a.id))
                    if artifact_ids:
                        sql = """INSERT INTO
                                    qiita.artifact_output_processing_job
                                    (artifact_id, processing_job_id,
                                     command_output_id)
                                 VALUES (%s, %s, %s)"""
                        sql_params = [[aid, self.id, out_id]
                                      for out_id, aid in artifact_ids]
                        qdb.sql_connection.TRN.add(sql, sql_params, many=True)
                self._set_status('success')
            else:
                log = qdb.logger.LogEntry.create('Runtime', error)
                self._set_status('error')
                self._set_log(log)

    @property
    def log(self):
        """The log entry attached to the job if it failed

        Returns
        -------
        qiita_db.logger.LogEntry or None
            If the status of the job is `error`, returns the LogEntry attached
            to the job
        """
        with qdb.sql_connection.TRN:
            res = None
            if self.status == 'error':
                sql = """SELECT logging_id
                         FROM qiita.processing_job
                         WHERE processing_job_id = %s"""
                qdb.sql_connection.TRN.add(sql, [self.id])
                log_id = qdb.sql_connection.TRN.execute_fetchlast()
                res = qdb.logger.LogEntry(log_id)
        return res

    def _set_log(self, value):
        """Attaches a log entry to the job

        Parameters
        ----------
        value : qiita_db.logger.LogEntry
            The log entry to attach to the job

        Raises
        ------
        qiita_db.exceptions.QiitaDBOperationNotPermittedError
            If the status of the job is not 'error'
        """
        with qdb.sql_connection.TRN:
            if self.status != 'error':
                raise qdb.exceptions.QiitaDBOperationNotPermittedError(
                    "Can only set up the log for jobs whose status is 'error'")

            sql = """UPDATE qiita.processing_job
                     SET logging_id = %s
                     WHERE processing_job_id = %s"""
            qdb.sql_connection.TRN.add(sql, [value.id, self.id])
            qdb.sql_connection.TRN.execute()

    @property
    def heartbeat(self):
        """The timestamp of the last heartbeat received from the job

        Returns
        -------
        datetime
            The last heartbeat timestamp
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT heartbeat
                     FROM qiita.processing_job
                     WHERE processing_job_id = %s"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            return qdb.sql_connection.TRN.execute_fetchlast()

    def execute_heartbeat(self):
        """Updates the heartbeat of the job

        In case that the job is in `queued` status, it changes the status to
        `running`.

        Raises
        ------
        QiitaDBOperationNotPermittedError
            If the job is already completed
        """
        with qdb.sql_connection.TRN:
            status = self.status
            if status == 'queued':
                self._set_status('running')
            elif status != 'running':
                raise qdb.exceptions.QiitaDBOperationNotPermittedError(
                    "Can't execute heartbeat on job: already completed")
            sql = """UPDATE qiita.processing_job
                     SET heartbeat = %s
                     WHERE processing_job_id = %s"""
            qdb.sql_connection.TRN.add(sql, [datetime.now(), self.id])
            qdb.sql_connection.TRN.execute()

    @property
    def step(self):
        """Returns the current step of the job

        Returns
        -------
        str
            The current step of the job
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT step
                     FROM qiita.processing_job
                     WHERE processing_job_id = %s"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            return qdb.sql_connection.TRN.execute_fetchlast()

    @step.setter
    def step(self, value):
        """Sets the current step of the job

        Parameters
        ----------
        value : str
            The new current step of the job

        Raises
        ------
        qiita_db.exceptions.QiitaDBOperationNotPermittedError
            If the status of the job is not 'running'
        """
        with qdb.sql_connection.TRN:
            if self.status != 'running':
                raise qdb.exceptions.QiitaDBOperationNotPermittedError(
                    "Cannot change the step of a job whose status is not "
                    "'running'")
            sql = """UPDATE qiita.processing_job
                     SET step = %s
                     WHERE processing_job_id = %s"""
            qdb.sql_connection.TRN.add(sql, [value, self.id])
            qdb.sql_connection.TRN.execute()
