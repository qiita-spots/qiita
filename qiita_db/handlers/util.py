# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from tornado.web import HTTPError

import qiita_db as qdb


def _get_instance(klass, oid, reason):
    """
    Returns the klass instance with the given `oid`

    Parameters
    ----------
    klass : class name
        The class name to instanciate
    oid : int/str
        The object id
    reason : str
        The failure reason we want to be displayed

    Returns
    -------
    qiita_db.user.User
        The requested user

    Raises
    ------
    HTTPError
        If the user does not exist, with error code 404
        If there is a problem instantiating, with error code 500
    """
    try:
        object = klass(oid)
    except qdb.exceptions.QiitaDBUnknownIDError:
        raise HTTPError(404)
    except Exception as e:
        raise HTTPError(500, reason=reason + ', id=%s: %s' % (oid, str(e)))

    return object
