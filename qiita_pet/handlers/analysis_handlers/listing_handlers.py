# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from functools import partial

from tornado.web import authenticated

from qiita_core.util import execute_as_transaction
from qiita_pet.handlers.base_handlers import BaseHandler
from qiita_pet.handlers.util import download_link_or_path
from qiita_pet.util import is_localhost
from qiita_db.util import get_filepath_id


class ListAnalysesHandler(BaseHandler):
    @authenticated
    @execute_as_transaction
    def get(self):
        message = self.get_argument('message', '')
        level = self.get_argument('level', '')
        user = self.current_user

        analyses = user.shared_analyses | user.private_analyses

        is_local_request = is_localhost(self.request.headers['host'])
        gfi = partial(get_filepath_id, 'analysis')
        dlop = partial(download_link_or_path, is_local_request)
        mappings = {}
        bioms = {}
        tgzs = {}
        for analysis in analyses:
            _id = analysis.id
            # getting mapping file
            mapping = analysis.mapping_file
            if mapping is not None:
                mappings[_id] = dlop(mapping, gfi(mapping), 'mapping file')
            else:
                mappings[_id] = ''

            bioms[_id] = ''
            # getting tgz file
            tgz = analysis.tgz
            if tgz is not None:
                tgzs[_id] = dlop(tgz, gfi(tgz), 'tgz file')
            else:
                tgzs[_id] = ''

        self.render("list_analyses.html", analyses=analyses, message=message,
                    level=level, is_local_request=is_local_request,
                    mappings=mappings, bioms=bioms, tgzs=tgzs)
