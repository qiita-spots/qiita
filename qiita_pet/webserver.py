# login code modified from https://gist.github.com/guillaumevincent/4771570

import tornado.auth
import tornado.escape
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.websocket
from tornado.options import define, options
from os.path import dirname, join
from base64 import b64encode
from uuid import uuid4

from qiita_pet.handlers.base_handlers import (MainHandler, MockupHandler,
                                              NoPageHandler)
from qiita_pet.handlers.auth_handlers import (
    AuthCreateHandler, AuthLoginHandler, AuthLogoutHandler, AuthVerifyHandler)
from qiita_pet.handlers.analysis_handlers import (
    CreateAnalysisHandler, SelectStudiesHandler, SelectCommandsHandler,
    AnalysisWaitHandler, AnalysisResultsHandler, ShowAnalysesHandler)
from qiita_pet.handlers.websocket_handlers import MessageHandler
from qiita_db.util import get_db_files_base_dir

define("port", default=8888, help="run on the given port", type=int)

DIRNAME = dirname(__file__)
STATIC_PATH = join(DIRNAME, "static")
TEMPLATE_PATH = join(DIRNAME, "templates")  # base folder for webpages
RES_PATH = get_db_files_base_dir()
COOKIE_SECRET = b64encode(uuid4().bytes + uuid4().bytes)
DEBUG = True


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/", MainHandler),
            (r"/auth/login/", AuthLoginHandler),
            (r"/auth/logout/", AuthLogoutHandler),
            (r"/auth/create/", AuthCreateHandler),
            (r"/results/(.*)", tornado.web.StaticFileHandler,
             {"path": RES_PATH}),
            (r"/static/(.*)", tornado.web.StaticFileHandler,
             {"path": STATIC_PATH}),
            (r"/analysis/1", CreateAnalysisHandler),
            (r"/analysis/2", SelectStudiesHandler),
            (r"/analysis/3", SelectCommandsHandler),
            (r"/analysis/wait/(.*)", AnalysisWaitHandler),
            (r"/analysis/results/(.*)", AnalysisResultsHandler),
            (r"/analysis/show/", ShowAnalysesHandler),
            (r"/consumer/", MessageHandler),
            (r"/mockup/", MockupHandler),
            # 404 PAGE MUST BE LAST IN THIS LIST!
            (r".*", NoPageHandler)
        ]
        settings = {
            "template_path": TEMPLATE_PATH,
            "debug": DEBUG,
            "cookie_secret": COOKIE_SECRET,
            "login_url": "/auth/login/"
        }
        tornado.web.Application.__init__(self, handlers, **settings)


def main():
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(options.port)
    print("Tornado started on port", options.port)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()
