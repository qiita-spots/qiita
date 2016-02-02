from __future__ import division

from tornado.web import authenticated

from qiita_pet.handlers.util import to_int
from qiita_pet.handlers.base_handlers import BaseHandler
from qiita_pet.handlers.api_proxy import artifact_get_req


class ProcessArtifactHandler(BaseHandler):
    @authenticated
    def get(self):
        artifact_id = to_int(self.get_argument('artifact_id'))

        info = artifact_get_req(self.current_user.id, artifact_id)
        self.render('study_ajax/processing_study.html', artifact_id=info['id'],
                    artifact_type=info['type'])


class ListCommandsHandler(BaseHandler):
    @authenticated
    def get(self):
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
        # job_id = self.get_argument("job_id")
        self.write({'status': 'success',
                    'message': '',
                    'options': []})
