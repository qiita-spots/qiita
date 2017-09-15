# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from json import dumps

from tornado.web import authenticated, HTTPError
from tornado.gen import coroutine, Task

from qiita_core.qiita_settings import qiita_config
from qiita_core.util import execute_as_transaction
from qiita_pet.handlers.base_handlers import BaseHandler
from qiita_pet.handlers.util import get_shared_links
from qiita_db.user import User
from qiita_db.analysis import Analysis
from qiita_db.util import add_message


class ShareAnalysisAJAX(BaseHandler):
    @execute_as_transaction
    def _get_shared_for_study(self, analysis, callback):
        shared_links = get_shared_links(analysis)
        users = [u.email for u in analysis.shared_with]
        callback((users, shared_links))

    @execute_as_transaction
    def _share(self, analysis, user, callback):
        user = User(user)
        add_message('Analysis <a href="%s/analysis/description/%d">\'%s\'</a> '
                    'has been shared with you.' %
                    (qiita_config.portal_dir, analysis.id, analysis.name),
                    [user])
        callback(analysis.share(user))

    @execute_as_transaction
    def _unshare(self, analysis, user, callback):
        user = User(user)
        add_message('Analysis \'%s\' has been unshared with you.' %
                    analysis.name, [user])
        callback(analysis.unshare(user))

    @authenticated
    @coroutine
    @execute_as_transaction
    def get(self):
        analysis_id = int(self.get_argument('id'))
        analysis = Analysis(analysis_id)
        if not analysis.has_access(self.current_user):
            raise HTTPError(403, 'User %s does not have permissions to share '
                            'analysis %s' % (
                                self.current_user.id, analysis.id))

        selected = self.get_argument('selected', None)
        deselected = self.get_argument('deselected', None)

        if selected is not None:
            yield Task(self._share, analysis, selected)
        if deselected is not None:
            yield Task(self._unshare, analysis, deselected)

        users, links = yield Task(self._get_shared_for_study, analysis)

        self.write(dumps({'users': users, 'links': links}))
