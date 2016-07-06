# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from tornado.web import HTTPError
from collections import defaultdict
from json import loads

import qiita_db as qdb
from .oauth2 import OauthBaseHandler, authenticate_oauth


def _get_artifact(a_id):
    """Returns the artifact with the given id if it exists

    Parameters
    ----------
    a_id : str
        The artifact id

    Returns
    -------
    qiita_db.artifact.Artifact
        The requested artifact

    Raises
    ------
    HTTPError
        If the artifact does not exist, with error code 404
        If there is a problem instantiating the artifact, with error code 500
    """
    try:
        a_id = int(a_id)
        artifact = qdb.artifact.Artifact(a_id)
    except qdb.exceptions.QiitaDBUnknownIDError:
        raise HTTPError(404)
    except Exception as e:
        raise HTTPError(500, 'Error instantiating artifact %s: %s'
                             % (a_id, str(e)))

    return artifact


class ArtifactHandler(OauthBaseHandler):
    @authenticate_oauth
    def get(self, artifact_id):
        """Retrieves the artifact information

        Parameters
        ----------
        artifact_id : str
            The id of the artifact whose information is being retrieved

        Returns
        -------
        dict
            The artifact information:
            'name': artifact name
            'timestamp': artifact creation timestamp
            'visibility': artifact visibility
            'type': artifact type
            'data_type': artifact data type
            'can_be_submitted_to_ebi': if the artifact can be submitted to ebi
            'ebi_run_accessions': dict with the EBI run accessions attached to
                the artifact
            'can_be_submitted_to_vamps': if the artifact can be submitted to
                vamps
            'is_submitted_to_vamps': whether the artifact has been submitted
                to vamps or not
            'prep_information': list of prep information ids
            'study': the study id
            'processing_parameters': dict with the processing parameters used
                to generate the artifact or None
            'files': dict with the artifact files, keyed by filepath type
        """
        with qdb.sql_connection.TRN:
            artifact = _get_artifact(artifact_id)
            response = {
                'name': artifact.name,
                'timestamp': str(artifact.timestamp),
                'visibility': artifact.visibility,
                'type': artifact.artifact_type,
                'data_type': artifact.data_type,
                'can_be_submitted_to_ebi': artifact.can_be_submitted_to_ebi,
                'can_be_submitted_to_vamps':
                    artifact.can_be_submitted_to_vamps,
                'prep_information': [p.id for p in artifact.prep_templates],
                'study': artifact.study.id}
            params = artifact.processing_parameters
            response['processing_parameters'] = (
                params.values if params is not None else None)

            response['ebi_run_accessions'] = (
                artifact.ebi_run_accessions
                if response['can_be_submitted_to_ebi'] else None)
            response['is_submitted_to_vamps'] = (
                artifact.is_submitted_to_vamps
                if response['can_be_submitted_to_vamps'] else None)

            # Instead of sending a list of files, provide the files as a
            # dictionary keyed by filepath type
            response['files'] = defaultdict(list)
            for _, fp, fp_type in artifact.filepaths:
                response['files'][fp_type].append(fp)

        self.write(response)

    @authenticate_oauth
    def patch(self, artifact_id):
        """Patches the artifact information

        Parameter
        ---------
        artifact_id : str
            The id of the artifact whose information is being updated
        """
        req_op = self.get_argument('op')
        req_path = self.get_argument('path')
        req_value = self.get_argument('value')

        if req_op == 'add':
            req_path = [v for v in req_path.split('/') if v]
            if len(req_path) != 1 or req_path[0] != 'html_summary':
                raise HTTPError(400, 'Incorrect path parameter value')
            else:
                artifact = _get_artifact(artifact_id)
                try:
                    artifact.html_summary_fp = req_value
                except Exception as e:
                    raise HTTPError(500, str(e))
        else:
            raise HTTPError(400, 'Operation "%s" not supported. Current '
                                 'supported operations: add' % req_op)

        self.finish()


class ArtifactAPItestHandler(OauthBaseHandler):
    @authenticate_oauth
    def post(self):
        """Creates a new artifact

        Parameters
        ----------
        filepahts : str
            Json string with a list of filepaths and its types
        type : str
            The artifact type
        prep_template: int
            The id of the template that the new artifact belongs to
        name : str, optional
            The artifact name

        Returns
        -------
        dict
            'artifact': the id of the new artifact

        See Also
        --------
        qiita_db.artifact.Artifact.create
        """
        filepaths = loads(self.get_argument('filepaths'))
        artifact_type = self.get_argument('type')
        prep_template = self.get_argument('prep')
        name = self.get_argument('name', None)

        if prep_template:
            prep_template = qdb.metadata_template.prep_template.PrepTemplate(
                prep_template)

        a = qdb.artifact.Artifact.create(
            filepaths, artifact_type, name=name, prep_template=prep_template)

        self.write({'artifact': a.id})
