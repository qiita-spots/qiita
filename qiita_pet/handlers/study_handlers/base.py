# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from __future__ import division

from tornado.web import authenticated, HTTPError

from qiita_pet.util import EBI_LINKIFIER
from qiita_pet.handlers.util import to_int, doi_linkifier, pubmed_linkifier
from qiita_pet.handlers.base_handlers import BaseHandler
from qiita_pet.handlers.api_proxy import (
    study_prep_get_req, study_get_req, study_delete_req, study_patch_request,
    study_files_get_req)


class StudyIndexHandler(BaseHandler):
    @authenticated
    def get(self, study_id):
        study = to_int(study_id)

        study_info = study_get_req(study, self.current_user.id)
        if study_info['status'] != 'success':
            raise HTTPError(404, study_info['message'])

        self.render("study_base.html", **study_info)

    @authenticated
    def patch(self, study_id):
        """Patches a prep template in the system

        Follows the JSON PATCH specification:
        https://tools.ietf.org/html/rfc6902
        """
        study_id = to_int(study_id)
        req_op = self.get_argument('op')
        req_path = self.get_argument('path')
        req_value = self.request.arguments.get('value[]', None)
        req_form= self.get_argument('form', None)

        response = study_patch_request(self.current_user.id, study_id,
                                       req_op, req_path, req_value, req_form)
        self.write(response)


class StudyBaseInfoAJAX(BaseHandler):
    @authenticated
    def get(self):
        study_id = self.get_argument('study_id')
        study = to_int(study_id)
        res = study_get_req(study, self.current_user.id)
        study_info = res['study_info']
        pdoi = [doi_linkifier([p]) for p in study_info['publication_doi']]
        ppid = [pubmed_linkifier([p]) for p in study_info['publication_pid']]

        email = '<a href="mailto:{email}">{name} ({affiliation})</a>'
        pi = email.format(**study_info['principal_investigator'])
        if study_info['lab_person']:
            contact = email.format(**study_info['lab_person'])
        else:
            contact = None
        share_access = (self.current_user.id in study_info['shared_with'] or
                        self.current_user.id == study_info['owner'])

        ebi_info = study_info['ebi_submission_status']
        ebi_study_accession = study_info['ebi_study_accession']
        if ebi_study_accession:
            links = ''.join([EBI_LINKIFIER.format(a)
                             for a in ebi_study_accession.split(',')])
            ebi_info = '%s (%s)' % (links, study_info['ebi_submission_status'])

        self.render('study_ajax/base_info.html',
                    study_info=study_info, publications=', '.join(pdoi + ppid),
                    pi=pi, contact=contact, editable=res['editable'],
                    share_access=share_access, ebi_info=ebi_info)


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

        res = study_files_get_req(self.current_user.id, study_id, pt_id, atype)

        self.render('study_ajax/artifact_file_selector.html', **res)
