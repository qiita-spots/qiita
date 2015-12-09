# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from __future__ import division

from tornado.web import authenticated

from qiita_pet.handlers.util import to_int
# ONLY IMPORT FROM qiita_pet HERE. All other imports must be made in
# api_proxy.py so they will be removed when we get the API in place.
from .api_proxy import StudyAPIProxy


class StudyIndexHandler(StudyAPIProxy):
    @authenticated
    def get(self, study_id):
        study = to_int(study_id)
        # Proxies for what will become API requests
        prep_info = self.study_prep_proxy(study)
        data_types = self.study_data_types_proxy()
        study_info = self.study_info_proxy(study)

        self.render("study_base.html", prep_info=prep_info,
                    data_types=data_types, study_info=study_info)


class StudyBaseInfoAJAX(StudyAPIProxy):
    @authenticated
    def get(self):
        study = to_int(self.get_argument('study_id'))
        # Proxy for what will become API request
        study_info = self.study_info_proxy(study)

        self.render('study_ajax/base_info.html',
                    study_info=study_info)
