from json import loads

from tornado.web import authenticated

from .base_handlers import BaseHandler
from qiita_ware import r_server


class ComputeCompleteHandler(BaseHandler):
    @authenticated
    def get(self, job_id):
        details = loads(r_server.get(job_id))

        if details['status_msg'] == 'Failed':
            # TODO: something smart
            pass

        self.render('/')
