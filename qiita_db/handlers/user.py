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


def _get_user_info(email):
    """Returns the user information with the given `email` if it exists

    Parameters
    ----------
    email : str
        The user email

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
        user = qdb.user.User(email)
    except qdb.exceptions.QiitaDBUnknownIDError:
        raise HTTPError(404)
    except Exception as e:
        raise HTTPError(500, reason='Error instantiating user %s: %s' %
                        (email, str(e)))

    return user


class UserInfoDBHandler(OauthBaseHandler):
    @authenticate_oauth
    def get(self, email):
        """Retrieves the User information

        Parameters
        ----------
        email: str
            The email of the user whose information is being retrieved

        Returns
        -------
        dict
            The user information as a dict
        """
        with qdb.sql_connection.TRN:
            user = _get_user_info(email)
            response = {'data': {'email': email, 'level': user.level,
                                 'password': user.password}}

            self.write(response)
