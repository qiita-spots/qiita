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
from qiita_core.qiita_settings import r_client

from qiita_core.exceptions import (IncorrectPasswordError, IncorrectEmailError,
                                   UnverifiedEmailError)
import qiita_db as qdb


def _oauth_error(handler, error_msg, error):
    """Set expected status and error formatting for Oauth2 style error

   Parameters
   ----------
   error_msg : str
        Human parsable error message
    error : str
        Oauth2 controlled vocab error

    Returns
    -------
    Writes out Oauth2 formatted error JSON of
        {error: error,
         error_description: error_msg}

    Notes
    -----
    Expects handler to be a tornado RequestHandler or subclass
    """
    handler.set_status(400)
    handler.write({'error': error,
                   'error_description': error_msg})
    handler.finish()


def _check_oauth2_header(handler):
    """Check if the oauth2 header is valid

    Parameters
    ----------
    handler : tornado.web.RequestHandler instance
        The handler instance being requested

    Returns
    -------
    errtype
        The type of error, None if no error was observed
    errdesc
        A description of the error, None if no error was observed.
    client_id
        The observed client ID. This field is None if any error was observed.
    """
    header = handler.request.headers.get('Authorization', None)

    if header is None:
        return ('invalid_request', 'Oauth2 error: invalid access token', None)

    token_info = header.split()
    # Based on RFC6750 if reply is not 2 elements in the format of:
    # ['Bearer', token] we assume a wrong reply
    if len(token_info) != 2 or token_info[0] != 'Bearer':
        return ('invalid_grant', 'Oauth2 error: invalid access token', None)

    token = token_info[1]
    db_token = r_client.hgetall(token)
    if not db_token:
        # token has timed out or never existed
        return ('invalid_grant', 'Oauth2 error: token has timed out', None)

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
                return ('invalid_grant',
                        'Oauth2 error: daily request limit reached', None)

    return (None, None, db_token['client_id'])


class authenticate_oauth2:
    """Decorate methods to require valid Oauth2 Authorization header[1]

    If a valid header is given, the handoff is done and the page is rendered.
    If an invalid header is given, a 400 error code is returned and the json
    error message is automatically sent.

    Attributes
    ----------
    default_public : bool
        If True, execute the handler if a) the oauth2 token is acceptable or
        b) if the Authorization header is not present. If False, the handler
        will only be executed if the oauth2 token is acceptable.
    inject_user : bool
        If True, monkey patch the handler's get_current_user method to return
        the instance of the User associated with the token's client ID. If
        False, get_current_user is not monkey patched. If default_public is
        also True, the default User returned is "demo@microbio.me"

    References
    ----------
    [1] The OAuth 2.0 Authorization Framework.
    http://tools.ietf.org/html/rfc6749
    """
    def __init__(self, default_public=False, inject_user=False):
        self.default_public = default_public
        self.inject_user = inject_user

    def get_user_maker(self, cid):
        """Produce a function which acts like get_current_user"""
        def f():
            if cid is None:
                return qdb.user.User("demo@microbio.me")
            else:
                return qdb.user.User.from_client_id(cid)
        return f

    def __call__(self, f):
        """Handle oauth, and execute the handler's method if appropriate

        Parameters
        ----------
        f : function
            The function decorated is expected to be a member method of a
            subclass of `Tornado.web.RequestHandler`

        Notes
        -----
        If an error with oauth2 occurs, a status code of 400 is set, a message
        about the error is sent out over `write` and the response is ended
        with `finish`. This happens without control being passed to the
        handler, and in this situation, the handler is not executed.
        """
        @functools.wraps(f)
        def wrapper(handler, *args, **kwargs):
            errtype, errdesc, cid = _check_oauth2_header(handler)

            if self.default_public:
                # no error, or no authorization header. We should error if
                # oauth is actually attempted but there was an auth issue
                # (e.g., rate limit hit)
                if errtype not in (None, 'invalid_request'):
                    _oauth_error(handler, errdesc, errtype)
                    return

                if self.inject_user:
                    handler.get_current_user = self.get_user_maker(cid)
            else:
                if errtype is not None:
                    _oauth_error(handler, errdesc, errtype)
                    return
                if self.inject_user:
                    if cid is None:
                        raise ValueError("cid is None, without an oauth "
                                         "error. This should never happen.")
                    else:
                        handler.get_current_user = self.get_user_maker(cid)

            return f(handler, *args, **kwargs)

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
        exc_info = kwargs['exc_info']

        # We don't need to log 403, 404 or 405 failures in the logging table
        if status_code not in {403, 404, 405}:
            # log the error
            error_lines = ['%s\n' % line
                           for line in format_exception(*exc_info)]
            trace_info = ''.join(error_lines)
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

        message = exc_info[1].message
        if hasattr(exc_info[1], 'log_message'):
            message = exc_info[1].log_message

        self.finish(message)

    def head(self):
        """Adds proper response for head requests"""
        self.finish()


class TokenAuthHandler(OauthBaseHandler):
    def generate_access_token(self, length=55):
        """Creates the random alphanumeric token

        Parameters
        ----------
        length : int, optional
            Length of token to generate. Default 55 characters.
            Can be a max of 255 characters, which is a hard HTTP transfer limit

        Returns
        -------
        str
            Random alphanumeric string of passed length

        Raises
        ------
        ValueError
            length is not between 1 and 255, inclusive
        """
        if not 0 < length < 256:
            raise ValueError("Invalid token length: %d" % length)

        pool = ascii_letters + digits
        return ''.join((SystemRandom().choice(pool) for _ in range(length)))

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

        Returns
        -------
        Writes token information JSON in the form expected by RFC6750:
        {'access_token': token,
         'token_type': 'Bearer',
         'expires_in': timeout}

         access_token: the actual token to use
         token_type: 'Bearer', which is the expected token type for Oauth2
         expires_in: time to token expiration, in seconds.
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
                    'expires_in': timeout})
        self.finish()

    def validate_client(self, client_id, client_secret):
        """Make sure client exists, then set the token and send it

        Parameters
        ----------
        client_id : str
            The client making the request
        client_secret : str
            The secret key for the client

        Returns
        -------
        Writes out Oauth2 formatted error JSON if error occured
            {error: error,
             error_description: error_msg}

        error: RFC6750 controlled vocabulary of errors
         error_description: Human readable explanation of error
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT EXISTS(
                        SELECT *
                        FROM qiita.oauth_identifiers
                        WHERE client_id = %s AND client_secret = %s)"""
            qdb.sql_connection.TRN.add(sql, [client_id, client_secret])
            if qdb.sql_connection.TRN.execute_fetchlast():
                self.set_token(client_id, 'client')
            else:
                _oauth_error(self, 'Oauth2 error: invalid client information',
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

        Returns
        -------
        Writes out Oauth2 formatted error JSON if error occured
            {error: error,
             error_description: error_msg}

        error: RFC6750 controlled vocabulary of errors
         error_description: Human readable explanation of error
        """
        try:
            qdb.user.User.login(username, password)
        except (IncorrectEmailError, IncorrectPasswordError,
                UnverifiedEmailError):
            _oauth_error(self, 'Oauth2 error: invalid user information',
                         'invalid_client')
            return

        with qdb.sql_connection.TRN:
            sql = """SELECT EXISTS(
                        SELECT *
                        FROM qiita.oauth_identifiers
                        WHERE client_id = %s AND client_secret IS NULL)"""
            qdb.sql_connection.TRN.add(sql, [client_id])
            if qdb.sql_connection.TRN.execute_fetchlast():
                self.set_token(client_id, 'password', user=username)
            else:
                _oauth_error(self, 'Oauth2 error: invalid client information',
                             'invalid_client')

    def post(self):
        """ Authenticate given information as per RFC6750

        Parameters
        ----------
        grant_type : {'client', 'password'}
            What type of token to grant
        client_id : str
            Client requesting the token

        One of the following, if password grant type:
        HTTP Header in the form
            Authorization: Bearer [base64encode of username:password]

        OR

        username : str
            Username to authenticate
        password : str
            Password for the username

        If client grant type:
        client_secret : str
            client authentication secret

        Returns
        -------
        Writes token information JSON in the form expected by RFC6750:
        {'access_token': token,
         'token_type': 'Bearer',
         'expires_in': timeout}

         access_token: the actual token to use
         token_type: 'Bearer', which is the expected token type for Oauth2
         expires_in: time to token expiration, in seconds.

         or an error message in the form
         {error: error,
         error_description: error_msg}

         error: RFC6750 controlled vocabulary of errors
         error_description: Human readable explanation of error
         """
        # first check for header version of sending auth, meaning client ID
        header = self.request.headers.get('Authorization', None)
        if header is not None:
            header_info = header.split()
            # Based on RFC6750 if reply is not 2 elements in the format of:
            # ['Basic', base64 encoded username:password] we assume the header
            # is invalid
            if len(header_info) != 2 or header_info[0] != 'Basic':
                # Invalid Authorization header type for this page
                _oauth_error(self, 'Oauth2 error: invalid token type',
                             'invalid_request')
                return

            # Get client information from the header and validate it
            grant_type = self.get_argument('grant_type', None)
            if grant_type != 'client':
                _oauth_error(self, 'Oauth2 error: invalid grant_type',
                             'invalid_request')
                return
            try:
                client_id, client_secret = urlsafe_b64decode(
                    header_info[1]).split(':')
            except ValueError:
                # Split didn't work, so invalid information sent
                _oauth_error(self, 'Oauth2 error: invalid base64 encoded info',
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
                _oauth_error(self, 'Oauth2 error: missing user information',
                             'invalid_request')
            else:
                self.validate_resource_owner(username, password, client_id)

        elif grant_type == 'client':
            client_secret = self.get_argument('client_secret', None)
            if not all([client_id, client_secret]):
                _oauth_error(self, 'Oauth2 error: missing client information',
                             'invalid_request')
                return
            self.validate_client(client_id, client_secret)
        else:
            _oauth_error(self, 'Oauth2 error: invalid grant_type',
                         'unsupported_grant_type')
            return
