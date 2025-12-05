# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from tornado.web import HTTPError, authenticated

from qiita_core.util import execute_as_transaction
from qiita_db.logger import LogEntry

from .base_handlers import BaseHandler


class LogEntryViewerHandler(BaseHandler):
    def check_access(self):
        if self.current_user.level not in {"admin", "dev"}:
            raise HTTPError(
                403,
                reason="User %s doesn't have sufficient "
                "privileges to view error page" % self.current_user.email,
            )

    @authenticated
    @execute_as_transaction
    def get(self):
        self.check_access()
        logentries = LogEntry.newest_records()
        self.render("error_log.html", logentries=logentries)

    @authenticated
    @execute_as_transaction
    def post(self):
        self.check_access()
        numentries = int(self.get_argument("numrecords"))
        if numentries <= 0:
            numentries = 100
        logentries = LogEntry.newest_records(numentries)
        self.render("error_log.html", logentries=logentries)
