# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from tornado.web import UIModule

from qiita_db.data import PreprocessedData
from qiita_db.metadata_template import PrepTemplate
from qiita_db.user import User


class PreprocessedDataTab(UIModule):
    def render(self, study):
        avail_ppd = [(ppd_id, PreprocessedData(ppd_id))
                     for ppd_id in study.preprocessed_data()]
        return self.render_string(
            "preprocessed_data_tab.html",
            available_preprocessed_data=avail_ppd,
            study_id=study.id)


class PreprocessedDataInfoTab(UIModule):
    def render(self, study_id, preprocessed_data):
        user = User(self.current_user)
        ppd_id = preprocessed_data.id
        ebi_status = preprocessed_data.submitted_to_insdc_status()
        ebi_study_accession = preprocessed_data.ebi_study_accession
        ebi_submission_accession = preprocessed_data.ebi_submission_accession
        filepaths = preprocessed_data.get_filepaths()
        is_local_request = ('localhost' in self.request.headers['host'] or
                            '127.0.0.1' in self.request.headers['host'])
        show_ebi_btn = user.level == "admin"

        if PrepTemplate.exists(preprocessed_data.prep_template):
            prep_template_id = preprocessed_data.prep_template
            raw_data_id = PrepTemplate(prep_template_id).raw_data
        else:
            prep_template_id = None
            raw_data_id = None

        return self.render_string(
            "preprocessed_data_info_tab.html",
            ppd_id=ppd_id,
            show_ebi_btn=show_ebi_btn,
            ebi_status=ebi_status,
            ebi_study_accession=ebi_study_accession,
            ebi_submission_accession=ebi_submission_accession,
            filepaths=filepaths,
            is_local_request=is_local_request,
            prep_template_id=prep_template_id,
            raw_data_id=raw_data_id)
