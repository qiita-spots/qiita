from tornado.web import authenticated

from .base_handlers import BaseHandler
from qiita_ware.dispatchable import processor
from qiita_ware.context import submit


class ProcessHandler(BaseHandler):
    @authenticated
    def post(self):
        study_id = int(self.get_argument('study_id'))
        preprocessed_data_id = int(self.get_argument('preprocessed_data_id'))
        param_id = self.get_argument('parameter-set-%s' % preprocessed_data_id)

        # The only parameter type supported is the ProcessedSortmernaParams
        # so we can hardcode the constructor here
        param_constructor = ProcessedSortmernaParams

        job_id = submit(self.current_user.id, processor, preprocessed_data_id,
                        param_id, param_constructor)

        self.render('compute_wait.html',
                    job_id=job_id, title='Processing',
                    completion_redirect='/study/description/%d?top_tab='
                                        'preprocessed_data_tab&sub_tab=%s'
                                        % (study_id, preprocessed_data_id))
