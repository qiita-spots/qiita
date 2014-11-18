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

from qiita_core.qiita_settings import qiita_config
from qiita_pet.handlers.base_handlers import (MainHandler, NoPageHandler)
from qiita_pet.handlers.auth_handlers import (
    AuthCreateHandler, AuthLoginHandler, AuthLogoutHandler, AuthVerifyHandler)
from qiita_pet.handlers.user_handlers import (
    ChangeForgotPasswordHandler, ForgotPasswordHandler, UserProfileHandler)
from qiita_pet.handlers.analysis_handlers import (
    SelectCommandsHandler, AnalysisWaitHandler, AnalysisResultsHandler,
    ShowAnalysesHandler, SearchStudiesHandler)
from qiita_pet.handlers.study_handlers import (
    CreateStudyHandler, PrivateStudiesHandler, PublicStudiesHandler,
    StudyDescriptionHandler, MetadataSummaryHandler, EBISubmitHandler,
    CreateStudyAJAX, ShareStudyAJAX, PreprocessingSummaryHandler)
from qiita_pet.handlers.logger_handlers import LogEntryViewerHandler
from qiita_pet.handlers.websocket_handlers import MessageHandler
from qiita_pet.handlers.upload import UploadFileHandler, StudyUploadFileHandler
from qiita_pet.handlers.compute import (
    ComputeCompleteHandler, AddFilesToRawData, UnlinkAllFiles)
from qiita_pet.handlers.preprocessing_handlers import PreprocessHandler
from qiita_pet.handlers.stats import StatsHandler
from qiita_pet.handlers.download import DownloadHandler
from qiita_db.util import get_mountpoint

define("port", default=8888, help="run on the given port", type=int)

DIRNAME = dirname(__file__)
STATIC_PATH = join(DIRNAME, "static")
TEMPLATE_PATH = join(DIRNAME, "templates")  # base folder for webpages
_, RES_PATH = get_mountpoint('job')[0]
COOKIE_SECRET = b64encode(uuid4().bytes + uuid4().bytes)
DEBUG = qiita_config.test_environment


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/", MainHandler),
            (r"/auth/login/", AuthLoginHandler),
            (r"/auth/logout/", AuthLogoutHandler),
            (r"/auth/create/", AuthCreateHandler),
            (r"/auth/verify/(.*)", AuthVerifyHandler),
            (r"/auth/forgot/", ForgotPasswordHandler),
            (r"/auth/reset/(.*)", ChangeForgotPasswordHandler),
            (r"/profile/", UserProfileHandler),
            (r"/results/(.*)", tornado.web.StaticFileHandler,
             {"path": RES_PATH}),
            (r"/static/(.*)", tornado.web.StaticFileHandler,
             {"path": STATIC_PATH}),
            (r"/analysis/2", SearchStudiesHandler),
            (r"/analysis/3", SelectCommandsHandler),
            (r"/analysis/wait/(.*)", AnalysisWaitHandler),
            (r"/analysis/results/(.*)", AnalysisResultsHandler),
            (r"/analysis/show/", ShowAnalysesHandler),
            (r"/consumer/", MessageHandler),
            (r"/error/", LogEntryViewerHandler),
            (r"/metadata_summary/(.*)", MetadataSummaryHandler),
            (r"/preprocessing_summary/(.*)", PreprocessingSummaryHandler),
            (r"/ebi_submission/(.*)", EBISubmitHandler),
            (r"/compute_complete/(.*)", ComputeCompleteHandler),
            (r"/study/create/", CreateStudyHandler),
            (r"/study/private/", PrivateStudiesHandler),
            (r"/study/public/", PublicStudiesHandler),
            (r"/study/add_files_to_raw_data", AddFilesToRawData),
            (r"/study/unlink_all_files", UnlinkAllFiles),
            (r"/study/preprocess", PreprocessHandler),
            (r"/study/sharing/", ShareStudyAJAX),
            (r"/study/description/(.*)", StudyDescriptionHandler),
            (r"/study/upload/(.*)", StudyUploadFileHandler),
            (r"/upload/", UploadFileHandler),
            (r"/check_study/", CreateStudyAJAX),
            (r"/stats/", StatsHandler),
            (r"/download/(.*)", DownloadHandler),
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
