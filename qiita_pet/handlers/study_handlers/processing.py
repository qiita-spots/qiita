# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from json import dumps, loads

from tornado.web import authenticated

from qiita_pet.handlers.api_proxy import (
    job_ajax_get_req,
    job_ajax_patch_req,
    list_commands_handler_get_req,
    list_options_handler_get_req,
    workflow_handler_patch_req,
    workflow_handler_post_req,
    workflow_run_post_req,
)
from qiita_pet.handlers.base_handlers import BaseHandler


class ListCommandsHandler(BaseHandler):
    @authenticated
    def get(self):
        # Fun fact - if the argument is a list, JS adds '[]' to the
        # argument name
        artifact_id = self.get_argument("artifact_id")
        exclude_analysis = self.get_argument("include_analysis") == "false"
        self.write(list_commands_handler_get_req(artifact_id, exclude_analysis))


class ListOptionsHandler(BaseHandler):
    @authenticated
    def get(self):
        command_id = self.get_argument("command_id")
        artifact_id = self.get_argument("artifact_id", None)
        # if the artifact id has ':' it means that it's a job in construction
        if artifact_id is not None and ":" in artifact_id:
            artifact_id = None
        self.write(list_options_handler_get_req(command_id, artifact_id))


class WorkflowRunHandler(BaseHandler):
    @authenticated
    def post(self):
        w_id = self.get_argument("workflow_id")
        self.write(workflow_run_post_req(w_id))


class WorkflowHandler(BaseHandler):
    @authenticated
    def post(self):
        command_id = self.get_argument("command_id")
        params = self.get_argument("params")

        if self.request.files:
            parameters = loads(params)
            for k, v in self.request.files.items():
                # [0] there is only one file -- this block is needed because
                # 'body' is a byte and JSON doesn't know how to translate it
                parameters[k] = {
                    "body": v[0]["body"].decode("utf-8"),
                    "filename": v[0]["filename"],
                    "content_type": v[0]["content_type"],
                }
            params = dumps(parameters)

        self.write(workflow_handler_post_req(self.current_user.id, command_id, params))

    @authenticated
    def patch(self):
        req_op = self.get_argument("op")
        req_path = self.get_argument("path")
        req_value = self.get_argument("value", None)
        req_from = self.get_argument("from", None)

        try:
            res = workflow_handler_patch_req(req_op, req_path, req_value, req_from)
            self.write(res)
        except Exception as e:
            self.write({"status": "error", "message": str(e)})


class JobAJAX(BaseHandler):
    @authenticated
    def get(self):
        job_id = self.get_argument("job_id")
        self.write(job_ajax_get_req(job_id))

    @authenticated
    def patch(self):
        req_op = self.get_argument("op")
        req_path = self.get_argument("path")
        req_value = self.get_argument("value", None)
        req_from = self.get_argument("from", None)

        try:
            res = job_ajax_patch_req(req_op, req_path, req_value, req_from)
            self.write(res)
        except Exception as e:
            self.write({"status": "error", "message": str(e)})
