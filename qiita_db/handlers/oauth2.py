from base64 import b64decode
from string import ascii_letters, digits
from random import SystemRandom
from tornado.web import RequestHandler
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
             sql.format("AND client_secret = %s")
             sql_info.append(client_secret)
        else:
            sql.format("")
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
        """
        token = self.request.headers('Authorization', None)
        if token is None:
            return False
        token_info = token.split(token, maxsplit=1)
        if len(token_info) != 2 or token_info[0] != 'Bearer':
                return False
        raise NotImplementedError("validate the token!")


class TokenAuthHandler(OauthBaseHandler):
    def generate_access_token():
        pool = ascii_letters + digits
        return ''.join((SystemRandom().choice(pool) for _ in range(55)))

    def validate_client(self, client_id, client_secret=None):
        if login_client(client_id, client_secret):
            token = self.generate_access_token()
            self.write({'access_token': token,
                        'token_type': 'Bearer',
                        'expires_in': '3600'})
            raise NotImplementedError('Store token with timeout somewhere')
        else:
            self.write({'error': 'Invalid request'})

    def validate_resource_owner(self, username, password, client_id):
        try:
            qdb.user.User.login(username, password)
        except (IncorrectEmailError, IncorrectPasswordError,
                UnverifiedEmailError):
            self.write({'error': 'Invalid request'})

        self.validate_client(client_id)

    def post(self):
        # first check for header version of sending auth, meaning client ID
        header = self.request.headers.get('Authorization', None)
        if header is not None:
            header_info = header.split(header, maxsplit=1)
            if header_info[0] != 'Basic':
                # Invalid Authorization header type for this page
                self.write({'error': 'Invalid request'})
                return

            # Get client information from the header and validate it
            try:
                client_id, client_secret = b64decode(header_info[1]).split(
                    ':', maxsplit=1)
            except ValueError:
                # Split didn't work, so invalid information sent
                self.write({'error': 'Invalid request'})
                return
            self.validate_client(client_id, client_secret)

        # Otherwise, do eother password or client based authentication
        client_id = self.get_argument('client_id', None)
        grant_type = self.get_argument('grant_type', None)
        if grant_type == 'password':
            username = self.get_argument('username', None)
            password = self.get_argument('password', None)
            if not all(username, password, client_id):
                self.write({'error': 'Invalid request'})
            else:
                self.validate_resource_owner(client_id, client_secret)

        elif grant_type == 'client':
            client_secret = self.get_argument('client_secret', None)
            if not all(client_id, client_secret):
                self.write({'error': 'Invalid request'})
            else:
                self.validate_client(client_id, client_secret)
        else:
            self.write({'error': 'Invalid request'})
