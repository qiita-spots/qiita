from tornado.web import authenticated

from .base_handlers import BaseHandler
from qiita_ware.dispatchable import preprocessor
from qiita_db.data import RawData
from qiita_db.parameters import (PreprocessedIlluminaParams,
                                 Preprocessed454Params)
from qiita_db.metadata_template import PrepTemplate
from qiita_ware.context import submit
from qiita_pet.uimodules.raw_data_tab import (PreprocessIlluminaParametersForm,
                                              Preprocess454ParametersForm)


class PreprocessHandler(BaseHandler):
    @authenticated
    def post(self):
        study_id = int(self.get_argument('study_id'))
        prep_template_id = int(self.get_argument('prep_template_id'))
        raw_data = RawData(PrepTemplate(prep_template_id).raw_data)

        # Get the preprocessing parameters
        if raw_data.file_type == 'FASTQ':
            form_data = PreprocessIlluminaParametersForm()
            form_data.process(data=self.request.arguments)
            rcomp_mapping_barcodes = form_data.data['rev_comp_mapping_barcodes']
            # currently only allow the user to change a single parameter of split
            # libraries: --rev_comp_mapping_barcodes. The parameter ids 1 and 2
            # contain the same set of values except for that flag. If param_id = 1,
            # the flag is not activated, while in param_id = 2; it is.
            if rcomp_mapping_barcodes:
                # Choose the parameter set with the --rev_comp_mapping_barcodes
                # flag activated
                param_id = 2
            else:
                # Choose the parameter set with the --rev_comp_mapping_barcodes
                # flag not activated
                param_id = 1
            param_constructor = PreprocessedIlluminaParams
        elif raw_data.file_type in ('FASTA', 'SFF'):
            form_data = Preprocess454ParametersForm()
            form_data.process(data=self.request.arguments)
            param_constructor = Preprocessed454Params
            barcode_type = form_data.data['barcode_type']
            if barcode_type == 'golay_12':
                param_id = 3
            else:
                param_id = 4
        else:
            raise ValueError('Unknown filetype')


        job_id = submit(self.current_user, preprocessor, study_id,
                        prep_template_id, param_id, param_constructor)

        self.render('compute_wait.html', user=self.current_user,
                    job_id=job_id, title='Preprocessing',
                    completion_redirect='/study/description/%d?top_tab='
                                        'raw_data_tab&sub_tab=%s&prep_tab=%s'
                                        % (study_id, raw_data.id,
                                           prep_template_id))
