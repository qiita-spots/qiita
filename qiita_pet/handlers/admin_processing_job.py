# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from tornado.gen import coroutine

from .base_handlers import BaseHandler
from qiita_core.util import execute_as_transaction

from qiita_db.software import Software


class AdminProcessingJob(BaseHandler):
    @coroutine
    @execute_as_transaction
    def get(self):
        # skipping the internal Qiita plugin and only selecting private
        # commands
        private_software = [s for s in Software.iter()
                            if s.name != 'Qiita' and s.type == 'private']
        jobs = []
        for ps in private_software:
            for cmd in ps.commands:
                for job in cmd.processing_jobs:
                    jobs.append(job)

        self.render("admin_processing_job.html", jobs=jobs,
                    private_software=private_software)
