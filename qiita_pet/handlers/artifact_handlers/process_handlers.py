# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from tornado.web import authenticated

from qiita_pet.handlers.base_handlers import BaseHandler
from qiita_pet.handlers.util import to_int
from qiita_db.artifact import Artifact


def process_artifact_handler_get_req(artifact_id):
    """Returns the information for the process artifact handler

    Parameters
    ----------
    artifact_id : int
        The artifact to be processed

    Returns
    -------
    dict of str
        A dictionary containing the artifact information
        {'status': str,
         'message': str,
         'name': str,
         'type': str}
    """
    artifact = Artifact(artifact_id)

    return {'status': 'success',
            'message': '',
            'name': artifact.name,
            'type': artifact.artifact_type,
            'artifact_id': artifact.id,
            'allow_change_optionals': artifact.analysis is not None}


class ProcessArtifactHandler(BaseHandler):
    @authenticated
    def get(self, artifact_id):
        # Check if the user has access to the artifact
        artifact_id = to_int(artifact_id)
        res = process_artifact_handler_get_req(artifact_id)
        self.render('artifact_ajax/processing_artifact.html', **res)
