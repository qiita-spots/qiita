#!/usr/bin/env python

__author__ = "Joshua Shorenstein"
__copyright__ = "Copyright 2013, The QiiTa-pet Project"
__credits__ = ["Joshua Shorenstein"]
__license__ = "BSD"
__version__ = "0.2.0-dev"
__maintainer__ = "Joshua Shorenstein"
__email__ = "Joshua.Shorenstein@colorado.edu"
__status__ = "Development"

#login code modified from https://gist.github.com/guillaumevincent/4771570
from os.path import dirname, join
from base64 import b64encode
from uuid import uuid4

import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.websocket
from tornado.options import define, options

from .push import MessageHandler, SearchASHandler
from .analysis_handlers import (WaitingHandler, RunningHandler,
                                ShowAnalysisHandler, DeleteAnalysisHandler,
                                QiitaAnalysisHandler)
from .auth_handlers import (AuthLoginHandler, AuthLogoutHandler,
                            AuthCreateHandler)
from .render_handlers import MultivisHandler, MockupHandler, MinStudyHandler
from ..qiita_ware.api.analysis_manager import get_completed_analyses


class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        """Overrides default method of returning user curently connected"""
        user = self.get_secure_cookie("user")
        if user is None:
            self.clear_cookie("user")
            return ""
        else:
            return user.strip("\"'")

    def write_error(self, status_code, **kwargs):
        """Overrides the error page created by Tornado"""
        from traceback import format_exception
        if self.settings.get("debug") and "exc_info" in kwargs:
            exc_info = kwargs["exc_info"]
            trace_info = "".join(["%s<br />" % line for line in
                                 format_exception(*exc_info)])
            request_info = "".join(["<strong>%s</strong>: %s<br />" %
                                    (k, self.request.__dict__[k]) for k in
                                    self.request.__dict__.keys()])
            error = exc_info[1]

            self.render("error.html", error=error, trace_info=trace_info,
                        request_info=request_info,
                        user=self.get_current_user())


class IndexHandler(BaseHandler):
    """Index page"""
    @tornado.web.authenticated
    def get(self):
        username = self.get_current_user()
        completed_analyses = get_completed_analyses(username)

        if completed_analyses is None:
            completed_analyses = []

        self.render("index.html", user=username, analyses=completed_analyses)


class NoPageHandler(BaseHandler):
    def get(self):
        self.render("404.html", user=self.get_current_user(), error="")


class Application(tornado.web.Application):
    def __init__(self):
        DIRNAME = dirname(__file__)
        STATIC_PATH = join(DIRNAME, "static")
        TEMPLATE_PATH = join(DIRNAME, "templates")
        RES_PATH = join(DIRNAME, "results")
        COOKIE_SECRET = b64encode(uuid4().bytes + uuid4().bytes)
        handlers = [
            (r"/", IndexHandler),
            (r"/auth/login/", AuthLoginHandler),
            (r"/auth/logout/", AuthLogoutHandler),
            (r"/auth/create/", AuthCreateHandler),
            (r"/results/(.*)", tornado.web.StaticFileHandler,
                {"path": RES_PATH}),
            (r"/static/(.*)", tornado.web.StaticFileHandler,
                {"path": STATIC_PATH}),
            (r"/waiting/(.*)", WaitingHandler),
            (r"/running/", RunningHandler),
            (r"/waitws/", MessageHandler),
            (r"/searchws/", SearchASHandler),
            (r"/minstudy/(.*)", MinStudyHandler),
            (r"/completed/(.*)", ShowAnalysisHandler),
            (r"/meta/([0-9]+)", QiitaAnalysisHandler),
            (r"/del/", DeleteAnalysisHandler),
            (r"/multivis/", MultivisHandler),
            (r"/mockup/", MockupHandler),
            #404 PAGE MUST BE LAST IN THIS LIST!
            (r".*", NoPageHandler)
        ]
        settings = {
            "template_path": TEMPLATE_PATH,
            "debug": True,
            "cookie_secret": COOKIE_SECRET,
            "login_url": "/auth/login/",
        }
        tornado.web.Application.__init__(self, handlers, **settings)


def main():
    define("port", default=8888, help="run on the given port", type=int)
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(options.port)
    print "Tornado started on port", options.port
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()
