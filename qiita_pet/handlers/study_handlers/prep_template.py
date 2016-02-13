# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from __future__ import division
from os.path import join

from tornado.web import authenticated, HTTPError
import pandas as pd

from qiita_pet.handlers.util import to_int, download_link_or_path
from qiita_pet.handlers.base_handlers import BaseHandler
from qiita_pet.util import is_localhost
from qiita_db.util import (get_files_from_uploads_folders, get_mountpoint,
                           supported_filepath_types)
from qiita_pet.handlers.api_proxy import (
    prep_template_summary_get_req, prep_template_post_req,
    prep_template_put_req, prep_template_delete_req,
    prep_template_filepaths_get_req, data_types_get_req,
    prep_template_graph_get_req, ena_ontology_get_req)


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
        prep_id = self.get_argument('prep_id')
        files = [f for _, f in get_files_from_uploads_folders(str(study_id))
                 if f.endswith(('txt', 'tsv'))]
        data_types = sorted(data_types_get_req())
        is_local = is_localhost(self.request.headers['host'])
        # Get the most recent version for download and build the link
        download = prep_template_filepaths_get_req(
            study_id, self.current_user.id)['filepaths'][-1]
        dl_path = download_link_or_path(
            is_local, download[1], download[0], "Download prep information")
        ontology = ena_ontology_get_req()

        stats = prep_template_summary_get_req(prep_id, self.current_user.id)
        self.render('study_ajax/prep_summary.html', stats=stats['summary'],
                    num_samples=stats['num_samples'], dl_path=dl_path,
                    files=files, prep_id=prep_id, data_types=data_types,
                    ontology=ontology)

    @authenticated
    def post(self):
        """Edit/delete/recreate prep template"""
        action = self.get_argument('action')
        prep_id = self.get_argument('prep_id')
        if action == 'create':
            filepath = self.get_argument('filepath')
            data_type = self.get_argument('data_type')
            result = prep_template_post_req(prep_id, self.current_user.id,
                                            data_type, filepath)
        elif action == 'update':
            filepath = self.get_argument('filepath')
            result = prep_template_put_req(prep_id, self.current_user.id,
                                           prep_template=filepath)
        elif action == 'delete':
            result = prep_template_delete_req(prep_id, self.current_user.id)
        elif action == 'ontology':
            inv_type = self.get_argument('ena')
            user_inv_type = self.get_argument('ena_user', None)
            new_inv_type = self.get_argument('ena_new', None)
            result = prep_template_put_req(
                prep_id, self.current_user.id, investigation_type=inv_type,
                user_defined_investigation_type=user_inv_type,
                new_investigation_type=new_inv_type)
        else:
            raise HTTPError(400, 'Unknown prep template action: %s' % action)
        self.write(result)


class PrepFilesHandler(BaseHandler):
    @authenticated
    def get(self):
        study_id = self.get_argument('study_id')
        prep_file = self.get_argument('prep_file')
        prep_type = self.get_argument('type')

        # TODO: Get file types for the artifact type
        # FILE TYPE IN POSTION 0 MUST BE DEFAULT FOR SELECTED
        file_types = supported_filepath_types(prep_type)

        selected = []
        not_selected = []
        _, base = get_mountpoint("uploads")[0]
        uploaded = get_files_from_uploads_folders(study_id)
        prep = pd.read_table(join(base, study_id, prep_file), sep='\t')
        if 'per_prefix' in prep.columns:
            # Use per_prefix column of prep template to auto-select
            # per-sample uploaded files if available.
            per_sample = True
            prep_prefixes = set(prep['per_prefix'])
            for _, filename in uploaded:
                for prefix in prep_prefixes:
                    if filename.startswith(prefix):
                        selected.append(filename)
                    else:
                        not_selected.append(filename)
        else:
            per_sample = False
            not_selected = [f for _, f in uploaded]

        # Write out if this prep template supports per-sample files, and the
        # as well as pre-selected and remaining files
        self.write({
            'per_sample': per_sample,
            'file_types': file_types,
            'selected': selected,
            'remaining': not_selected})
