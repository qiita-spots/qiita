# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from .oauth2 import OauthBaseHandler, authenticate_oauth

import qiita_db as qdb


def _get_reference(r_id):
    """Returns the reference with the given id if exists

    Parameters
    ----------
    r_id : int
        The reference id

    Returns
    -------
    qiita_db.reference.Reference, bool, string
        The requested reference or None
        Whether if we could get the reference object or not
        Error message in case we counldn't get the reference object
    """
    try:
        reference = qdb.reference.Reference(r_id)
    except qdb.exceptions.QiitaDBUnknownIDError:
        return None, False, 'Reference does not exist'
    except qdb.exceptions.QiitaDBError as e:
        return None, False, 'Error instantiating the reference: %s' % str(e)

    return reference, True, ''


class ReferenceFilepathsHandler(OauthBaseHandler):
    @authenticate_oauth
    def get(self, reference_id):
        """Retrieves the filepath information of the given reference

        Parameters
        ----------
        reference_id : str
            The id of the reference whose filepath information is being
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
            - filepaths: the filepaths attached to the reference and their
            filepath types
        """
        with qdb.sql_connection.TRN:
            reference, success, error_msg = _get_reference(reference_id)
            fps = None
            if success:
                fps = [(reference.sequence_fp, "reference_seqs")]
                tax_fp = reference.taxonomy_fp
                if tax_fp:
                    fps.append((tax_fp, "reference_tax"))
                tree_fp = reference.tree_fp
                if tree_fp:
                    fps.append((tree_fp, "reference_tree"))

            response = {'success': success, 'error': error_msg,
                        'filepaths': fps}

        self.write(response)
