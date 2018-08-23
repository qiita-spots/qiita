# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from __future__ import division

from tornado.gen import coroutine
from tornado.web import HTTPError

from qiita_core.util import execute_as_transaction
from qiita_db.software import Software
from .base_handlers import BaseHandler


class SoftwareHandler(BaseHandler):
    def check_access(self):
        if self.current_user.level not in {'admin', 'dev'}:
            raise HTTPError(405, reason="User %s doesn't have sufficient "
                            "privileges to view error page" %
                            self.current_user)

    @coroutine
    @execute_as_transaction
    def get(self):
        self.check_access()
        software = Software.iter(False)
        self.render("software.html", software=software)
