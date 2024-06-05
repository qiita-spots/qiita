# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

import urllib.parse
import os
import requests

from tornado.escape import url_escape, json_encode, json_decode
from tornado.auth import OAuth2Mixin
from tornado.curl_httpclient import CurlAsyncHTTPClient
from tornado.web import HTTPError
from tornado.httpclient import HTTPClientError

from qiita_pet.handlers.base_handlers import BaseHandler
from qiita_core.qiita_settings import qiita_config, r_client
from qiita_core.util import execute_as_transaction
from qiita_core.exceptions import (IncorrectPasswordError, IncorrectEmailError,
                                   UnverifiedEmailError)
from qiita_db.util import send_email
from qiita_db.user import User
from qiita_db.exceptions import (QiitaDBUnknownIDError, QiitaDBDuplicateError,
                                 QiitaDBError)
from qiita_db.logger import LogEntry
# login code modified from https://gist.github.com/guillaumevincent/4771570


class AuthCreateHandler(BaseHandler):
    """User Creation"""
    def get(self):
        try:
            error_message = self.get_argument("error")
        # Tornado can raise an Exception directly, not a defined type
        except Exception:
            error_message = ""
        self.render("create_user.html", error=error_message)

    @execute_as_transaction
    def post(self):
        username = self.get_argument("email", "").strip().lower()
        password = self.get_argument("newpass", "")
        info = {}
        for info_column in ("name", "affiliation", "address", "phone"):
            hold = self.get_argument(info_column, None)
            if hold:
                info[info_column] = hold

        created = False
        try:
            created = User.create(username, password, info)
        except QiitaDBDuplicateError:
            msg = "Email already registered as a user"

        if created:
            info = created.info
            try:
                # qiita_config.base_url doesn't have a / at the end, but the
                # qiita_config.portal_dir has it at the beginning but not at
                # the end. This constructs the correct URL
                url = qiita_config.base_url + qiita_config.portal_dir
                send_email(username, "QIITA: Verify Email Address", "Please "
                           "click the following link to verify email address: "
                           "%s/auth/verify/%s?email=%s\n\nBy clicking you are "
                           "accepting our term and conditions: "
                           "%s/iframe/?iframe=qiita-terms"
                           % (url, info['user_verify_code'],
                              url_escape(username), url))
            except Exception:
                msg = ("Unable to send verification email. Please contact the "
                       "qiita developers at <a href='mailto:%s'>%s</a>") % (
                       qiita_config.help_email, qiita_config.help_email)
                self.redirect(u"%s/?level=danger&message=%s"
                              % (qiita_config.portal_dir, url_escape(msg)))
                return

            msg = ("<h3>User Successfully Created</h3><p>Your Qiita account "
                   "has been successfully created. An email has been sent to "
                   "the email address you provided. This email contains "
                   "instructions on how to activate your account.</p>"
                   "<p>If you don't receive your activation email within a "
                   "couple of minutes, check your spam folder. If you still "
                   "don't see it, send us an email at <a "
                   "href=\"mailto:%s\">%s"
                   "</a>.</p>") % (qiita_config.help_email,
                                   qiita_config.help_email)
            self.redirect(u"%s/?level=success&message=%s" %
                          (qiita_config.portal_dir, url_escape(msg)))
        else:
            error_msg = u"?error=" + url_escape(msg)
            self.redirect(u"%s/auth/create/%s"
                          % (qiita_config.portal_dir, error_msg))


class AuthVerifyHandler(BaseHandler):
    def get(self, code):
        email = self.get_argument("email").strip().lower()

        code_is_valid = False
        msg = "This code is not valid."

        # an exception is raised if the 'code type' is not available, otherwise
        # the method determines the validity of the code
        try:
            code_is_valid = User.verify_code(email, code, "create")
        except QiitaDBError:
            msg = "This user has already created an account."

        if code_is_valid:
            msg = "Successfully verified user. You are now free to log in."
            color = "black"
            r_client.zadd('qiita-usernames', {email: 0})
        else:
            color = "red"

        self.render("user_verified.html", msg=msg, color=color,
                    email=self.get_argument("email").strip())


class AuthLoginHandler(BaseHandler):
    """user login, no page necessary"""
    def get(self):
        self.redirect("%s/" % qiita_config.portal_dir)

    @execute_as_transaction
    def post(self):
        username = self.get_argument("username", "").strip().lower()
        passwd = self.get_argument("password", "")
        nextpage = self.get_argument("next", None)
        if nextpage is None:
            if "auth/" not in self.request.headers['Referer']:
                nextpage = self.request.headers['Referer']
            else:
                nextpage = "%s/" % qiita_config.portal_dir

        msg = ""
        # check the user level
        try:
            if User(username).level == "unverified":
                # email not verified so dont log in
                msg = ("Email not verified. Please check your email and click "
                       "the verify link. You may need to check your spam "
                       "folder to find the email.<br/>If a verification email"
                       " has not arrived in 15 minutes, please email <a href='"
                       "mailto:%s'>%s</a>") % (qiita_config.help_email,
                                               qiita_config.help_email)
        except QiitaDBUnknownIDError:
            msg = "Unknown user"
        except RuntimeError:
            # means DB not available, so set maintenance mode and failover
            r_client.set("maintenance", "Database connection unavailable, "
                         "please try again later.")
            self.redirect("%s/" % qiita_config.portal_dir)
            return

        # Check the login information
        login = None
        try:
            login = User.login(username, passwd)
        except IncorrectEmailError:
            msg = "Unknown user"
        except IncorrectPasswordError:
            msg = "Incorrect password"
        except UnverifiedEmailError:
            msg = "You have not verified your email address"

        if login:
            # everything good so log in
            self.set_current_user(username)
            self.redirect(nextpage)
        else:
            self.render("index.html", message=msg, level='danger')

    def set_current_user(self, user):
        if user:
            self.set_secure_cookie("user", json_encode(user))
        else:
            self.clear_cookie("user")


class AuthLogoutHandler(BaseHandler):
    """Logout handler, no page necessary"""
    def get(self):
        self.clear_cookie("user")
        self.redirect("%s/" % qiita_config.portal_dir)


class KeycloakMixin(OAuth2Mixin):
    config = dict()

    # environment variables that define proxies
    vars_proxy = [env for env in os.environ if env.lower().endswith('_proxy')]
    proxies = list(sorted({os.environ[var] for var in vars_proxy}))
    if len(proxies) > 1:
        msg = ("The OS serving Qiita defines multiple proxy servers via "
               "environment variables, but with different values. Using the "
               "first one:\n  %s") % '\n  '.join(
                ['%s=%s' % (var, os.environ[var]) for var in vars_proxy])
        LogEntry.create('Runtime', msg)
    elif len(proxies) == 1:
        try:
            config['proxy_host'] = ':'.join(proxies[0].split(':')[:-1])
            config['proxy_port'] = int(proxies[0].split(':')[-1])
        except IndexError:
            LogEntry.create(
                'Runtime',
                ("Your proxy configuration doesn't seem to "
                 "follow the host:port pattern."))

    def get_auth_http_client(self):
        return CurlAsyncHTTPClient()

    async def get_authenticated_user(self, redirect_uri: str, code: str):
        http = self.get_auth_http_client()
        body = urllib.parse.urlencode(
            {
                "redirect_uri": redirect_uri,
                "code": code,
                "client_id": qiita_config.oidc[self.idp]['client_id'],
                "client_secret": qiita_config.oidc[self.idp]['client_secret'],
                "grant_type": "authorization_code"
            }
        )
        try:
            response = await http.fetch(
                self._OAUTH_ACCESS_TOKEN_URL,
                method="POST",
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                body=body,
                **self.config)
            return json_decode(response.body)
        except HTTPClientError as e:
            msg = ("The external identity provider '%s' returns an '%s' error"
                   ", when sending a request against '%s'. Thus, we cannot log"
                   " you in. Please contact the Qiita support team at "
                   "<a href='mailto:%s'>%s</a>") % (
                   self.idp, str(e), self._OAUTH_ACCESS_TOKEN_URL,
                   qiita_config.help_email, qiita_config.help_email)
            self.render("index.html", message=msg, level='danger')


class AuthLoginOIDCHandler(BaseHandler, KeycloakMixin):
    idp = None

    async def post(self, login):
        code = self.get_argument('code', False)

        # Qiita might be configured for multiple identity providers. We learn
        # which one the user chose through different name attributes of the
        # html form button
        msg = ""
        self.idp = None
        if hasattr(self, 'path_args') and (len(self.path_args) > 0) and \
           (self.path_args[0] is not None) and (self.path_args[0] != ""):
            self.idp = self.path_args[0]
        else:
            msg = 'External Identity Provider not specified!'
        if self.idp not in qiita_config.oidc.keys():
            msg = ('Unknown Identity Provider "%s", '
                   'please check config file.') % self.idp
            self.idp = None

        if self.idp is None:
            self.render("index.html", message=msg, level='warning')

        idp_config = requests.get(
            qiita_config.oidc[self.idp]['wellknown_uri'],
            proxies={env: os.environ[env]
                     for env in os.environ
                     if env.lower().endswith('_proxy')}).json()

        self._OAUTH_AUTHORIZE_URL = idp_config['authorization_endpoint']
        self._OAUTH_ACCESS_TOKEN_URL = idp_config['token_endpoint']
        self._OAUTH_USERINFO_URL = idp_config['userinfo_endpoint']

        if code:
            # step 2: we got a code and now want to exchange it for a user
            # access token
            access = await self.get_authenticated_user(
                redirect_uri='%s%s' % (
                    qiita_config.base_url,
                    qiita_config.oidc[self.idp]['redirect_endpoint']),
                code=code)
            access_token = access['access_token']
            if not access_token:
                raise HTTPError(400, (
                    "failed to exchange code for access token with "
                    "identity provider '%s'") % self.idp)

            # step 3: obtain user information (email, username, ...) from IdP
            http = self.get_auth_http_client()
            try:
                user_info_res = await http.fetch(
                    self._OAUTH_USERINFO_URL,
                    method="GET",
                    headers={
                        "Accept": "application/json",
                        "Authorization": "Bearer {}".format(access_token)},
                    **self.config)
                user_info = json_decode(user_info_res.body.decode(
                    'utf8', 'replace'))

                if ('email' not in user_info.keys()) or \
                   (user_info['email'] is None) or (user_info['email'] == ""):
                    raise HTTPError(400, (
                        "Email address was not provided "
                        "from your identity provider '%s'") % self.idp)

                username = user_info['email']
                if not User.exists(username):
                    self.create_new_user(username, user_info, self.idp)
                else:
                    self.set_secure_cookie("user", username)
                    self.redirect("%s/" % qiita_config.portal_dir)

            except HTTPClientError as e:
                msg = (
                    "The external identity provider '%s' returns an '%s' error"
                    ", when sending a request against '%s'. Thus, we cannot "
                    "log you in. Please contact the Qiita support team at "
                    "<a href='mailto:%s'>%s</a>") % (
                    self.idp, str(e), self._OAUTH_USERINFO_URL,
                    qiita_config.help_email, qiita_config.help_email)
                self.render("index.html", message=msg, level='danger')
        else:
            # step 1: no code from IdP yet, thus retrieve one now
            self.authorize_redirect(
                 redirect_uri='%s%s' % (
                    qiita_config.base_url,
                    qiita_config.oidc[self.idp]['redirect_endpoint']),
                 client_id=qiita_config.oidc[self.idp]['client_id'],
                 client_secret=qiita_config.oidc[self.idp]['client_secret'],
                 response_type='code',
                 scope=[qiita_config.oidc[self.idp]['scope']]
            )
    get = post  # redirect will use GET method

    @execute_as_transaction
    def create_new_user(self, username, user_info, idp):
        msg, msg_level = None, None  # 'danger', 'success', 'info', 'warning'
        try:
            # create user stub
            created = User.create_oidc(username, user_info, idp)
            if created:
                msg, msg_level = ((
                    "<h3>User Successfully Registered!</h3><p>Your user '%s',"
                    " provided through '%s', has been successfully registered"
                    " and activated. Welcome to Qiita!</p>"
                    "<p>Please direct any upcoming questions to "
                    "<a href=\"mailto:%s\">%s</a></p>") % (
                        username, qiita_config.oidc[idp]['label'],
                        qiita_config.help_email,
                        qiita_config.help_email)), 'success'
            else:
                msg, msg_level = (
                    ("Unable to create account. Please contact the qiita "
                     "developers at <a href='mailto:%s'>%s</a>") % (
                        qiita_config.help_email,
                        qiita_config.help_email)), 'danger'

            # activate user
            User.verify_code(
                username, User(username).info['user_verify_code'], "create")

            self.set_secure_cookie("user", username)
        except QiitaDBDuplicateError:
            msg, msg_level = "Email already registered as a user", 'info'

        self.redirect(u"%s/?level=%s&message=%s" % (
             qiita_config.portal_dir, msg_level, url_escape(msg)))
