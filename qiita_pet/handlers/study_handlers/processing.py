from __future__ import division

from tornado.web import authenticated

from qiita_pet.handlers.util import to_int
from qiita_pet.handlers.base_handlers import BaseHandler
from qiita_pet.handlers.api_proxy import (
    list_commands_handler_get_req, process_artifact_handler_get_req)


class ProcessArtifactHandler(BaseHandler):
    @authenticated
    def get(self):
        artifact_id = to_int(self.get_argument('artifact_id'))

        res = process_artifact_handler_get_req(artifact_id)

        self.render('study_ajax/processing_artifact.html',
                    artifact_id=artifact_id, name=res["name"],
                    type=res["type"])


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
        # TODO: callback to get optons for job
        # job_id = self.get_argument("job_id")
        self.write({'status': 'success',
                    'message': '',
                    'options': [{'name': 'com_int', 'value': 2,
                                 'type': 'integer', 'required': True},
                                {'name': 'com_bool', 'value': True,
                                 'type': 'bool', 'required': False},
                                {'name': 'com_string', 'value': 'blarg',
                                 'type': 'string', 'required': False},
                                {'name': 'com_float', 'value': 6.2,
                                 'type': 'float', 'required': False},
                                {'name': 'com_ref', 'value': 1,
                                 'type': 'reference', 'required': True},
                                {'name': 'com_artifact', 'value': 2,
                                 'type': 'reference', 'required': True}]})
