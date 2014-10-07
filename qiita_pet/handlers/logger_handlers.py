from __future__ import division

from tornado.web import authenticated

from .base_handlers import BaseHandler
from qiita_db.logger import LogEntry


class LogEntryViewerHandler(BaseHandler):
    @authenticated
    def get(self):
        logentries = LogEntry.newest_records()
        self.render("error_log.html", logentries=logentries,
                    user=self.current_user)

    @authenticated
    def post(self):
        numentries = int(self.get_argument("numrecords"))
        if numentries < 0:
            numentries = 100
        logentries = LogEntry.newest_records(numentries)
        self.render("error_log.html", logentries=logentries,
                    user=self.current_user)
