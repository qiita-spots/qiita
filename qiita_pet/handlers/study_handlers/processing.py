from __future__ import division

from tornado.web import authenticated

from qiita_pet.handlers.util import to_int
from qiita_pet.handlers.base_handlers import BaseHandler


class ProcessArtifactHandler(BaseHandler):
    @authenticated
    def get(self):
        artifact_id = to_int(self.get_argument('artifact_id'))

        self.render('study_ajax/processing_artifact.html',
                    artifact_id=artifact_id,
                    name="NAME IT")


class ListCommandsHandler(BaseHandler):
    @authenticated
    def get(self):
        # TODO: callback to get commands for artifact type
        # artifact_type = self.get_argument("artifact_type")
        self.write({'status': 'success',
                    'message': '',
                    'commands': [
                        {'id': 1, 'command': 'DEMUX', 'output': ['FASTA']},
                        {'id': 1, 'command': 'FILTER',
                         'output': ['FASTA', 'OTHER']},
                        {'id': 1, 'command': 'PICK_OTUS', 'output': ['BIOM']}]
                    })


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
