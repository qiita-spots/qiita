# login code modified from https://gist.github.com/guillaumevincent/4771570
import tornado.auth
import tornado.escape
import tornado.web
import tornado.websocket
from os.path import dirname, join, exists
from shutil import copy
from base64 import b64encode
from uuid import uuid4
from moi import moi_js, moi_list_js
from moi.websocket import MOIMessageHandler

from qiita_core.qiita_settings import qiita_config
from qiita_pet.handlers.base_handlers import (MainHandler, NoPageHandler)
from qiita_pet.handlers.auth_handlers import (
    AuthCreateHandler, AuthLoginHandler, AuthLogoutHandler, AuthVerifyHandler)
from qiita_pet.handlers.user_handlers import (
    ChangeForgotPasswordHandler, ForgotPasswordHandler, UserProfileHandler,
    UserMessagesHander)
from qiita_pet.handlers.analysis_handlers import (
    SelectCommandsHandler, AnalysisWaitHandler, AnalysisResultsHandler,
    ShowAnalysesHandler, ResultsHandler, SelectedSamplesHandler,
    AnalysisSummaryAJAX, ShareAnalysisAJAX)
from qiita_pet.handlers.study_handlers import (
    StudyIndexHandler, StudyBaseInfoAJAX, SampleTemplateAJAX,
    StudyEditHandler, ListStudiesHandler, SearchStudiesAJAX, EBISubmitHandler,
    CreateStudyAJAX, ShareStudyAJAX, StudyApprovalList, ArtifactGraphAJAX,
    PreprocessingSummaryHandler, VAMPSHandler, PrepTemplateGraphAJAX,
    ProcessArtifactHandler, ListCommandsHandler, ListOptionsHandler,
    PrepTemplateAJAX, NewArtifactHandler, SampleAJAX,
    StudyDeleteAjax, ArtifactAdminAJAX, ArtifactAJAX,
    NewPrepTemplateAjax, DataTypesMenuAJAX, StudyFilesAJAX,
    PrepTemplateSummaryAJAX, ArtifactSummaryAJAX,
    WorkflowHandler, WorkflowRunHandler, JobAJAX, AutocompleteHandler)
from qiita_pet.handlers.websocket_handlers import (
    MessageHandler, SelectedSocketHandler, SelectSamplesHandler)
from qiita_pet.handlers.logger_handlers import LogEntryViewerHandler
from qiita_pet.handlers.upload import UploadFileHandler, StudyUploadFileHandler
from qiita_pet.handlers.compute import ComputeCompleteHandler, CreateRawData
from qiita_pet.handlers.preprocessing_handlers import PreprocessHandler
from qiita_pet.handlers.processing_handlers import ProcessHandler
from qiita_pet.handlers.stats import StatsHandler
from qiita_pet.handlers.download import DownloadHandler
from qiita_pet.handlers.prep_template import PrepTemplateHandler
from qiita_pet.handlers.ontology import OntologyHandler
from qiita_db.handlers.processing_job import (JobHandler, HeartbeatHandler,
                                              ActiveStepHandler,
                                              CompleteHandler)
from qiita_db.handlers.artifact import (ArtifactFilepathsHandler,
                                        ArtifactMappingHandler,
                                        ArtifactTypeHandler)
from qiita_db.handlers.oauth2 import TokenAuthHandler
from qiita_db.handlers.reference import ReferenceFilepathsHandler
from qiita_pet import uimodules
from qiita_db.util import get_mountpoint
if qiita_config.portal == "QIITA":
    from qiita_pet.handlers.portal import (
        StudyPortalHandler, StudyPortalAJAXHandler)


DIRNAME = dirname(__file__)
STATIC_PATH = join(DIRNAME, "static")
TEMPLATE_PATH = join(DIRNAME, "templates")  # base folder for webpages
_, RES_PATH = get_mountpoint('job')[0]
COOKIE_SECRET = b64encode(uuid4().bytes + uuid4().bytes)
DEBUG = qiita_config.test_environment


_vendor_js = join(STATIC_PATH, 'vendor', 'js')
if not exists(join(_vendor_js, 'moi.js')):
    copy(moi_js(), _vendor_js)
    copy(moi_list_js(), _vendor_js)


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
            (r"/user/messages/", UserMessagesHander),
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
            (r"/analysis/sharing/", ShareAnalysisAJAX),
            (r"/moi-ws/", MOIMessageHandler),
            (r"/consumer/", MessageHandler),
            (r"/admin/error/", LogEntryViewerHandler),
            (r"/admin/approval/", StudyApprovalList),
            (r"/admin/artifact/", ArtifactAdminAJAX),
            (r"/preprocessing_summary/(.*)", PreprocessingSummaryHandler),
            (r"/ebi_submission/(.*)", EBISubmitHandler),
            (r"/compute_complete/(.*)", ComputeCompleteHandler),
            (r"/study/create/", StudyEditHandler),
            (r"/study/edit/(.*)", StudyEditHandler),
            (r"/study/list/", ListStudiesHandler),
            (r"/study/process/commands/options/", ListOptionsHandler),
            (r"/study/process/commands/", ListCommandsHandler),
            (r"/study/process/workflow/run/", WorkflowRunHandler),
            (r"/study/process/workflow/", WorkflowHandler),
            (r"/study/process/job/", JobAJAX),
            (r"/study/process/", ProcessArtifactHandler),
            (r"/study/list/socket/", SelectSamplesHandler),
            (r"/study/search/(.*)", SearchStudiesAJAX),
            (r"/study/new_artifact/", NewArtifactHandler),
            (r"/study/files/", StudyFilesAJAX),
            (r"/study/create_raw_data", CreateRawData),
            (r"/study/preprocess", PreprocessHandler),
            (r"/study/process", ProcessHandler),
            (r"/study/sharing/", ShareStudyAJAX),
            (r"/study/sharing/autocomplete/", AutocompleteHandler),
            (r"/study/new_prep_template/", NewPrepTemplateAjax),
            (r"/prep/graph/", PrepTemplateGraphAJAX),
            (r"/artifact/", ArtifactAJAX),
            (r"/artifact/graph/", ArtifactGraphAJAX),
            (r"/prep_template/", PrepTemplateHandler),
            (r"/ontology/", OntologyHandler),
            # ORDER FOR /study/description/ SUBPAGES HERE MATTERS.
            # Same reasoning as below. /study/description/(.*) should be last.
            (r"/study/description/sample_template/", SampleTemplateAJAX),
            (r"/study/description/sample_summary/", SampleAJAX),
            (r"/study/description/prep_summary/", PrepTemplateSummaryAJAX),
            (r"/study/description/prep_template/", PrepTemplateAJAX),
            (r"/study/description/artifact_summary/", ArtifactSummaryAJAX),
            (r"/study/description/baseinfo/", StudyBaseInfoAJAX),
            (r"/study/description/data_type_menu/", DataTypesMenuAJAX),
            (r"/study/description/(.*)", StudyIndexHandler),
            (r"/study/delete/", StudyDeleteAjax),
            (r"/study/upload/(.*)", StudyUploadFileHandler),
            (r"/upload/", UploadFileHandler),
            (r"/check_study/", CreateStudyAJAX),
            (r"/stats/", StatsHandler),
            (r"/download/(.*)", DownloadHandler),
            (r"/vamps/(.*)", VAMPSHandler),
            # Plugin handlers - the order matters here so do not change
            # qiita_db/jobs/(.*) should go after any of the
            # qiita_db/jobs/(.*)/XXXX because otherwise it will match the
            # regular expression and the qiita_db/jobs/(.*)/XXXX will never
            # be hit.
            (r"/qiita_db/authenticate/", TokenAuthHandler),
            (r"/qiita_db/jobs/(.*)/heartbeat/", HeartbeatHandler),
            (r"/qiita_db/jobs/(.*)/step/", ActiveStepHandler),
            (r"/qiita_db/jobs/(.*)/complete/", CompleteHandler),
            (r"/qiita_db/jobs/(.*)", JobHandler),
            (r"/qiita_db/artifacts/(.*)/filepaths/", ArtifactFilepathsHandler),
            (r"/qiita_db/artifacts/(.*)/mapping/", ArtifactMappingHandler),
            (r"/qiita_db/artifacts/(.*)/type/", ArtifactTypeHandler),
            (r"/qiita_db/references/(.*)/filepaths/",
             ReferenceFilepathsHandler)
        ]
        if qiita_config.portal == "QIITA":
            # Add portals editing pages only on main portal
            portals = [
                (r"/admin/portals/studies/", StudyPortalHandler),
                (r"/admin/portals/studiesAJAX/", StudyPortalAJAXHandler)
            ]
            handlers.extend(portals)
        # 404 PAGE MUST BE LAST IN THIS LIST!
        handlers.append((r".*", NoPageHandler))

        settings = {
            "template_path": TEMPLATE_PATH,
            "debug": DEBUG,
            "cookie_secret": qiita_config.cookie_secret,
            "login_url": "%s/auth/login/" % qiita_config.portal_dir,
            "ui_modules": uimodules,
        }
        tornado.web.Application.__init__(self, handlers, **settings)
