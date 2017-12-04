# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from tornado.web import authenticated

from qiita_pet.handlers.base_handlers import BaseHandler
from qiita_pet.handlers.api_proxy import (
    prep_template_post_req, prep_template_patch_req, prep_template_delete_req,
    prep_template_graph_get_req, prep_template_jobs_get_req)


class PrepTemplateHandler(BaseHandler):
    @authenticated
    def post(self):
        """Creates a prep template"""
        study_id = self.get_argument('study_id')
        data_type = self.get_argument('data-type')
        ena_ontology = self.get_argument('ena-ontology', None)
        user_ontology = self.get_argument('user-ontology', None)
        new_ontology = self.get_argument('new-ontology', None)
        prep_fp = self.get_argument('prep-file')

        response = prep_template_post_req(
            study_id, self.get_current_user().id, prep_fp, data_type,
            ena_ontology, user_ontology, new_ontology)

        self.write(response)

    @authenticated
    def patch(self):
        """Patches a prep template in the system

        Follows the JSON PATCH specification:
        https://tools.ietf.org/html/rfc6902
        """
        req_op = self.get_argument('op')
        req_path = self.get_argument('path')
        req_value = self.get_argument('value', None)
        req_from = self.get_argument('from', None)

        response = prep_template_patch_req(
            self.current_user.id, req_op, req_path, req_value, req_from)

        self.write(response)

    @authenticated
    def delete(self):
        """Deletes a prep template from the system"""
        prep_id = self.get_argument('prep-template-id')
        self.write(prep_template_delete_req(prep_id, self.current_user.id))


class PrepTemplateGraphHandler(BaseHandler):
    @authenticated
    def get(self, prep_id):
        self.write(
            prep_template_graph_get_req(prep_id, self.current_user.id))


class PrepTemplateJobHandler(BaseHandler):
    @authenticated
    def get(self, prep_id):
        self.write(prep_template_jobs_get_req(prep_id, self.current_user.id))
