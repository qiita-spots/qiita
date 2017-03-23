# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from qiita_db.handlers.oauth2 import authenticate_oauth
from .rest_handler import RESTHandler


class StudyHandler(RESTHandler):
    # /api/v1/study/<int>

    @authenticate_oauth
    def get(self, study_id):
        study = self.study_boilerplate(study_id)
        if study is None:
            return

        info = study.info
        self.write({'title': study.title,
                    'contacts': {'principal-investigator': [
                                     info['principal_investigator'].name,
                                     info['principal_investigator'].email],
                                 'lab-person': [
                                     info['lab_person'].name,
                                     info['lab_person'].email]},
                    'abstract': info['study_abstract']})
        self.finish()
