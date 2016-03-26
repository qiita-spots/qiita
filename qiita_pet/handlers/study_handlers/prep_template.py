# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from __future__ import division
from os.path import join

from tornado.web import authenticated
import pandas as pd

from qiita_pet.handlers.util import to_int
from qiita_pet.handlers.base_handlers import BaseHandler
from qiita_db.util import (get_files_from_uploads_folders, get_mountpoint,
                           supported_filepath_types)
from qiita_pet.handlers.api_proxy import (
    prep_template_ajax_get_req, prep_template_graph_get_req,
    new_prep_template_get_req, prep_template_summary_get_req)


class NewPrepTemplateAjax(BaseHandler):
    @authenticated
    def get(self):
        study_id = to_int(self.get_argument('study_id'))
        result = new_prep_template_get_req(study_id)
        self.render('study_ajax/add_prep_template.html',
                    prep_files=result['prep_files'],
                    data_types=result['data_types'],
                    ontology=result['ontology'],
                    study_id=study_id)


class PrepTemplateGraphAJAX(BaseHandler):
    @authenticated
    def get(self):
        prep = to_int(self.get_argument('prep_id'))
        self.write(prep_template_graph_get_req(prep, self.current_user.id))


class PrepTemplateSummaryAJAX(BaseHandler):
    @authenticated
    def get(self):
        prep_id = to_int(self.get_argument('prep_id'))
        res = prep_template_summary_get_req(prep_id, self.current_user.id)
        self.render('study_ajax/prep_summary_table.html',
                    stats=res['summary'])


class PrepTemplateAJAX(BaseHandler):
    @authenticated
    def get(self):
        """Send formatted summary page of prep template"""
        prep_id = to_int(self.get_argument('prep_id'))

        res = prep_template_ajax_get_req(self.current_user.id, prep_id)
        res['prep_id'] = prep_id

        self.render('study_ajax/prep_summary.html', **res)


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
        if 'run_prefix' in prep.columns:
            # Use run_prefix column of prep template to auto-select
            # per-prefix uploaded files if available.
            per_prefix = True
            prep_prefixes = set(prep['run_prefix'])
            for _, filename in uploaded:
                for prefix in prep_prefixes:
                    if filename.startswith(prefix):
                        selected.append(filename)
                    else:
                        not_selected.append(filename)
        else:
            per_prefix = False
            not_selected = [f for _, f in uploaded]

        # Write out if this prep template supports per-prefix files, and the
        # as well as pre-selected and remaining files
        self.write({
            'per_prefix': per_prefix,
            'file_types': file_types,
            'selected': selected,
            'remaining': not_selected})
