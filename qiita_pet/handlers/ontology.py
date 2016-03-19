# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from tornado.web import authenticated

from qiita_pet.handlers.base_handlers import BaseHandler
from qiita_pet.handlers.api_proxy import ontology_patch_handler


class OntologyHandler(BaseHandler):
    @authenticated
    def patch(self):
        """Patches an ontology in the system

        Follows the JSON PATCH specification:
        https://tools.ietf.org/html/rfc6902
        """
        req_op = self.get_argument('op')
        req_path = self.get_argument('path')
        req_value = self.get_argument('value', None)
        req_from = self.get_argument('from', None)

        response = ontology_patch_handler(req_op, req_path, req_value,
                                          req_from)
        self.write(response)
