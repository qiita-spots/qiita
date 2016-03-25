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
    study_prep_get_req, study_get_req, study_delete_req,
    study_files_get_req)


class StudyIndexHandler(BaseHandler):
    @authenticated
    def get(self, study_id):
        study = to_int(study_id)

        study_info = study_get_req(study, self.current_user.id)
        if study_info['status'] != 'success':
            raise HTTPError(404, study_info['message'])

        study_info = study_info['info']

        editable = study_info['status'] == 'sandbox'

        self.render("study_base.html", study_info=study_info,
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
        if study_info['lab_person']:
            contact = email.format(**study_info['lab_person'])
        else:
            contact = None

        self.render('study_ajax/base_info.html',
                    study_info=study_info, publications=study_doi, pi=pi,
                    contact=contact)


class StudyDeleteAjax(BaseHandler):
    def post(self):
        study_id = self.get_argument('study_id')
        self.write(study_delete_req(int(study_id), self.current_user.id))


class DataTypesMenuAJAX(BaseHandler):
    @authenticated
    def get(self):
        study_id = to_int(self.get_argument('study_id'))
        # Retrieve the prep template information for the menu
        prep_info = study_prep_get_req(study_id, self.current_user.id)
        # Make sure study exists
        if prep_info['status'] != 'success':
            raise HTTPError(404, prep_info['message'])

        prep_info = prep_info['info']

        self.render('study_ajax/data_type_menu.html', prep_info=prep_info,
                    study_id=study_id)


class StudyFilesAJAX(BaseHandler):
    @authenticated
    def get(self):
        study_id = to_int(self.get_argument('study_id'))
        atype = self.get_argument('artifact_type')
        pt_id = self.get_argument('prep_template_id')

        res = study_files_get_req(study_id, pt_id, atype)

        self.render('study_ajax/artifact_file_selector.html',
                    remaining=res['remaining'],
                    file_types=res['file_types'],
                    num_prefixes=res['num_prefixes'])
