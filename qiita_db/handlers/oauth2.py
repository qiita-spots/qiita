# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from base64 import urlsafe_b64decode
from string import ascii_letters, digits
import datetime
from random import SystemRandom

from tornado.web import RequestHandler

from moi import r_client
from qiita_core.exceptions import (IncorrectPasswordError, IncorrectEmailError,
                                   UnverifiedEmailError)
import qiita_db as qdb


def login_client(client_id, client_secret=None):
    """Login client_id, optionally with client_secret

    Parameters
    ----------
    client_id : str
        The client ID to validate
    client_secret : str, optional
        The client secret code. If not given, will only validate if client_id
        exists

    Returns
    -------
    bool
        Whether client_id exists and, if client_secret given, the secret
        matches the id
    """
    with qdb.sql_connection.TRN:
        sql = """SELECT EXISTS(
                    SELECT *
                    FROM qiita.oauth_identifiers
                    WHERE client_id = %s{0})"""
        sql_info = [client_id]
        if client_secret is not None:
            sql = sql.format("AND client_secret = %s")
            sql_info.append(client_secret)
        else:
            sql = sql.format("")
        qdb.sql_connection.TRN.add(sql, sql_info)
        return qdb.sql_connection.TRN.execute_fetchlast()


class OauthBaseHandler(RequestHandler):
    def write_error(self, status_code, **kwargs):
        if status_code in {403, 404, 405}:
            # We don't need to log these failues in the logging table
            return
        # log the error
        from traceback import format_exception
        exc_info = kwargs['exc_info']
        trace_info = ''.join(['%s\n' % line for line in
                             format_exception(*exc_info)])
        req_dict = self.request.__dict__
        # must trim body to 1024 chars to prevent huge error messages
        req_dict['body'] = req_dict.get('body', '')[:1024]
        request_info = ''.join(['<strong>%s</strong>: %s\n' %
                               (k, req_dict[k]) for k in
                                req_dict.keys() if k != 'files'])
        error = exc_info[1]
        qdb.logger.LogEntry.create(
            'Runtime',
            'ERROR:\n%s\nTRACE:\n%s\nHTTP INFO:\n%s\n' %
            (error, trace_info, request_info))

    def head(self):
        """Adds proper response for head requests"""
        self.finish()

    def authenticate_header(self):
        """Authenticates the Authorization header token for a given call

        Returns
        -------
        bool
            Whether authentication succeded or failed
        user, optional
            If this key is attached to a user, the User object for the user
        """
        token = self.request.headers('Authorization', None)
        if token is None:
            return False
        token_info = token.split(token)
        if len(token_info) != 2 or token_info[0] != 'Bearer':
                return False
        db_token = r_client.hget(token, 'timestamp')
        if db_token is None:
            # token has timed out
            return False
        user = r_client.hget(token, 'user')
        if user:
            return True, qdb.user.User(user)
        else:
            return True


class TokenAuthHandler(OauthBaseHandler):
    def generate_access_token(self):
        pool = ascii_letters + digits
        return ''.join((SystemRandom().choice(pool) for _ in range(55)))

    def set_token(self, token, user=None, timeout=3600):
        r_client.hset(token, 'timestamp', datetime.datetime.now())
        r_client.expire(token, timeout)
        if user:
            r_client.hset(token, 'user', user)

    def validate_client(self, client_id, client_secret):
        if login_client(client_id, client_secret):
            token = self.generate_access_token()
            self.write({'access_token': token,
                        'token_type': 'Bearer',
                        'expires_in': '3600'})
            self.finish()
            self.set_token(token)
        else:
            self.write({'error': 'Invalid request'})
            self.finish()

    def validate_resource_owner(self, username, password, client_id):
        try:
            qdb.user.User.login(username, password)
        except (IncorrectEmailError, IncorrectPasswordError,
                UnverifiedEmailError):
            self.write({'error': 'Invalid request'})
            self.finish()
            return

        if login_client(client_id):
            token = self.generate_access_token()
            self.write({'access_token': token,
                        'token_type': 'Bearer',
                        'expires_in': '3600'})
            self.finish()
            self.set_token(token, user=username)
        else:
            self.write({'error': 'Invalid request'})
            self.finish()

    def post(self):
        # first check for header version of sending auth, meaning client ID
        header = self.request.headers.get('Authorization', None)
        if header is not None:
            header_info = header.split()
            if header_info[0] != 'Basic':
                # Invalid Authorization header type for this page
                self.write({'error': 'Invalid request'})
                self.finish()
                return

            # Get client information from the header and validate it
            grant_type = self.get_argument('grant_type', None)
            if grant_type != 'client':
                self.write({'error': 'Invalid request'})
                self.finish()
                return
            try:
                client_id, client_secret = urlsafe_b64decode(
                    header_info[1]).split(':')
            except ValueError:
                # Split didn't work, so invalid information sent
                self.write({'error': 'Invalid request'})
                self.finish()
                return
            self.validate_client(client_id, client_secret)
            return

        # Otherwise, do eother password or client based authentication
        client_id = self.get_argument('client_id', None)
        grant_type = self.get_argument('grant_type', None)
        if grant_type == 'password':
            username = self.get_argument('username', None)
            password = self.get_argument('password', None)
            if not all(username, password, client_id):
                self.write({'error': 'Invalid request'})
                self.finish()
            else:
                self.validate_resource_owner(client_id, client_secret)

        elif grant_type == 'client':
            client_secret = self.get_argument('client_secret', None)
            if not all([client_id, client_secret]):
                self.write({'error': 'Invalid request'})
                self.finish()
                return
            self.validate_client(client_id, client_secret)
        else:
            self.write({'error': 'Invalid request'})
