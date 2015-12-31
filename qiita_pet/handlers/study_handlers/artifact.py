# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from __future__ import division

from tornado.web import authenticated

from qiita_core.qiita_settings import qiita_config
from qiita_pet.handlers.util import to_int
from qiita_pet.handlers.base_handlers import BaseHandler
from qiita_pet.handlers.api_proxy import (artifact_status_put_req,
                                          artifact_get_req,
                                          artifact_delete_req)


class ArtifactGraphAJAX(BaseHandler):
    @authenticated
    def get(self):
        direction = self.get_argument('direction')
        artifact = to_int(self.get_argument('artifact_id'))
        self.write(self.artifact_graph_proxy(artifact, direction))


class ArtifactAJAX(BaseHandler):
    def get(self):
        artifact_id = to_int(self.get_argument('artifact_id'))
        self.write('TITLE FOR ARTIFACT %d' % artifact_id)

    def post(self):
        artifact_id = to_int(self.get_argument('artifact_id'))
        self.write(artifact_delete_req(artifact_id, self.current_user.id))


class ArtifactAdminAJAX(BaseHandler):
    def get(self):
        artifact_id = to_int(self.get_argument('artifact_id'))
        info = artifact_get_req(artifact_id, self.current_user.id)
        status = info['visibility']
        buttons = []

        btn_base = ('<button onclick="set_admin_visibility(\'%s\', {0})" '
                    'class="btn btn-primary">%s</button>').format(artifact_id)

        if all([status == 'sandbox', qiita_config.require_approval]):
            # The request approval button only appears if the processed data is
            # sandboxed and the qiita_config specifies that the approval should
            # be requested
            buttons.append(
                btn_base % ('awaiting_approval', 'Request approval'))
        elif all([self.current_user.level == 'admin',
                  status == 'awaiting_approval',
                  qiita_config.require_approval]):
            # The approve processed data button only appears if the user is an
            # admin, the processed data is waiting to be approved and the qiita
            # config requires processed data approval
            buttons.append(btn_base % ('private', 'Approve artifact'))
        elif status == 'private':
            # The make public button only appears if the status is private
            buttons.append(btn_base % ('public', 'Make public'))

        # The revert to sandbox button only appears if the processed data is
        # not sandboxed or public
        if status not in {'sandbox', 'public'}:
            buttons.append(btn_base % ('sandbox', 'Revert to sandbox'))

        # Add EBI and VAMPS submission buttons if allowed
        if all([not info['ebi_run_accessions'],
                info['can_be_submitted_to_ebi']]):
            buttons.append('<a class="btn btn-primary glyphicon '
                           'glyphicon-export" href="/ebi_submission/{{ppd_id}}'
                           '" style="word-spacing: -10px;"> Submit to EBI</a>')
        if all([not info['is_submitted_to_vamps'],
                info['can_be_submitted_to_vamps']]):
            buttons.append('<a class="btn btn-primary glyphicon '
                           'glyphicon-export" href="/vamps/{{ppd_id}}" '
                           'style="word-spacing: -10px;"> Submit to VAMPS</a>')
        # Add delete button if in sandbox status
        if status == 'sandbox':
            buttons = ['<button class="btn btn-danger" '
                       'onclick="delete_artifact(%d)">Delete Artifact</button>'
                       % (artifact_id)]

        self.write(' '.join(buttons))

    def post(self):
        visibility = self.get_argument('visibility')
        artifact_id = int(self.get_argument('artifact_id'))
        response = artifact_status_put_req(artifact_id, self.current_user.id,
                                           visibility)
        self.write(response)
