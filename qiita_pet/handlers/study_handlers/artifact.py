# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from __future__ import division

from tornado.web import authenticated


from qiita_pet.handlers.util import to_int
from qiita_pet.handlers.base_handlers import BaseHandler
from qiita_pet.handlers.api_proxy import (
    artifact_graph_get_req, artifact_types_get_req, artifact_post_req,
    artifact_status_put_req, artifact_get_req, artifact_get_prep_req,
    artifact_get_info)
from qiita_core.util import execute_as_transaction
from qiita_core.qiita_settings import qiita_config


class ArtifactGraphAJAX(BaseHandler):
    @authenticated
    def get(self):
        direction = self.get_argument('direction')
        artifact = to_int(self.get_argument('artifact_id'))
        self.write(artifact_graph_get_req(artifact, direction,
                                          self.current_user.id))


class NewArtifactHandler(BaseHandler):
    @authenticated
    def get(self):
        study_id = self.get_argument("study_id")
        prep_id = self.get_argument("prep_template_id")
        artifact_types = [(at, desc) for at, desc, _, _, raw in
                          artifact_types_get_req()['types'] if raw]

        self.render("study_ajax/add_artifact.html",
                    study_id=study_id, prep_id=prep_id,
                    artifact_types=artifact_types)

    @authenticated
    @execute_as_transaction
    def post(self):
        artifact_type = self.get_argument('artifact-type')
        name = self.get_argument('name')
        prep_id = self.get_argument('prep-template-id')
        artifact_id = self.get_argument('import-artifact')

        # Request the rest of the arguments, which will be the files
        files = {arg: self.get_argument(arg) for arg in self.request.arguments
                 if arg not in ['name', 'prep-template-id', 'artifact-type',
                                'import-artifact']}

        artifact = artifact_post_req(
            self.current_user.id, files, artifact_type, name, prep_id,
            artifact_id)
        self.write(artifact)


class ArtifactGetSamples(BaseHandler):
    @authenticated
    def get(self):
        aids = map(int, self.request.arguments.get('ids[]', []))

        response = artifact_get_prep_req(self.current_user.id, aids)

        self.write(response)


class ArtifactGetInfo(BaseHandler):
    @authenticated
    def get(self):
        aids = map(int, self.request.arguments.get('ids[]', []))
        only_biom = self.get_argument('only_biom', 'True') == 'True'

        response = artifact_get_info(self.current_user.id, aids, only_biom)

        self.write(response)


class ArtifactAdminAJAX(BaseHandler):
    @authenticated
    def get(self):
        artifact_id = to_int(self.get_argument('artifact_id'))
        info = artifact_get_req(self.current_user.id, artifact_id)
        status = info['visibility']
        buttons = []

        btn_base = ('<button onclick="set_admin_visibility(\'%s\', {0})" '
                    'class="btn btn-primary">%s</button>').format(artifact_id)

        if qiita_config.require_approval:
            if status == 'sandbox':
                # The request approval button only appears if the processed
                # data issandboxed and the qiita_config specifies that the
                # approval should be requested
                buttons.append(
                    btn_base % ('awaiting_approval', 'Request approval'))
            elif self.current_user.level == 'admin' and \
                    status == 'awaiting_approval':
                # The approve processed data button only appears if the user is
                # an admin, the processed data is waiting to be approved and
                # the qiita config requires processed data approval
                buttons.append(btn_base % ('private', 'Approve artifact'))
        if status == 'private':
            # The make public button only appears if the status is private
            buttons.append(btn_base % ('public', 'Make public'))

        # The revert to sandbox button only appears if the processed data is
        # not sandboxed or public
        if status not in {'sandbox', 'public'}:
            buttons.append(btn_base % ('sandbox', 'Revert to sandbox'))

        # Add EBI and VAMPS submission buttons if allowed
        if not info['ebi_run_accessions'] and info['can_submit_ebi']:
            buttons.append('<a class="btn btn-primary glyphicon '
                           'glyphicon-export" href="/ebi_submission/{{ppd_id}}'
                           '" style="word-spacing: -10px;"> Submit to EBI</a>')
        if not info['is_submitted_vamps'] and \
                info['can_submit_vamps']:
            buttons.append('<a class="btn btn-primary glyphicon '
                           'glyphicon-export" href="/vamps/{{ppd_id}}" '
                           'style="word-spacing: -10px;"> Submit to VAMPS</a>')
        # Add delete button if in sandbox status
        if status == 'sandbox':
            buttons = ['<button class="btn btn-danger" '
                       'onclick="delete_artifact(%d)">Delete Artifact</button>'
                       % (artifact_id)]

        self.write(' '.join(buttons))

    @authenticated
    def post(self):
        visibility = self.get_argument('visibility')
        artifact_id = int(self.get_argument('artifact_id'))
        response = artifact_status_put_req(artifact_id, self.current_user.id,
                                           visibility)
        self.write(response)
