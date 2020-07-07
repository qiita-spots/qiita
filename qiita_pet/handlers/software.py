# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from tornado.gen import coroutine

from qiita_core.util import execute_as_transaction
from qiita_db.software import Software
from .base_handlers import BaseHandler


class SoftwareHandler(BaseHandler):
    @coroutine
    @execute_as_transaction
    def get(self):
        # active True will only show active software
        active = True
        user = self.current_user
        if user is not None and user.level in {'admin', 'dev'}:
            active = False

        software = Software.iter(active=active)
        self.render("software.html", software=software)
