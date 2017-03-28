# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

import pandas as pd

from tornado.escape import json_encode, json_decode

from qiita_db.metadata_template.prep_template import PrepTemplate
from qiita_db.handlers.oauth2 import authenticate_oauth
from .rest_handler import RESTHandler


class StudyPrepCreatorHandler(RESTHandler):
    # /api/v1/study/<int>/preparation/
    # TODO: do something smart about warnings, perhaps this should go in its
    # own endpoint i.e. /api/v1/study/<int>/preparation/validate

    @authenticate_oauth
    def post(self, study_id, *args, **kwargs):
        data_type = self.get_argument('data_type')
        investigation_type = self.get_argument('investigation_type', None)

        study_id = self.study_boilerplate(study_id)

        data = pd.DataFrame.from_dict(json_decode(self.request.body),
                                      orient='index')

        try:
            p = PrepTemplate.create(data, study_id, data_type,
                                    investigation_type)
        except Exception as e:
            self.write(json_encode({'message': e.message}))
            self.set_status(406)
            self.finish()
            return

        self.write({'id': p.id})
        self.set_status(200)
        self.finish()

class StudyPrepArtifactCreatorHandler(RESTHandler):
    pass

# POST /api/v1/study/<int>/preparation/<int>/artifact

