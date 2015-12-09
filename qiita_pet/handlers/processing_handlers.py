from tornado.web import authenticated

from .base_handlers import BaseHandler
from qiita_db.software import Parameters, DefaultParameters
from qiita_ware.executor import plugin_submit


class ProcessHandler(BaseHandler):
    @authenticated
    def post(self):
        study_id = int(self.get_argument('study_id'))
        preprocessed_data_id = int(self.get_argument('preprocessed_data_id'))
        param_id = self.get_argument('parameter-set-%s' % preprocessed_data_id)

        parameters = Parameters.from_default_params(
            DefaultParameters(param_id), {'input_data': preprocessed_data_id})
        job_id = plugin_submit(self.current_user, parameters)

        self.render('compute_wait.html',
                    job_id=job_id, title='Processing',
                    completion_redirect='/study/description/%d?top_tab='
                                        'preprocessed_data_tab&sub_tab=%s'
                                        % (study_id, preprocessed_data_id))
