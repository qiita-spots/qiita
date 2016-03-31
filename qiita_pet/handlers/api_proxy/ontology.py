# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from qiita_db.util import convert_to_id
from qiita_db.exceptions import QiitaDBLookupError
from qiita_db.ontology import Ontology


def ontology_patch_handler(req_op, req_path, req_value=None, req_from=None):
    """Patches an ontology

    Parameters
    ----------
    req_op : str
        The operation to perform on the ontology
    req_path : str
        The ontology to patch
    req_value : str, optional
        The value that needs to be modified
    req_from : str, optional
        The original path of the element

    Returns
    -------
    dict of {str: str}
        A dictionary of the form: {'status': str, 'message': str} in which
        status is the status of the request ('error' or 'success') and message
        is a human readable string with the error message in case that status
        is 'error'.
    """
    if req_op == 'add':
        req_path = [v for v in req_path.split('/') if v]
        if len(req_path) != 1:
            return {'status': 'error',
                    'message': 'Incorrect path parameter'}
        req_path = req_path[0]

        try:
            o_id = convert_to_id(req_path, 'ontology')
        except QiitaDBLookupError:
            return {'status': 'error',
                    'message': 'Ontology "%s" does not exist' % req_path}

        ontology = Ontology(o_id)
        ontology.add_user_defined_term(req_value)

        return {'status': 'success',
                'message': ''}
    else:
        return {'status': 'error',
                'message': 'Operation "%s" not supported. '
                           'Current supported operations: add' % req_op}
