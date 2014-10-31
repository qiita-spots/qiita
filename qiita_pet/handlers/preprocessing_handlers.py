from tornado.web import authenticated

from .base_handlers import BaseHandler
from qiita_ware.dispatchable import preprocessor
from qiita_ware.context import submit
from qiita_db.parameters import PreprocessedIlluminaParams


class PreprocessHandler(BaseHandler):
    @authenticated
    def post(self):
        study_id = int(self.get_argument('study_id'))
        prep_template_id = int(self.get_argument('prep_template_id'))
        rcomp_mapping_barcodes = self.get_argument('rev_comp_mapping_barcodes')
        # currently forcing these values
        # param_constructor = self.get_argument('param_constructor')
        if rcomp_mapping_barcodes == 'false':
            param_id = 1
        else:
            param_id = 2

        param_constructor = PreprocessedIlluminaParams

        job_id = submit(self.current_user, preprocessor, study_id,
                        prep_template_id, param_id, param_constructor)

        self.render('compute_wait.html', user=self.current_user,
                    job_id=job_id, title='Preprocessing',
                    completion_redirect='/study/description/%d' % study_id)
