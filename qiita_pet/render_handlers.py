#!/usr/bin/env python

__author__ = "Joshua Shorenstein"
__copyright__ = "Copyright 2013, The QiiTa-pet Project"
__credits__ = ["Joshua Shorenstein"]
__license__ = "BSD"
__version__ = "0.2.0-dev"
__maintainer__ = "Joshua Shorenstein"
__email__ = "Joshua.Shorenstein@colorado.edu"
__status__ = "Development"

from tornado.web import authenticated

from .webserver import BaseHandler


class MultivisHandler(BaseHandler):
    def get(self):
        self.render("multivis.html", user=self.get_current_user(), error="")


class MockupHandler(BaseHandler):
    def get(self):
        self.render("mockup.html", user=self.get_current_user(), error="")


class MinStudyHandler(BaseHandler):
    @authenticated
    def get(self, study):
        self.render("minstudy.html", user=self.get_current_user(), error="",
                    study=study)
