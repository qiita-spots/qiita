# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from __future__ import division

from tornado.web import authenticated, HTTPError

from qiita_pet.handlers.util import to_int, doi_linkifier
from qiita_pet.handlers.base_handlers import BaseHandler
from qiita_pet.handlers.api_proxy import (
    study_prep_get_req, data_types_get_req, study_get_req)


class StudyIndexHandler(BaseHandler):
    @authenticated
    def get(self, study_id):
        study = to_int(study_id)

        # Proxies for what will become API requests
        prep_info = study_prep_get_req(study, self.current_user.id)
        # Make sure study exists
        if prep_info['status'] != 'success':
            raise HTTPError(404, prep_info['message'])

        prep_info = prep_info['info']
        data_types = data_types_get_req()['data_types']
        study_info = study_get_req(study, self.current_user.id)['info']
        editable = study_info['status'] == 'sandbox'

        self.render("study_base.html", prep_info=prep_info,
                    data_types=data_types, study_info=study_info,
                    editable=editable)


class StudyBaseInfoAJAX(BaseHandler):
    @authenticated
    def get(self):
        study_id = self.get_argument('study_id')
        study = to_int(study_id)
        study_info = study_get_req(study, self.current_user.id)['info']
        study_doi = ' '.join(
            [doi_linkifier(p) for p in study_info['publications']])
        email = '<a href="mailto:{email}">{name} ({affiliation})</a>'
        pi = email.format(**study_info['principal_investigator'])
        contact = email.format(**study_info['lab_person'])

        self.render('study_ajax/base_info.html',
                    study_info=study_info, publications=study_doi, pi=pi,
                    contact=contact)
