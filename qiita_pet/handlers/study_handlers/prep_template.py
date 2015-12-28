# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from __future__ import division

from tornado.web import authenticated, HTTPError

from qiita_pet.handlers.util import to_int, download_link_or_path
from qiita_pet.handlers.base_handlers import BaseHandler
from qiita_pet.util import is_localhost
from qiita_db.util import get_files_from_uploads_folders
from qiita_pet.handlers.api_proxy import (
    prep_template_summary_get_req, prep_template_post_req,
    prep_template_put_req, prep_template_delete_req,
    get_prep_template_filepaths, data_types_get_req,
    prep_template_graph_get_req)


class PrepTemplateGraphAJAX(BaseHandler):
    @authenticated
    def get(self):
        prep = to_int(self.get_argument('prep_id'))
        self.write(prep_template_graph_get_req(prep, self.current_user.id))


class PrepTemplateAJAX(BaseHandler):
    @authenticated
    def get(self):
        """Send formatted summary page of prep template"""
        study_id = self.get_argument('study_id')
        files = [f for _, f in get_files_from_uploads_folders(study_id)
                 if f.endswith(('txt', 'tsv'))]
        data_types = sorted(data_types_get_req())
        is_local = is_localhost(self.request.headers['host'])
        # Get the most recent version for download and build the link
        download = get_prep_template_filepaths(study_id,
                                               self.current_user.id)[-1]
        dl_path = download_link_or_path(
            is_local, download[0], download[1], "Download prep information")

        stats = prep_template_summary_get_req(study_id, self.current_user.id)
        self.render('study_ajax/prep_summary.html', stats=stats['summary'],
                    num_samples=stats['num_samples'], dl_path=dl_path,
                    files=files, study_id=study_id, data_types=data_types)

    @authenticated
    def post(self):
        """Edit/delete/recreate prep template"""
        action = self.get_argument('action')
        study_id = self.get_argument('study_id')
        if action == 'create':
            filepath = self.get_argument('filepath')
            data_type = self.get_argument('data_type')
            result = prep_template_post_req(study_id, self.current_user.id,
                                            data_type, filepath)
        elif action == 'update':
            filepath = self.get_argument('filepath')
            result = prep_template_put_req(study_id, self.current_user.id,
                                           filepath)
        elif action == 'delete':
            result = prep_template_delete_req(study_id, self.current_user.id)
        else:
            raise HTTPError(400, 'Unknown prep template action: %s' % action)
        self.write(result)
