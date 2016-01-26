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
    artifact_graph_get_req, artifact_types_get_req, data_types_get_req,
    ena_ontology_get_req, prep_template_post_req, artifact_post_req)


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
        artifact_types = artifact_types_get_req()['types']
        data_types = sorted(data_types_get_req()['data_types'])
        ontology = ena_ontology_get_req()
        self.render("study_ajax/add_prep_artifact.html", prep_files=prep_files,
                    artifact_types=artifact_types, data_types=data_types,
                    ontology=ontology, study_id=study_id)

    @authenticated
    def post(self, study_id):
        study_id = int(study_id)
        name = self.get_argument('name')
        data_type = self.get_argument('data-type')
        ena_ontology = self.get_argument('ena-ontology', None)
        user_ontology = self.get_argument('user-ontology', None)
        new_ontology = self.get_argument('new-ontology', None)
        artifact_type = self.get_argument('type')
        prep_file = self.get_argument('prep-file')

        # Remove known columns, leaving just file types and files
        files = self.request.arguments
        for arg in ['name', 'data-type', 'ena-ontology', 'user-ontology',
                    'new-ontology', 'type', 'prep-file']:
            files.pop(arg, None)

        prep = prep_template_post_req(study_id, self.current_user.id,
                                      prep_file, data_type, ena_ontology,
                                      user_ontology, new_ontology)
        if prep['status'] != 'success':
            self.write(prep)
            return

        artifact = artifact_post_req(
            self.current_user.id, files, artifact_type, name, prep.id)
        if artifact['status'] == 'success':
            self.redirect('/study/description/%d' % study_id)
        else:
            self.write(prep)
