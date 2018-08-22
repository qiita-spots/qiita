# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

# login code modified from https://gist.github.com/guillaumevincent/4771570
import tornado.auth
import tornado.escape
import tornado.web
import tornado.websocket
from os.path import dirname, join
from base64 import b64encode
from uuid import uuid4

from qiita_core.qiita_settings import qiita_config
from qiita_core.util import is_test_environment
from qiita_pet.handlers.base_handlers import (
    MainHandler, NoPageHandler, IFrame)
from qiita_pet.handlers.auth_handlers import (
    AuthCreateHandler, AuthLoginHandler, AuthLogoutHandler, AuthVerifyHandler)
from qiita_pet.handlers.user_handlers import (
    ChangeForgotPasswordHandler, ForgotPasswordHandler, UserProfileHandler,
    UserMessagesHander, UserJobs)
from qiita_pet.handlers.analysis_handlers import (
    ListAnalysesHandler, AnalysisSummaryAJAX, SelectedSamplesHandler,
    AnalysisDescriptionHandler, AnalysisGraphHandler, CreateAnalysisHandler,
    AnalysisJobsHandler, ShareAnalysisAJAX)
from qiita_pet.handlers.study_handlers import (
    StudyIndexHandler, StudyBaseInfoAJAX, SampleTemplateHandler,
    SampleTemplateOverviewHandler, SampleTemplateColumnsHandler,
    StudyEditHandler, ListStudiesHandler, ListStudiesAJAX, EBISubmitHandler,
    CreateStudyAJAX, ShareStudyAJAX, StudyApprovalList, ArtifactGraphAJAX,
    VAMPSHandler, StudyTags, StudyGetTags,
    ListCommandsHandler, ListOptionsHandler, PrepTemplateSummaryAJAX,
    PrepTemplateAJAX, NewArtifactHandler, SampleAJAX, StudyDeleteAjax,
    ArtifactAdminAJAX, NewPrepTemplateAjax, DataTypesMenuAJAX, StudyFilesAJAX,
    ArtifactGetSamples, ArtifactGetInfo, WorkflowHandler,
    WorkflowRunHandler, JobAJAX, AutocompleteHandler)
from qiita_pet.handlers.artifact_handlers import (
    ArtifactSummaryAJAX, ArtifactAJAX, ArtifactSummaryHandler)
from qiita_pet.handlers.websocket_handlers import (
    MessageHandler, SelectedSocketHandler, SelectSamplesHandler)
from qiita_pet.handlers.logger_handlers import LogEntryViewerHandler
from qiita_pet.handlers.upload import UploadFileHandler, StudyUploadFileHandler
from qiita_pet.handlers.stats import StatsHandler
from qiita_pet.handlers.download import (
    DownloadHandler, DownloadStudyBIOMSHandler, DownloadRelease,
    DownloadRawData, DownloadEBISampleAccessions, DownloadEBIPrepAccessions,
    DownloadUpload)
from qiita_pet.handlers.prep_template import (
    PrepTemplateHandler, PrepTemplateGraphHandler, PrepTemplateJobHandler)
from qiita_pet.handlers.ontology import OntologyHandler
from qiita_db.handlers.processing_job import (
    JobHandler, HeartbeatHandler, ActiveStepHandler, CompleteHandler,
    ProcessingJobAPItestHandler)
from qiita_db.handlers.artifact import (
    ArtifactHandler, ArtifactAPItestHandler, ArtifactTypeHandler)
from qiita_db.handlers.sample_information import SampleInfoDBHandler
from qiita_db.handlers.user import UserInfoDBHandler, UsersListDBHandler
from qiita_db.handlers.prep_template import (
    PrepTemplateDataHandler, PrepTemplateAPItestHandler,
    PrepTemplateDBHandler)
from qiita_db.handlers.oauth2 import TokenAuthHandler
from qiita_db.handlers.reference import ReferenceHandler
from qiita_db.handlers.core import ResetAPItestHandler
from qiita_db.handlers.plugin import (
    PluginHandler, CommandHandler, CommandListHandler, CommandActivateHandler,
    ReloadPluginAPItestHandler)
from qiita_db.handlers.analysis import APIAnalysisMetadataHandler
from qiita_db.handlers.archive import APIArchiveObservations
from qiita_db.util import get_mountpoint
from qiita_pet.handlers.rest import ENDPOINTS as REST_ENDPOINTS
from qiita_pet.handlers.qiita_redbiom import RedbiomPublicSearch

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
            (r"/user/jobs/", UserJobs),
            (r"/static/(.*)", tornado.web.StaticFileHandler,
             {"path": STATIC_PATH}),
            # Analysis handlers
            (r"/analysis/list/", ListAnalysesHandler),
            (r"/analysis/dflt/sumary/", AnalysisSummaryAJAX),
            (r"/analysis/create/", CreateAnalysisHandler),
            (r"/analysis/selected/", SelectedSamplesHandler),
            (r"/analysis/selected/socket/", SelectedSocketHandler),
            (r"/analysis/description/(.*)/graph/", AnalysisGraphHandler),
            (r"/analysis/description/(.*)/jobs/", AnalysisJobsHandler),
            (r"/analysis/description/(.*)/", AnalysisDescriptionHandler),
            (r"/analysis/sharing/", ShareAnalysisAJAX),
            (r"/artifact/samples/", ArtifactGetSamples),
            (r"/artifact/info/", ArtifactGetInfo),
            (r"/consumer/", MessageHandler),
            (r"/admin/error/", LogEntryViewerHandler),
            (r"/admin/approval/", StudyApprovalList),
            (r"/admin/artifact/", ArtifactAdminAJAX),
            (r"/ebi_submission/(.*)", EBISubmitHandler),
            # Study handlers
            (r"/study/create/", StudyEditHandler),
            (r"/study/edit/(.*)", StudyEditHandler),
            (r"/study/list/", ListStudiesHandler),
            (r"/study/process/commands/options/", ListOptionsHandler),
            (r"/study/process/commands/", ListCommandsHandler),
            (r"/study/process/workflow/run/", WorkflowRunHandler),
            (r"/study/process/workflow/", WorkflowHandler),
            (r"/study/process/job/", JobAJAX),
            (r"/study/list/socket/", SelectSamplesHandler),
            (r"/study/list_studies/(.*)", ListStudiesAJAX),
            (r"/study/new_artifact/", NewArtifactHandler),
            (r"/study/files/", StudyFilesAJAX),
            (r"/study/sharing/", ShareStudyAJAX),
            (r"/study/sharing/autocomplete/", AutocompleteHandler),
            (r"/study/new_prep_template/", NewPrepTemplateAjax),
            (r"/study/tags/(.*)", StudyTags),
            (r"/study/get_tags/", StudyGetTags),
            # Artifact handlers
            (r"/artifact/graph/", ArtifactGraphAJAX),
            (r"/artifact/(.*)/summary/", ArtifactSummaryAJAX),
            (r"/artifact/html_summary/(.*)", ArtifactSummaryHandler,
             {"path": qiita_config.base_data_dir}),
            (r"/artifact/(.*)/", ArtifactAJAX),
            # Prep template handlers
            (r"/prep_template/", PrepTemplateHandler),
            (r"/prep_template/(.*)/graph/", PrepTemplateGraphHandler),
            (r"/prep_template/(.*)/jobs/", PrepTemplateJobHandler),
            (r"/ontology/", OntologyHandler),
            # ORDER FOR /study/description/ SUBPAGES HERE MATTERS.
            # Same reasoning as below. /study/description/(.*) should be last.
            (r"/study/description/sample_template/overview/",
             SampleTemplateOverviewHandler),
            (r"/study/description/sample_template/columns/",
             SampleTemplateColumnsHandler),
            (r"/study/description/sample_template/", SampleTemplateHandler),
            (r"/study/description/sample_summary/", SampleAJAX),
            (r"/study/description/prep_summary/", PrepTemplateSummaryAJAX),
            (r"/study/description/prep_template/", PrepTemplateAJAX),
            (r"/study/description/baseinfo/", StudyBaseInfoAJAX),
            (r"/study/description/data_type_menu/", DataTypesMenuAJAX),
            (r"/study/description/(.*)", StudyIndexHandler),
            (r"/study/delete/", StudyDeleteAjax),
            (r"/study/upload/(.*)", StudyUploadFileHandler),
            (r"/upload/", UploadFileHandler),
            (r"/check_study/", CreateStudyAJAX),
            (r"/stats/", StatsHandler),
            (r"/download/(.*)", DownloadHandler),
            (r"/download_study_bioms/(.*)", DownloadStudyBIOMSHandler),
            (r"/download_raw_data/(.*)", DownloadRawData),
            (r"/download_ebi_accessions/samples/(.*)",
                DownloadEBISampleAccessions),
            (r"/download_ebi_accessions/experiments/(.*)",
                DownloadEBIPrepAccessions),
            (r"/download_upload/(.*)", DownloadUpload),
            (r"/release/download/(.*)", DownloadRelease),
            (r"/vamps/(.*)", VAMPSHandler),
            (r"/redbiom/(.*)", RedbiomPublicSearch),
            (r"/iframe/", IFrame),
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
            (r"/qiita_db/artifacts/types/", ArtifactTypeHandler),
            (r"/qiita_db/artifacts/(.*)/", ArtifactHandler),
            (r"/qiita_db/users/", UsersListDBHandler),
            (r"/qiita_db/user/(.*)/data/", UserInfoDBHandler),
            (r"/qiita_db/sample_information/(.*)/data/", SampleInfoDBHandler),
            (r"/qiita_db/prep_template/(.*)/data/", PrepTemplateDataHandler),
            (r"/qiita_db/prep_template/(.*)/", PrepTemplateDBHandler),
            (r"/qiita_db/references/(.*)/", ReferenceHandler),
            (r"/qiita_db/plugins/(.*)/(.*)/commands/(.*)/activate/",
             CommandActivateHandler),
            (r"/qiita_db/plugins/(.*)/(.*)/commands/(.*)/", CommandHandler),
            (r"/qiita_db/plugins/(.*)/(.*)/commands/", CommandListHandler),
            (r"/qiita_db/plugins/(.*)/(.*)/", PluginHandler),
            (r"/qiita_db/analysis/(.*)/metadata/", APIAnalysisMetadataHandler),
            (r"/qiita_db/archive/observations/", APIArchiveObservations)

        ]

        # rest endpoints
        handlers.extend(REST_ENDPOINTS)

        if qiita_config.portal == "QIITA":
            # Add portals editing pages only on main portal
            portals = [
                (r"/admin/portals/studies/", StudyPortalHandler),
                (r"/admin/portals/studiesAJAX/", StudyPortalAJAXHandler)
            ]
            handlers.extend(portals)

        if is_test_environment():
            # We add the endpoints for testing plugins
            test_handlers = [
                (r"/apitest/processing_job/", ProcessingJobAPItestHandler),
                (r"/apitest/reset/", ResetAPItestHandler),
                (r"/apitest/prep_template/", PrepTemplateAPItestHandler),
                (r"/apitest/artifact/", ArtifactAPItestHandler),
                (r"/apitest/reload_plugins/", ReloadPluginAPItestHandler)
            ]
            handlers.extend(test_handlers)

        # 404 PAGE MUST BE LAST IN THIS LIST!
        handlers.append((r".*", NoPageHandler))

        settings = {
            "template_path": TEMPLATE_PATH,
            "debug": DEBUG,
            "cookie_secret": qiita_config.cookie_secret,
            "login_url": "%s/auth/login/" % qiita_config.portal_dir,
        }
        tornado.web.Application.__init__(self, handlers, **settings)
