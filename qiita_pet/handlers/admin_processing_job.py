# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from tornado.gen import coroutine
from tornado.web import HTTPError

from .base_handlers import BaseHandler
from qiita_core.util import execute_as_transaction

from qiita_db.software import Software

from json import dumps


class AdminProcessingJobBaseClass(BaseHandler):
    def _check_access(self):
        if self.current_user.level not in {'admin', 'wet-lab admin'}:
            raise HTTPError(403, reason="User %s doesn't have sufficient "
                            "privileges to view error page" %
                            self.current_user.email)

        return self

    def _get_private_software(self):
        # skipping the internal Qiita plugin and only selecting private
        # commands
        private_software = [s for s in Software.iter()
                            if s.name != 'Qiita' and s.type == 'private']

        return private_software


class AdminProcessingJob(AdminProcessingJobBaseClass):
    @coroutine
    @execute_as_transaction
    def get(self):
        self._check_access()

        self.render("admin_processing_job.html",
                    private_software=self._get_private_software())


class AJAXAdminProcessingJobListing(AdminProcessingJobBaseClass):
    @coroutine
    @execute_as_transaction
    def get(self):
        self._check_access()
        echo = self.get_argument('sEcho')
        command_id = int(self.get_argument('commandId'))

        jobs = []
        for ps in self._get_private_software():
            for cmd in ps.commands:
                if cmd.id != command_id:
                    continue

                for job in cmd.processing_jobs:
                    if job.hidden:
                        continue
                    msg = ''
                    if job.status == 'error':
                        msg = job.log.msg
                    elif job.status == 'running':
                        msg = job.step
                    msg = msg.replace('\n', '</br>')
                    outputs = []
                    if job.status == 'success':
                        outputs = [[k, v.id] for k, v in job.outputs.items()]
                    validator_jobs = [v.id for v in job.validator_jobs]

                    if job.heartbeat is not None:
                        heartbeat = job.heartbeat.strftime('%Y-%m-%d %H:%M:%S')
                    else:
                        heartbeat = 'N/A'

                    jobs.append([job.id, job.command.name, job.status, msg,
                                 outputs, validator_jobs, heartbeat,
                                 job.parameters.values])
        results = {
            "sEcho": echo,
            "recordsTotal": len(jobs),
            "recordsFiltered": len(jobs),
            "data": jobs
        }

        # return the json in compact form to save transmit size
        self.write(dumps(results, separators=(',', ':')))
