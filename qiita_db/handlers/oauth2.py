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
            sql = sql.format("AND client_secret IS NULL")
        qdb.sql_connection.TRN.add(sql, sql_info)
        return qdb.sql_connection.TRN.execute_fetchlast()


class OauthBaseHandler(RequestHandler):
    def write_error(self, status_code, **kwargs):
        """Overriding the default write error in tornado RequestHandler"""
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

    def oauth_error(self, error_msg, error='invalid_request'):
        self.set_status(400)
        self.write({'error': error,
                    'error_description': error_msg})
        self.finish()

    def check_rate_limit(self, client_id, user):
        limit_key = '%s_%s_daily_limit' % (client_id, user)
        limiter = r_client.get(limit_key)
        if limiter is None:
            # Set limit to 5,000 requests per day
            r_client.setex(limit_key, 5000, 86400)
        else:
            r_client.decr(limit_key)
            if int(r_client.get(limit_key)) <= 0:
                return False
        return True

    def authenticate_header(self):
        """Authenticates the Authorization header token for a given call

        Returns
        -------
        bool
            Whether authentication succeded or failed
        user, optional
            If this key is attached to a user, the User object for the user
        """
        header = self.request.headers.get('Authorization', None)
        if header is None:
            self.oauth_error('Oauth2 error: invalid access token')
            return False
        token_info = header.split()
        if len(token_info) != 2 or token_info[0] != 'Bearer':
            self.oauth_error('Oauth2 error: invalid access token',
                             'invalid_grant')
            return False
        token = token_info[1]
        db_token = r_client.hgetall(token)
        if not db_token:
            # token has timed out or never existed
            self.oauth_error('Oauth2 error: token has timed out',
                             'invalid_grant')
            return False
        # Check daily rate limit for key if password style key
        user = db_token.get('user', None)
        if user:
            if self.check_rate_limit(db_token['client_id'], user):
                return True, qdb.user.User(user)
            else:
                self.oauth_error('Oauth2 error: daily request limit reached',
                                 'invalid_grant')
                return False
        else:
            return True


class TokenAuthHandler(OauthBaseHandler):
    def generate_access_token(self):
        """Creates the random alphanumeric token

        Returns
        -------
        str
            55 character random alphanumeric string
        """
        pool = ascii_letters + digits
        return ''.join((SystemRandom().choice(pool) for _ in range(55)))

    def set_token(self, token, client_id, user=None, timeout=3600):
        """Create the access token for the client on redis

        Parameters
        ----------
        token: str
            Random token string for authorization
        client_id : str
            Client that requested the token
        user : str, optional
            If password grant type requested, the user requesting the key.
        timeout : int
            The timeout, in seconds, for the token. Default 3600
        """
        r_client.hset(token, 'timestamp', datetime.datetime.now())
        r_client.hset(token, 'client_id', client_id)
        r_client.expire(token, timeout)
        if user:
            r_client.hset(token, 'user', user)
            # Check if client has access limit key, and if not, create it
            limit_key = '%s_%s_daily_limit' % (client_id, user)
            limiter = r_client.get(limit_key)
            if limiter is None:
                # Set limit to 5,000 requests per day
                r_client.setex(limit_key, 5000, 86400)

    def validate_client(self, client_id, client_secret):
        """Make sure client exists, then set the token and send it

        Parameters
        ----------
        client_id : str
            The client making the request
        client_secret : str
            The secret key for the client
        """
        if login_client(client_id, client_secret):
            token = self.generate_access_token()
            self.write({'access_token': token,
                        'token_type': 'Bearer',
                        'expires_in': '3600'})
            self.finish()
            self.set_token(token, client_id)
        else:
            self.oauth_error('Oauth2 error: invalid client information',
                             'invalid_client')

    def validate_resource_owner(self, username, password, client_id):
        """Make sure user and client exist, then set the token and send it

        Parameters
        ----------
        username : str
            The username to validate
        password : str
            The password for the username
        client_id : str
            The client making the request
        """
        try:
            qdb.user.User.login(username, password)
        except (IncorrectEmailError, IncorrectPasswordError,
                UnverifiedEmailError):
            self.oauth_error('Oauth2 error: invalid user information',
                             'invalid_client')
            return

        if login_client(client_id):
            token = self.generate_access_token()
            self.write({'access_token': token,
                        'token_type': 'Bearer',
                        'expires_in': '3600'})
            self.finish()
            self.set_token(token, client_id, user=username)
        else:
            self.oauth_error('Oauth2 error: invalid client information',
                             'invalid_client')

    def post(self):
        # first check for header version of sending auth, meaning client ID
        header = self.request.headers.get('Authorization', None)
        if header is not None:
            header_info = header.split()
            if header_info[0] != 'Basic':
                # Invalid Authorization header type for this page
                self.oauth_error('Oauth2 error: invalid token type')
                return

            # Get client information from the header and validate it
            grant_type = self.get_argument('grant_type', None)
            if grant_type != 'client':
                self.oauth_error('Oauth2 error: invalid grant_type')
                return
            try:
                client_id, client_secret = urlsafe_b64decode(
                    header_info[1]).split(':')
            except ValueError:
                # Split didn't work, so invalid information sent
                self.oauth_error('Oauth2 error: invalid base64 encoded info')
                return
            self.validate_client(client_id, client_secret)
            return

        # Otherwise, do eother password or client based authentication
        client_id = self.get_argument('client_id', None)
        grant_type = self.get_argument('grant_type', None)
        if grant_type == 'password':
            username = self.get_argument('username', None)
            password = self.get_argument('password', None)
            if not all([username, password, client_id]):
                self.oauth_error('Oauth2 error: missing user information')
            else:
                self.validate_resource_owner(username, password, client_id)

        elif grant_type == 'client':
            client_secret = self.get_argument('client_secret', None)
            if not all([client_id, client_secret]):
                self.oauth_error('Oauth2 error: missing client information')
                return
            self.validate_client(client_id, client_secret)
        else:
            self.oauth_error('Oauth2 error: invalid grant_type',
                             'unsupported_grant_type')
            return
