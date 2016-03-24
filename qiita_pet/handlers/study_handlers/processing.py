from __future__ import division

from tornado.web import authenticated

from qiita_pet.handlers.util import to_int
from qiita_pet.handlers.base_handlers import BaseHandler
from qiita_pet.handlers.api_proxy import (
    list_commands_handler_get_req, process_artifact_handler_get_req,
    list_options_handler_get_req, workflow_handler_post_req)


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
        self.write(list_commands_handler_get_req(artifact_types))


class ListOptionsHandler(BaseHandler):
    @authenticated
    def get(self):
        command_id = self.get_argument("command_id")
        self.write(list_options_handler_get_req(command_id))


class WorkflowHandler(BaseHandler):
    @authenticated
    def post(self):
        dflt_params_id = self.get_argument('dflt_params_id')
        req_params = self.get_argument('req_params')
        self.write(workflow_handler_post_req(
            self.current_user.id, dflt_params_id, req_params))
