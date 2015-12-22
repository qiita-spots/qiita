# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from __future__ import division

from tornado.web import authenticated

from qiita_pet.handlers.util import to_int, doi_linkifier
# ONLY IMPORT FROM qiita_pet HERE. All other imports must be made in
# api_proxy.py so they will be removed when we get the API in place.
from qiita_pet.handlers.base_handlers import BaseHandler
from qiita_pet.handlers.api_proxy import (
    prep_template_get_req, data_types_get_req, study_get_req)


class StudyIndexHandler(BaseHandler):
    @authenticated
    def get(self, study_id):
        study = to_int(study_id)
        # Proxies for what will become API requests
        prep_info = prep_template_get_req(study, self.current_user.id)
        data_types = data_types_get_req()
        study_info = study_get_req(study, self.current_user.id)
        editable = study_info['status'] == 'sandbox'

        self.render("study_base.html", prep_info=prep_info,
                    data_types=data_types, study_info=study_info,
                    editable=editable)


class StudyBaseInfoAJAX(BaseHandler):
    @authenticated
    def get(self):
        study_id = self.get_argument('study_id')
        study = to_int(study_id)
        # Proxy for what will become API request
        study_info = study_get_req(study, self.current_user.id)
        study_doi = ' '.join(
            [doi_linkifier(p) for p in study_info['publications']])

        self.render('study_ajax/base_info.html',
                    study_info=study_info, publications=study_doi)
