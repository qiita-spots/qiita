#!/usr/bin/env python

from tornado.escape import url_escape, json_encode

from qiita_pet.handlers.base_handlers import BaseHandler
from qiita_core.util import send_email
from qiita_core.exceptions import IncorrectPasswordError, IncorrectEmailError
from qiita_db.user import User
from qiita_db.exceptions import QiitaDBUnknownIDError
# login code modified from https://gist.github.com/guillaumevincent/4771570


class AuthCreateHandler(BaseHandler):
    """User Creation"""
    def get(self):
        try:
            error_message = self.get_argument("error")
        # Tornado can raise an Exception directly, not a defined type
        except:
            error_message = ""
        self.render("create_user.html", user=self.current_user,
                    error=error_message)

    def post(self):
        username = self.get_argument("username", "").strip().lower()
        password = self.get_argument("pass", "")
        info = {}
        for info_column in ("name", "affiliation", "address", "phone"):
            hold = self.get_argument(info_column, None)
            if hold:
                info[info_column] = hold

        created = User.create(username, password, info)

        if created:
            send_email(username, "QIITA: Verify Email Address", "Please click "
                       "the following link to verify email address: "
                       "http://qiita.colorado.edu/auth/verify/%s" %
                       User.verify_code)
            self.redirect(u"/")
        else:
            error_msg = u"?error=" + url_escape("Error with user creation")
            self.redirect(u"/auth/create/" + error_msg)


class AuthVerifyHandler(BaseHandler):
    def get(self):
        email = self.get_argument("email").strip().lower()
        code = self.get_argument("code")
        try:
            User(email).level = 3
            msg = "Successfully verified user!"
        except QiitaDBUnknownIDError:
            msg = "Code not valid!"

        self.render("user_verified.html", user=None, error=msg)


class AuthLoginHandler(BaseHandler):
    """user login, no page necessary"""
    def get(self):
        self.write("YOU SHOULD NOT BE ACCESSING THIS PAGE DIRECTLY. GO AWAY.")

    def post(self):
        username = self.get_argument("username", "").strip().lower()
        passwd = self.get_argument("password", "")
        nextpage = self.get_argument("next", "/")
        # check the user level
        try:
            if User(username).level == 4:  # 4 is id for unverified
                # email not verified so dont log in
                msg = "Email not verified"
        except QiitaDBUnknownIDError:
            msg = "Unknown user"

        # Check the login information
        login = None
        try:
            login = User.login(username, passwd)
        except IncorrectEmailError:
            msg = "Unknown user"
        except IncorrectPasswordError:
            msg = "Incorrect password"

        if login:
            # everthing good so log in
            self.set_current_user(username)
            self.redirect(nextpage)
            return
        self.render("index.html", user=None, loginerror=msg)

    def set_current_user(self, user):
        if user:
            self.set_secure_cookie("user", json_encode(user))
        else:
            self.clear_cookie("user")


class AuthLogoutHandler(BaseHandler):
    """Logout handler, no page necessary"""
    def get(self):
        self.clear_cookie("user")
        self.redirect("/")
