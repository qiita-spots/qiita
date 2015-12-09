from tornado.web import authenticated

from .base_handlers import BaseHandler
from qiita_db.metadata_template.prep_template import PrepTemplate
from qiita_ware.executor import plugin_submit
from qiita_core.util import execute_as_transaction
from qiita_db.software import Parameters, DefaultParameters


class PreprocessHandler(BaseHandler):
    @authenticated
    @execute_as_transaction
    def post(self):
        study_id = int(self.get_argument('study_id'))
        prep_template_id = int(self.get_argument('prep_template_id'))
        raw_data = PrepTemplate(prep_template_id).artifact
        param_id = int(self.get_argument('preprocessing_parameters_id'))

        parameters = Parameters.from_default_params(
            DefaultParameters(param_id), {'input_data': raw_data.id})

        job_id = plugin_submit(self.current_user, parameters)

        self.render('compute_wait.html',
                    job_id=job_id, title='Preprocessing',
                    completion_redirect='/study/description/%d?top_tab='
                                        'prep_template_tab&sub_tab=%s'
                                        % (study_id, prep_template_id))
