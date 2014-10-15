from tornado.web import authenticated

from .base_handlers import BaseHandler
from qiita_ware.dispatchable import preprocessor
from qiita_ware.context import submit
from qiita_db.parameters import PreprocessedIlluminaParams


class PreprocessHandler(BaseHandler):
    @authenticated
    def post(self):
        study_id = int(self.get_argument('study_id'))
        raw_data_id = int(self.get_argument('raw_data_id'))
        # currently forcing these values
        # param_id = int(self.get_argument('param_id'))
        # param_constructor = self.get_argument('param_constructor')
        param_id = 1
        param_constructor = PreprocessedIlluminaParams

        job_id = submit(self.current_user, preprocessor, study_id, raw_data_id,
                        param_id, param_constructor)

        self.render('compute_wait.html', user=self.current_user,
                    job_id=job_id, title='Preprocessing',
                    completion_redirect='/compute_complete')
