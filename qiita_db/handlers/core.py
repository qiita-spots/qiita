# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

import qiita_db as qdb

from .oauth2 import OauthBaseHandler, authenticate_oauth


class ResetAPItestHandler(OauthBaseHandler):
    @authenticate_oauth
    def post(self):
        drop_labcontrol = self.get_argument("drop_labcontrol", False)
        qdb.environment_manager.drop_and_rebuild_tst_database(drop_labcontrol)
