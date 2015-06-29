# login code modified from https://gist.github.com/guillaumevincent/4771570
import tornado.auth
import tornado.escape
import tornado.web
import tornado.websocket
from os.path import dirname, join
from base64 import b64encode
from uuid import uuid4
from moi.websocket import MOIMessageHandler

from qiita_core.qiita_settings import qiita_config
from qiita_pet.handlers.base_handlers import (MainHandler, NoPageHandler)
from qiita_pet.handlers.auth_handlers import (
    AuthCreateHandler, AuthLoginHandler, AuthLogoutHandler, AuthVerifyHandler)
from qiita_pet.handlers.user_handlers import (
    ChangeForgotPasswordHandler, ForgotPasswordHandler, UserProfileHandler)
from qiita_pet.handlers.analysis_handlers import (
    SelectCommandsHandler, AnalysisWaitHandler, AnalysisResultsHandler,
    ShowAnalysesHandler, ResultsHandler, SelectedSamplesHandler,
    AnalysisSummaryAJAX)
from qiita_pet.handlers.study_handlers import (
    StudyEditHandler, ListStudiesHandler, SearchStudiesAJAX,
    StudyDescriptionHandler, MetadataSummaryHandler, EBISubmitHandler,
    CreateStudyAJAX, ShareStudyAJAX, StudyApprovalList,
    PreprocessingSummaryHandler, VAMPSHandler)
from qiita_pet.handlers.websocket_handlers import (
    MessageHandler, SelectedSocketHandler, SelectSamplesHandler)
from qiita_pet.handlers.logger_handlers import LogEntryViewerHandler
from qiita_pet.handlers.upload import UploadFileHandler, StudyUploadFileHandler
from qiita_pet.handlers.compute import (
    ComputeCompleteHandler, AddFilesToRawData, UnlinkAllFiles, CreateRawData)
from qiita_pet.handlers.preprocessing_handlers import PreprocessHandler
from qiita_pet.handlers.processing_handlers import ProcessHandler
from qiita_pet.handlers.stats import StatsHandler
from qiita_pet.handlers.download import DownloadHandler
from qiita_pet import uimodules
from qiita_db.util import get_mountpoint
if qiita_config.portal == "QIITA":
    from qiita_pet.handlers.portal import StudyPortalHandler


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
            (r"/results/(.*)", ResultsHandler,
             {"path": RES_PATH}),
            (r"/static/(.*)", tornado.web.StaticFileHandler,
             {"path": STATIC_PATH}),
            (r"/analysis/3", SelectCommandsHandler),
            (r"/analysis/wait/(.*)", AnalysisWaitHandler),
            (r"/analysis/results/(.*)", AnalysisResultsHandler),
            (r"/analysis/show/", ShowAnalysesHandler),
            (r"/analysis/dflt/sumary/", AnalysisSummaryAJAX),
            (r"/analysis/selected/", SelectedSamplesHandler),
            (r"/analysis/selected/socket/", SelectedSocketHandler),
            (r"/moi-ws/", MOIMessageHandler),
            (r"/consumer/", MessageHandler),
            (r"/admin/error/", LogEntryViewerHandler),
            (r"/admin/approval/", StudyApprovalList),
            (r"/metadata_summary/(.*)", MetadataSummaryHandler),
            (r"/preprocessing_summary/(.*)", PreprocessingSummaryHandler),
            (r"/ebi_submission/(.*)", EBISubmitHandler),
            (r"/compute_complete/(.*)", ComputeCompleteHandler),
            (r"/study/create/", StudyEditHandler),
            (r"/study/edit/(.*)", StudyEditHandler),
            (r"/study/list/", ListStudiesHandler),
            (r"/study/list/socket/", SelectSamplesHandler),
            (r"/study/search/(.*)", SearchStudiesAJAX),
            (r"/study/add_files_to_raw_data", AddFilesToRawData),
            (r"/study/create_raw_data", CreateRawData),
            (r"/study/unlink_all_files", UnlinkAllFiles),
            (r"/study/preprocess", PreprocessHandler),
            (r"/study/process", ProcessHandler),
            (r"/study/sharing/", ShareStudyAJAX),
            (r"/study/description/(.*)", StudyDescriptionHandler),
            (r"/study/upload/(.*)", StudyUploadFileHandler),
            (r"/upload/", UploadFileHandler),
            (r"/check_study/", CreateStudyAJAX),
            (r"/stats/", StatsHandler),
            (r"/download/(.*)", DownloadHandler),
            (r"/vamps/(.*)", VAMPSHandler),
        ]
        if qiita_config.portal == "QIITA":
            # Add portals editing pages only on main portal
            portals = [
                (r"/admin/portals/studies/", StudyPortalHandler)
            ]
            handlers.extend(portals)
        # 404 PAGE MUST BE LAST IN THIS LIST!
        handlers.append((r".*", NoPageHandler))

        settings = {
            "template_path": TEMPLATE_PATH,
            "debug": DEBUG,
            "cookie_secret": COOKIE_SECRET,
            "login_url": "/auth/login/",
            "ui_modules": uimodules
        }
        tornado.web.Application.__init__(self, handlers, **settings)
