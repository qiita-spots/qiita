# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from tornado.escape import json_encode

from qiita_db.handlers.oauth2 import authenticate_oauth
from qiita_db.study import StudyPerson
from qiita_db.exceptions import QiitaDBLookupError
from .rest_handler import RESTHandler


class StudyPersonHandler(RESTHandler):
    def get(self, *args, **kwargs):
        name = self.get_argument('name')
        affiliation = self.get_argument('affiliation')

        try:
            p = StudyPerson.from_name_and_affiliation(name, affiliation)
        except QiitaDBLookupError:
            self.set_status(404)
            self.write({'message': 'Person not found'})
            self.finish()
            return

        self.write({'address': p.address, 'phone': p.phone, 'email': p.email,
                    'id': p.id})
        self.finish()

    # @authenticate_oauth
    def post(self, *args, **kwargs):
        name = self.get_argument('name')
        affiliation = self.get_argument('affiliation')
        email = self.get_argument('email')

        phone = self.get_argument('phone', None)
        address = self.get_argument('address', None)

        if StudyPerson.exists(name, affiliation):
            self.set_status(409)
            self.write({'message': 'Person already exists'})
            self.finish()
            return

        p = StudyPerson.create(name=name, affiliation=affiliation, email=email,
                               phone=phone, address=address)

        self.write({'id': p.id})
        self.finish()

