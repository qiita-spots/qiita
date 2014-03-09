#!/usr/bin/env python

__author__ = "Joshua Shorenstein"
__copyright__ = "Copyright 2013, The QiiTa-pet Project"
__credits__ = ["Joshua Shorenstein", "Antonio Gonzalez",
               "Jose Antonio Navas Molina"]
__license__ = "BSD"
__version__ = "0.2.0-dev"
__maintainer__ = "Joshua Shorenstein"
__email__ = "Joshua.Shorenstein@colorado.edu"
__status__ = "Development"

from tornado.web import authenticated, HTTPError

from .webserver import BaseHandler
from qiita_core.qiita_settings import DATATYPES, FUNCTIONS


class WaitingHandler(BaseHandler):
    """Waiting Page"""
    @authenticated
    def get(self, analysis):
        pass

    @authenticated
    #This post function takes care of actual job submission
    def post(self, page):
        pass


class RunningHandler(BaseHandler):
    """Currently running jobs list handler"""
    @authenticated
    def get(self):
        pass


class ShowAnalysisHandler(BaseHandler):
    """Completed analysis page"""
    @authenticated
    def get(self, analysis):
        pass

    @authenticated
    def post(self, page):
        pass


class DeleteAnalysisHandler(BaseHandler):
    @authenticated
    def post(self):
        pass


#ANALYSES and COMBINED lists are set in settings.py
class QiitaAnalysisHandler(BaseHandler):
    #@authenticated
    def get(self, page):
        if page != "1":
            HTTPError("405", "Request page >1 of QiitaAnalysisHandler")
        else:
            #global variable that is wiped when you start a new analysis
            self.render("meta1.html", user=self.get_current_user(), error="",
                        metadata=["meta1", "meta2", "meta3"], datatypes=DATATYPES)

    @authenticated
    def post(self, page):
        if page == "1":
            HTTPError("405", "Post to page 1 of QiitaAnalysisHandler")
        elif page == "2":
            raise NotImplementedError("MetaAnalysis Page %s missing!" % page)
        else:
            raise NotImplementedError("MetaAnalysis Page %s missing!" % page)
