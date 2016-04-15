# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from tornado.web import HTTPError

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


class ArtifactFilepathsHandler(OauthBaseHandler):
    @authenticate_oauth
    def get(self, artifact_id):
        """Retrieves the filepath information of the given artifact

        Parameters
        ----------
        artifact_id : str
            The id of the artifact whose filepath information is being
            retrieved

        Returns
        -------
        dict
            Format:
            {'success': bool,
             'error': str,
             'filepaths': list of (str, str)}
            - success: whether the request is successful or not
            - error: in case that success is false, it contains the error msg
            - filepaths: the filepaths attached to the artifact and their
            filepath types
        """
        with qdb.sql_connection.TRN:
            artifact = _get_artifact(artifact_id)
            response = {
                'filepaths': [(fp, fp_type)
                              for _, fp, fp_type in artifact.filepaths]}

        self.write(response)

    @authenticate_oauth
    def patch(self, artifact_id):
        """Patches the filepaths of the artifact

        Parameter
        ---------
        artifact_id : str
            The id of the artifact whose filepaths information is being updated

        Returns
        -------
        dict
            Format:
            {'success': bool,
             'error': str}
            - success: whether the request is successful or not
            - error: in case that success is false, it contains the error msg
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


class ArtifactMappingHandler(OauthBaseHandler):
    @authenticate_oauth
    def get(self, artifact_id):
        """Retrieves the mapping file information of the given artifact

        Parameters
        ----------
        artifact_id : str
            The id of the artifact whose mapping file information is being
            retrieved

        Returns
        -------
        dict
            Format:
            {'success': bool,
             'error': str,
             'mapping': str}
             - success: whether the request is successful or not
             - error: in case that success is false, it contains the error msg
             - mapping: the filepath to the mapping file
        """
        with qdb.sql_connection.TRN:
            artifact = _get_artifact(artifact_id)
            # In the current system, we don't have any artifact that
            # is the result of two other artifacts, and there is no way
            # of generating such artifact. This operation will be
            # eventually supported, but in interest of time we are not
            # going to implement that here.
            prep_templates = artifact.prep_templates
            if len(prep_templates) > 1:
                raise NotImplementedError(
                    "Artifact %d has more than one prep template")

            fp = prep_templates[0].qiime_map_fp

            response = {'mapping': fp}

        self.write(response)


class ArtifactTypeHandler(OauthBaseHandler):
    @authenticate_oauth
    def get(self, artifact_id):
        """Retrieves the artifact type information of the given artifact

        Parameters
        ----------
        artifact_id : str
            The id of the artifact whose information is being retrieved

        Returns
        -------
        dict
            Format:
            {'success': bool,
             'error': str,
             'type': str}
            - success: whether the request is successful or not
            - error: in case that success is false, it contains the error msg
            - type: the artifact type
        """
        with qdb.sql_connection.TRN:
            artifact = _get_artifact(artifact_id)
            response = {'type': artifact.artifact_type}

        self.write(response)
