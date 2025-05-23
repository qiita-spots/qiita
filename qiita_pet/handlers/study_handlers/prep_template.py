# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from os.path import join, relpath

from tornado.web import authenticated
from tornado.escape import url_escape
import pandas as pd

from qiita_core.qiita_settings import qiita_config
from qiita_pet.handlers.util import to_int
from qiita_pet.handlers.base_handlers import BaseHandler
from qiita_db.util import (get_files_from_uploads_folders, get_mountpoint,
                           supported_filepath_types)
from qiita_db.metadata_template.prep_template import PrepTemplate
from qiita_pet.handlers.api_proxy import (
    prep_template_ajax_get_req, new_prep_template_get_req,
    prep_template_summary_get_req)


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


class AddDefaultWorkflowHandler(BaseHandler):
    @authenticated
    def post(self):
        prep_id = self.get_argument('prep_id')
        msg_error = None
        data = None
        try:
            workflow = PrepTemplate(prep_id).add_default_workflow(
                self.current_user)
            data = workflow.id
        except Exception as error:
            msg_error = str(error)

        self.write({'data': data, 'msg_error': msg_error})


class PrepTemplateSummaryAJAX(BaseHandler):
    @authenticated
    def get(self):
        prep_id = to_int(self.get_argument('prep_id'))

        res = prep_template_summary_get_req(prep_id, self.current_user.id)

        self.render('study_ajax/prep_summary_table.html', pid=prep_id,
                    stats=res['summary'], editable=res['editable'],
                    num_samples=res['num_samples'])


class PrepTemplateAJAX(BaseHandler):
    @authenticated
    def get(self):
        """Send formatted summary page of prep template"""
        prep_id = to_int(self.get_argument('prep_id'))
        row_id = self.get_argument('row_id', '0')
        current_user = self.current_user

        res = prep_template_ajax_get_req(current_user.id, prep_id)
        res['prep_id'] = prep_id
        res['row_id'] = row_id
        # Escape the message just in case javascript breaking characters in it
        res['alert_message'] = url_escape(res['alert_message'])
        res['user_level'] = current_user.level
        if res['creation_job'] is not None:
            params = res['creation_job'].parameters.values
            summary = None
            if 'sample_sheet' in params:
                fp = params['sample_sheet']
                res['creation_job_filename'] = fp['filename']
                res['creation_job_filename_body'] = fp['body']
                if res['creation_job'].status == 'success':
                    if res['creation_job'].outputs:
                        # [0] is the id, [1] is the filepath
                        _file = res['creation_job'].outputs[
                            'output'].html_summary_fp[1]
                        summary = relpath(_file, qiita_config.base_data_dir)
            else:
                res['creation_job_filename'] = None
                res['creation_job_filename_body'] = None
            res['creation_job_artifact_summary'] = summary
        res['human_reads_filter_method'] = None
        a = PrepTemplate(prep_id).artifact
        if a is not None:
            hrfm = a.human_reads_filter_method
            if hrfm is not None:
                res['human_reads_filter_method'] = hrfm

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
            not_selected = [f for _, f, _ in uploaded]

        # Write out if this prep template supports per-prefix files, and the
        # as well as pre-selected and remaining files
        self.write({
            'per_prefix': per_prefix,
            'file_types': file_types,
            'selected': selected,
            'remaining': not_selected})
