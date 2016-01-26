# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from __future__ import division

from tornado.web import authenticated

from qiita_db.util import get_files_from_uploads_folders
from qiita_pet.handlers.util import to_int
from qiita_pet.handlers.base_handlers import BaseHandler
from qiita_pet.handlers.api_proxy import (
    artifact_graph_get_req, artifact_types_get_req)


class ArtifactGraphAJAX(BaseHandler):
    @authenticated
    def get(self):
        direction = self.get_argument('direction')
        artifact = to_int(self.get_argument('artifact_id'))
        self.write(artifact_graph_get_req(artifact, direction,
                                          self.current_user.id))


class NewArtifactHandler(BaseHandler):
    @authenticated
    def get(self, study_id):
        prep_files = [f for _, f in get_files_from_uploads_folders(study_id)
                      if f.endswith(('txt', 'tsv'))]
        types = artifact_types_get_req()['types']
        self.render("study_ajax/add_prep_artifact.html", prep_files=prep_files,
                    types=types, study_id=study_id)

    @authenticated
    def post(self, study_id):
        pass
