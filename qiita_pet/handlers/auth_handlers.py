# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

import secrets
from tornado.escape import url_escape, json_encode

from qiita_pet.handlers.base_handlers import BaseHandler
from qiita_pet.handlers.globus import GlobusOAuth2Mixin
from qiita_core.qiita_settings import qiita_config, r_client
from qiita_core.util import execute_as_transaction
from qiita_core.exceptions import (IncorrectPasswordError, IncorrectEmailError,
                                   UnverifiedEmailError)
from qiita_db.util import send_email
from qiita_db.user import User
from qiita_db.exceptions import (QiitaDBUnknownIDError, QiitaDBDuplicateError,
                                 QiitaDBError)
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
                       "qiita developers at <a href='mailto:qiita-help"
                       "@gmail.com'>qiita-help@gmail.com</a>")
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
                   "href=\"mailto:qiita.help@ucsd.edu\">qiita.help@ucsd.edu"
                   "</a>.</p>")
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
                       "mailto:qiita.help@gmail.com'>qiita.help@gmail.com</a>")
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


class GlobusOAuth2LoginHandler(BaseHandler, GlobusOAuth2Mixin):
    """Globus Auth OAuth2 authentication handler"""
    def post(self):
        self.authorize_redirect(
            redirect_uri=qiita_config.globus_redirect_uri,
            client_id=qiita_config.globus_client_key,
            scope=["openid",
                   "profile",
                   "email",
                   "urn:globus:auth:scope:transfer.api.globus.org:all"],
            response_type="code",
            extra_params={"access_type": "offline"})

    async def get(self):
        if self.get_argument("code", False):
            nextpage = self.get_argument("next", None)
            if nextpage is None:
                nextpage = "%s/" % qiita_config.portal_dir
            tokens = await self.get_tokens(
                key=qiita_config.globus_client_key,
                secret=qiita_config.globus_client_secret,
                redirect_uri=qiita_config.globus_redirect_uri,
                code=self.get_argument("code"))
            user_info = await self.get_user_info(tokens["access_token"])
            username = user_info.get("preferred_username")
            password = secrets.token_urlsafe(16)
            info = {
                "name": user_info.get("name"),
                "affiliation": user_info.get("organization")
            }
            try:
                User.create(username, password, info)
            except QiitaDBDuplicateError:
                pass
            self.set_current_user(username)
            self.set_secure_cookie("access_token", tokens["access_token"])
            self.set_secure_cookie("refresh_token", tokens["refresh_token"])
            self.redirect(nextpage)

    def set_current_user(self, user):
        if user:
            self.set_secure_cookie("user", json_encode(user))
        else:
            self.clear_cookie("user")
