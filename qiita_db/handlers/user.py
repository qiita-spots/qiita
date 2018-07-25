# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

import qiita_db as qdb
from .oauth2 import OauthBaseHandler, authenticate_oauth
from .util import _get_instance


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
            user = _get_instance(qdb.user.User, email,
                                 'Error instantiating user')
            response = {'data': {'email': email, 'level': user.level,
                                 'password': user.password}}

            self.write(response)
