# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from qiita_pet.handlers.base_handler import BaseHandler

class StudyHandler(BaseHandler):
    def get(self, id):

        self.set_status(404)
        self.write({'message': 'Study not found'})
        self.finish()
