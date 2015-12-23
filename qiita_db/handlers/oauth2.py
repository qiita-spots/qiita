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
import functools
from traceback import format_exception

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
                    WHERE client_id = %s {0})"""
        sql_info = [client_id]
        if client_secret is not None:
            sql = sql.format("AND client_secret = %s")
            sql_info.append(client_secret)
        else:
            sql = sql.format("AND client_secret IS NULL")
        qdb.sql_connection.TRN.add(sql, sql_info)
        return qdb.sql_connection.TRN.execute_fetchlast()


def _oauth_error(self, error_msg, error):
            self.set_status(400)
            self.write({'error': error,
                        'error_description': error_msg})
            self.finish()


def authenticate_oauth(f):
    """Decorate methods to require valid Oauth2 Authorization header[1]

    If a valid header is given, the handoff is done and the page is rendered.
    If an invalid header is given, a 400 error code is returned and the json
    error message is automatically sent.

    References
    ---------
    [1] The OAuth 2.0 Authorization Framework.
    http://tools.ietf.org/html/rfc6749
    """
    @functools.wraps(f)
    def wrapper(self, *args, **kwargs):
        header = self.request.headers.get('Authorization', None)
        if header is None:
            _oauth_error(self, 'Oauth2 error: invalid access token',
                         'invalid_request')
            return
        token_info = header.split()
        if len(token_info) != 2 or token_info[0] != 'Bearer':
            _oauth_error(self, 'Oauth2 error: invalid access token',
                         'invalid_grant')
            return

        token = token_info[1]
        db_token = r_client.hgetall(token)
        if not db_token:
            # token has timed out or never existed
            _oauth_error(self, 'Oauth2 error: token has timed out',
                         'invalid_grant')
            return
        # Check daily rate limit for key if password style key
        if db_token['grant_type'] == 'password':
            limit_key = '%s_%s_daily_limit' % (db_token['client_id'],
                                               db_token['user'])
            limiter = r_client.get(limit_key)
            if limiter is None:
                # Set limit to 5,000 requests per day
                r_client.setex(limit_key, 5000, 86400)
            else:
                r_client.decr(limit_key)
                if int(r_client.get(limit_key)) <= 0:
                    _oauth_error(
                        self, 'Oauth2 error: daily request limit reached',
                        'invalid_grant')
                    return

        return f(self, *args, **kwargs)
    return wrapper


class OauthBaseHandler(RequestHandler):
    def write_error(self, status_code, **kwargs):
        """Overriding the default write error in tornado RequestHandler

        Instead of writing all errors to stderr, this writes them to the logger
        tables.

        Parameters
        ----------
        status_code : int
            HTML status code of the error
        **kwargs : dict
            Other parameters describing the error

        Notes
        -----
        This function is automatically called by the tornado package on errors,
        and should never be called directly.
        """
        if status_code in {403, 404, 405}:
            # We don't need to log these failues in the logging table
            return
        # log the error
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

    # Allow call to oauth_error function as part of the class
    oauth_error = _oauth_error

    def head(self):
        """Adds proper response for head requests"""
        self.finish()


class TokenAuthHandler(OauthBaseHandler):
    def generate_access_token(self):
        """Creates the random alphanumeric token

        Returns
        -------
        str
            55 character random alphanumeric string

        Notes
        -----
        55 was chosen as a cryptographically secure limit that needs to be
        hard coded so we can set the same varchar length for the postgres
        column storing the key.
        """
        pool = ascii_letters + digits
        return ''.join((SystemRandom().choice(pool) for _ in range(55)))

    def set_token(self, client_id, grant_type, user=None, timeout=3600):
        """Create access token for the client on redis and send json response

        Parameters
        ----------
        client_id : str
            Client that requested the token
        grant_type : str
            Type of key being requested
        user : str, optional
            If password grant type requested, the user requesting the key.
        timeout : int, optional
            The timeout, in seconds, for the token. Default 3600
        """
        token = self.generate_access_token()

        r_client.hset(token, 'timestamp', datetime.datetime.now())
        r_client.hset(token, 'client_id', client_id)
        r_client.hset(token, 'grant_type', grant_type)
        r_client.expire(token, timeout)
        if user:
            r_client.hset(token, 'user', user)
        if grant_type == 'password':
            # Check if client has access limit key, and if not, create it
            limit_key = '%s_%s_daily_limit' % (client_id, user)
            limiter = r_client.get(limit_key)
            if limiter is None:
                # Set limit to 5,000 requests per day
                r_client.setex(limit_key, 5000, 86400)

        self.write({'access_token': token,
                    'token_type': 'Bearer',
                    'expires_in': '3600'})
        self.finish()

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
            self.set_token(client_id, 'client')
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
            self.set_token(client_id, 'password', user=username)
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
                self.oauth_error('Oauth2 error: invalid token type',
                                 'invalid_request')
                return

            # Get client information from the header and validate it
            grant_type = self.get_argument('grant_type', None)
            if grant_type != 'client':
                self.oauth_error('Oauth2 error: invalid grant_type',
                                 'invalid_request')
                return
            try:
                client_id, client_secret = urlsafe_b64decode(
                    header_info[1]).split(':')
            except ValueError:
                # Split didn't work, so invalid information sent
                self.oauth_error('Oauth2 error: invalid base64 encoded info',
                                 'invalid_request')
                return
            self.validate_client(client_id, client_secret)
            return

        # Otherwise, do either password or client based authentication
        client_id = self.get_argument('client_id', None)
        grant_type = self.get_argument('grant_type', None)
        if grant_type == 'password':
            username = self.get_argument('username', None)
            password = self.get_argument('password', None)
            if not all([username, password, client_id]):
                self.oauth_error('Oauth2 error: missing user information',
                                 'invalid_request')
            else:
                self.validate_resource_owner(username, password, client_id)

        elif grant_type == 'client':
            client_secret = self.get_argument('client_secret', None)
            if not all([client_id, client_secret]):
                self.oauth_error('Oauth2 error: missing client information',
                                 'invalid_request')
                return
            self.validate_client(client_id, client_secret)
        else:
            self.oauth_error('Oauth2 error: invalid grant_type',
                             'unsupported_grant_type')
            return
