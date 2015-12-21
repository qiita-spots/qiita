# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from __future__ import division

from tornado.web import authenticated

from qiita_pet.handlers.util import to_int
from qiita_pet.handlers.base_handlers import BaseHandler
from qiita_pet.handlers.api_proxy import prep_graph_proxy


class PrepTemplateGraphAJAX(BaseHandler):
    @authenticated
    def get(self):
        prep = to_int(self.get_argument('prep_id'))
        self.write(prep_graph_proxy(prep, self.current_user.id))
