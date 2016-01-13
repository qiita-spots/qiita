# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

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
    qiita_db.artifact.Artifact, bool, string
        The requested artifact or None
        Whether if we could get the artifact or not
        Error message in case we couldn't get the artifact
    """
    try:
        artifact = qdb.artifact.Artifact(a_id)
    except qdb.exceptions.QiitaDBUnknownIDError:
        return None, False, 'Artifact does not exist'
    except qdb.exceptions.QiitaDBError as e:
        return None, False, 'Error instantiating the artifact: %s' % str(e)

    return artifact, True, ''


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
            artifact, success, error_msg = _get_artifact(artifact_id)
            fps = None
            if success:
                fps = [(fp, fp_type) for _, fp, fp_type in artifact.filepaths]

            response = {'success': success, 'error': error_msg,
                        'filepaths': fps}

        self.write(response)


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
            artifact, success, error_msg = _get_artifact(artifact_id)
            fp = None
            if success:
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

            response = {'success': success, 'error': error_msg,
                        'mapping': fp}

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
            artifact, success, error_msg = _get_artifact(artifact_id)
            atype = None
            if success:
                atype = artifact.artifact_type

            response = {'success': success, 'error': error_msg,
                        'type': atype}

        self.write(response)
