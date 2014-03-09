#!/usr/bin/env python

__author__ = "Joshua Shorenstein"
__copyright__ = "Copyright 2013, The QiiTa-pet Project"
__credits__ = ["Joshua Shorenstein"]
__license__ = "BSD"
__version__ = "0.2.0-dev"
__maintainer__ = "Joshua Shorenstein"
__email__ = "Joshua.Shorenstein@colorado.edu"
__status__ = "Development"

from hashlib import sha512

from tornado.escape import url_escape, json_encode

from .webserver import BaseHandler
from ..qiita_ware.api.user_manager import create_user, check_password
from ..qiita_core.exceptions import QiitaUserError


class AuthCreateHandler(BaseHandler):
    '''User Creation'''
    def get(self):
        try:
            error_message = self.get_argument("error")
        # Tornado can raise an Exception directly, not a defined type
        except Exception, e:
            error_message = str(e)
        self.render("create.html", user=self.get_current_user(),
                    errormessage=url_escape(error_message))

    def post(self):
        username = self.get_argument("username", "")
        passwd = sha512(self.get_argument("password", "")).hexdigest()
        try:
            create_user(username, passwd)
        except QiitaUserError, e:
            error_msg = u"?error=" + url_escape(str(e))
            self.redirect(u"/auth/create/" + error_msg)
            return
        self.redirect(u"/auth/login/?error=User+created")


class AuthLoginHandler(BaseHandler):
    '''Login Page'''
    def get(self):
        try:
            error_message = self.get_argument("error")
        # Tornado can raise an Exception directly, not a defined type
        except Exception:
            error_message = ""

        self.render("login.html", user=self.get_current_user(),
                    errormessage=error_message)

    def post(self):
        username = self.get_argument("username", "")
        passwd = sha512(self.get_argument("password", "")).hexdigest()
        auth = check_password(username, passwd)
        if auth:
            self.set_current_user(username)
            self.redirect(self.get_argument("next", u"/"))
        else:
            error_msg = u"?error=%s" % url_escape("Login incorrect")
            self.redirect(u"/auth/login/" + error_msg)

    def set_current_user(self, user):
        """Sets current user or, if already set, clears current user
        Input:
            user: username to set
        """
        if user:
            self.set_secure_cookie("user", json_encode(user))
        else:
            self.clear_cookie("user")


class AuthLogoutHandler(BaseHandler):
    '''Logout handler, no page necessary'''
    def get(self):
        self.clear_cookie("user")
        self.redirect("/")
