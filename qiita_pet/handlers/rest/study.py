# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from qiita_db.study import Study
from qiita_db.exceptions import QiitaDBUnknownIDError
from qiita_db.handlers.oauth2 import authenticate_oauth
from qiita_pet.handlers.util import to_int
from qiita_pet.handlers.base_handlers import BaseHandler


class StudyHandler(BaseHandler):
    @authenticate_oauth
    def get(self, study_id):
        study_id = to_int(study_id)
        try:
            Study(study_id)
        except QiitaDBUnknownIDError:
            self.set_status(404)
            self.write({'message': 'Study not found'})
        finally:
            self.finish()
