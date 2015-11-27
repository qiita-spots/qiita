# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from tornado.web import RequestHandler

import qiita_db as qdb


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
        Whether if we could get the job or not
        Error message in case we couldn't get the job
    """
    try:
        artifact = qdb.artifact.Artifact(a_id)
    except qdb.exceptions.QiitaDBUnknownIDError:
        return None, False, 'Artifact does not exist'
    except qdb.exceptions.QiitaDBError as e:
        return None, False, 'Error instantiating the artifact: %s' % str(e)

    return artifact, True, ''


class ArtifactFilepathsHandler(RequestHandler):
    def get(self, artifact_id):
        """Retrieves the filepath information of the given artifact

        Parameters
        ----------
        artifact_id : str
            the id of the artifact that the information needs to be returned

        Returns
        -------
        dict
            Format:
            {'success': bool,
             'error': bool,
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
