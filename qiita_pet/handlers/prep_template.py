# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from tornado.web import authenticated

from qiita_pet.handlers.base_handlers import BaseHandler
from qiita_pet.handlers.api_proxy import prep_template_post_req


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
