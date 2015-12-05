from tornado.web import authenticated

from .base_handlers import BaseHandler
from qiita_ware.dispatchable import preprocessor
from qiita_db.metadata_template.prep_template import PrepTemplate
from qiita_ware.context import submit
from qiita_core.util import execute_as_transaction


class PreprocessHandler(BaseHandler):
    @authenticated
    @execute_as_transaction
    def post(self):
        study_id = int(self.get_argument('study_id'))
        prep_template_id = int(self.get_argument('prep_template_id'))
        raw_data = PrepTemplate(prep_template_id).artifact
        param_id = int(self.get_argument('preprocessing_parameters_id'))

        user_id = self.current_user.id

        job_id = submit(user_id, preprocessor, user_id, raw_data.id, param_id)

        self.render('compute_wait.html',
                    job_id=job_id, title='Preprocessing',
                    completion_redirect='/study/description/%d?top_tab='
                                        'prep_template_tab&sub_tab=%s'
                                        % (study_id, prep_template_id))
