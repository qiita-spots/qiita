# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from tornado.web import UIModule


class PreprocessedDataTab(UIModule):
    def render(self, study):
        avail_ppd = []
        return self.render_string(
            "preprocessed_data_tab.html",
            available_preprocessed_data=avail_ppd,
            study_id=study.id)


class PreprocessedDataInfoTab(UIModule):
    def render(self, study_id, preprocessed_data):
        ppd_id = preprocessed_data.id
        ebi_status = preprocessed_data.submitted_to_insdc_status()
        ebi_study_accession = preprocessed_data.ebi_study_accession
        ebi_submission_accession = preprocessed_data.ebi_submission_accession
        return self.render_string(
            "preprocessed_data_info_tab",
            ppd_id=ppd_id,
            ebi_status=ebi_status,
            ebi_study_accession=ebi_study_accession,
            ebi_submission_accession=ebi_submission_accession)
