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
from qiita_pet.handlers.api_proxy import (
    list_commands_handler_get_req, process_artifact_handler_get_req,
    list_options_handler_get_req, workflow_handler_post_req,
    workflow_handler_patch_req, job_ajax_get_req,
    workflow_run_post_req)


class ProcessArtifactHandler(BaseHandler):
    @authenticated
    def get(self):
        artifact_id = to_int(self.get_argument('artifact_id'))
        res = process_artifact_handler_get_req(artifact_id)
        res['artifact_id'] = artifact_id
        self.render('study_ajax/processing_artifact.html', **res)


class ListCommandsHandler(BaseHandler):
    @authenticated
    def get(self):
        # Fun fact - if the argument is a list, JS adds '[]' to the
        # argument name
        artifact_types = self.get_argument("artifact_types[]")
        exclude_analysis = self.get_argument('include_analysis') == 'false'
        self.write(
            list_commands_handler_get_req(artifact_types, exclude_analysis))


class ListOptionsHandler(BaseHandler):
    @authenticated
    def get(self):
        command_id = self.get_argument("command_id")
        self.write(list_options_handler_get_req(command_id))


class WorkflowRunHandler(BaseHandler):
    @authenticated
    def post(self):
        w_id = self.get_argument('workflow_id')
        self.write(workflow_run_post_req(w_id))


class WorkflowHandler(BaseHandler):
    @authenticated
    def post(self):
        command_id = self.get_argument('command_id')
        params = self.get_argument('params')
        self.write(workflow_handler_post_req(
            self.current_user.id, command_id, params))

    @authenticated
    def patch(self):
        req_op = self.get_argument('op')
        req_path = self.get_argument('path')
        req_value = self.get_argument('value', None)
        req_from = self.get_argument('from', None)

        self.write(workflow_handler_patch_req(
            req_op, req_path, req_value, req_from))


class JobAJAX(BaseHandler):
    @authenticated
    def get(self):
        job_id = self.get_argument('job_id')
        self.write(job_ajax_get_req(job_id))
