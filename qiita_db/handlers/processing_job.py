# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from json import loads

from tornado.web import HTTPError

import qiita_db as qdb
from .oauth2 import OauthBaseHandler, authenticate_oauth


def _get_job(job_id):
    """Returns the job with the given id if it exists

    Parameters
    ----------
    job_id : str
        The job id to check

    Returns
    -------
    qiita_db.processing_job.ProcessingJob
        The requested job

    Raises
    ------
    HTTPError
        If the job does not exist, with error code 404
        If there is a problem instantiating the processing job, with error
        code 500
    """
    if not qdb.processing_job.ProcessingJob.exists(job_id):
        raise HTTPError(404)

    try:
        job = qdb.processing_job.ProcessingJob(job_id)
    except Exception as e:
        raise HTTPError(500, 'Error instantiating the job: %s' % str(e))

    return job


class JobHandler(OauthBaseHandler):
    @authenticate_oauth
    def get(self, job_id):
        """Get the job information

        Parameters
        ----------
        job_id : str
            The job id

        Returns
        -------
        dict
            {'command': str,
             'parameters': dict of {str, obj},
             'status': str}
             - command: the name of the command that the job executes
             - parameters: the parameters of the command, keyed by parameter
             name
             - status: the status of the job
        """
        with qdb.sql_connection.TRN:
            job = _get_job(job_id)
            cmd = job.command.name
            params = job.parameters.values
            status = job.status

        response = {'command': cmd, 'parameters': params,
                    'status': status}
        self.write(response)


class HeartbeatHandler(OauthBaseHandler):
    @authenticate_oauth
    def post(self, job_id):
        """Update the heartbeat timestamp of the job

        Parameters
        ----------
        job_id : str
            The job id
        """
        with qdb.sql_connection.TRN:
            job = _get_job(job_id)

            try:
                job.update_heartbeat_state()
            except qdb.exceptions.QiitaDBOperationNotPermittedError as e:
                raise HTTPError(403, str(e))

        self.finish()


class ActiveStepHandler(OauthBaseHandler):
    @authenticate_oauth
    def post(self, job_id):
        """Changes the current exectuion step of the given job

        Parameters
        ----------
        job_id : str
            The job id
        """
        with qdb.sql_connection.TRN:
            job = _get_job(job_id)
            payload = loads(self.request.body)
            step = payload['step']
            try:
                job.step = step
            except qdb.exceptions.QiitaDBOperationNotPermittedError as e:
                raise HTTPError(403, str(e))

        self.finish()


class CompleteHandler(OauthBaseHandler):
    @authenticate_oauth
    def post(self, job_id):
        """Updates the job to one of the completed statuses: 'success', 'error'

        Parameters
        ----------
        job_id : str
            The job to complete
        """
        with qdb.sql_connection.TRN:
            job = _get_job(job_id)

            if job.status != 'running':
                raise HTTPError(
                    403, "Can't complete job: not in a running state")

            qiita_plugin = qdb.software.Software.from_name_and_version(
                'Qiita', 'alpha')
            cmd = qiita_plugin.get_command('complete_job')
            params = qdb.software.Parameters.load(
                cmd, values_dict={'job_id': job_id,
                                  'payload': self.request.body})
            job = qdb.processing_job.ProcessingJob.create(job.user, params)
            job.submit()

        self.finish()


class ProcessingJobAPItestHandler(OauthBaseHandler):
    @authenticate_oauth
    def post(self):
        user = self.get_argument('user', 'test@foo.bar')
        s_name, s_version, cmd_name = loads(self.get_argument('command'))
        params_dict = self.get_argument('parameters')
        status = self.get_argument('status', None)

        cmd = qdb.software.Software.from_name_and_version(
            s_name, s_version).get_command(cmd_name)

        params = qdb.software.Parameters.load(cmd, json_str=params_dict)

        job = qdb.processing_job.ProcessingJob.create(
            qdb.user.User(user), params)

        if status:
            job._set_status(status)

        self.write({'job': job.id})
