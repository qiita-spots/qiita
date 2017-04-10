# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from tornado.escape import json_encode
from tornado.web import MissingArgumentError

from qiita_db.handlers.oauth2 import authenticate_oauth
from qiita_db.study import StudyPerson
from qiita_db.exceptions import QiitaDBLookupError
from .rest_handler import RESTHandler


class StudyPersonHandler(RESTHandler):
    @authenticate_oauth
    def get(self, *args, **kwargs):
        name = self.get_argument('name', None)
        affiliation = self.get_argument('affiliation', None)

        if name is None and affiliation is None:
            # Retrieve the list of all the StudyPerson
            sp = [{'name': p.name, 'affiliation': p.affiliation}
                  for p in StudyPerson.iter()]
            self.write(json_encode(sp))
            self.finish()
        elif name is not None and affiliation is not None:
            try:
                p = StudyPerson.from_name_and_affiliation(name, affiliation)
            except QiitaDBLookupError:
                self.fail('Person not found', 404)
                return
            self.write({'address': p.address, 'phone': p.phone,
                        'email': p.email, 'id': p.id})
            self.finish()
        else:
            arg_name = 'name' if name is None else 'affiliation'
            raise MissingArgumentError(arg_name)

    @authenticate_oauth
    def post(self, *args, **kwargs):
        name = self.get_argument('name')
        affiliation = self.get_argument('affiliation')
        email = self.get_argument('email')

        phone = self.get_argument('phone', None)
        address = self.get_argument('address', None)

        if StudyPerson.exists(name, affiliation):
            self.fail('Person already exists', 409)
            return

        p = StudyPerson.create(name=name, affiliation=affiliation, email=email,
                               phone=phone, address=address)

        self.set_status(201)
        self.write({'id': p.id})
        self.finish()
