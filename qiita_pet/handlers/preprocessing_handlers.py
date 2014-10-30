from tornado.web import authenticated

from .base_handlers import BaseHandler
from qiita_ware.dispatchable import preprocessor
from qiita_ware.context import submit
from qiita_db.parameters import PreprocessedIlluminaParams
from qiita_db.study import Study 
from qiita_db.metadata_template import PrepTemplate


class PreprocessHandler(BaseHandler):
    @authenticated
    def post(self):
        study_id = int(self.get_argument('study_id'))
        prep_template_id = int(self.get_argument('prep_template_id'))
        rev_comp_mapping_barcodes = self.get_argument('prep_template_id')
        # currently forcing these values
        # param_constructor = self.get_argument('param_constructor')
        if rev_comp_mapping_barcodes == 'false':
            param_id = 1
        else:
            param_id = 2

        job_id = submit(self.current_user, preprocessor, Study(study_id),
                        PrepTemplate(prep_template_id), param_id)

        # do not remove this is useful for debugging
        print job_id
        self.render('compute_wait.html', user=self.current_user,
                    job_id=job_id, title='Preprocessing',
                    completion_redirect='/study/description/%d' % study_id)
