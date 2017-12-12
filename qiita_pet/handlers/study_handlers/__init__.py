# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from .listing_handlers import (ListStudiesHandler, StudyApprovalList,
                               ShareStudyAJAX, SearchStudiesAJAX,
                               AutocompleteHandler)
from .edit_handlers import StudyEditHandler, CreateStudyAJAX
from .ebi_handlers import EBISubmitHandler
from .vamps_handlers import VAMPSHandler
from .base import (StudyIndexHandler, StudyBaseInfoAJAX, StudyDeleteAjax,
                   DataTypesMenuAJAX, StudyFilesAJAX, StudyGetTags, StudyTags)
from .prep_template import (
    PrepTemplateAJAX, PrepFilesHandler,
    NewPrepTemplateAjax, PrepTemplateSummaryAJAX)
from .processing import (ListCommandsHandler, ListOptionsHandler,
                         WorkflowHandler, WorkflowRunHandler, JobAJAX)
from .artifact import (ArtifactGraphAJAX, NewArtifactHandler,
                       ArtifactAdminAJAX, ArtifactGetSamples, ArtifactGetInfo)
from .sample_template import (
    SampleTemplateHandler, SampleTemplateOverviewHandler,
    SampleTemplateSummaryHandler, SampleAJAX)

__all__ = ['ListStudiesHandler', 'StudyApprovalList', 'ShareStudyAJAX',
           'StudyEditHandler', 'CreateStudyAJAX', 'EBISubmitHandler',
           'VAMPSHandler', 'SearchStudiesAJAX', 'ArtifactGraphAJAX',
           'ArtifactAdminAJAX', 'StudyIndexHandler', 'StudyBaseInfoAJAX',
           'SampleTemplateHandler', 'SampleTemplateOverviewHandler',
           'SampleTemplateSummaryHandler',
           'PrepTemplateAJAX', 'NewArtifactHandler', 'PrepFilesHandler',
           'ListCommandsHandler', 'ListOptionsHandler', 'SampleAJAX',
           'StudyDeleteAjax', 'NewPrepTemplateAjax',
           'DataTypesMenuAJAX', 'StudyFilesAJAX', 'PrepTemplateSummaryAJAX',
           'WorkflowHandler', 'WorkflowRunHandler',
           'JobAJAX', 'AutocompleteHandler', 'StudyGetTags', 'StudyTags',
           'ArtifactGetSamples', 'ArtifactGetInfo']
