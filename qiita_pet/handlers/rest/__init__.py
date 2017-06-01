# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from .study import StudyHandler, StudyCreatorHandler, StudyStatusHandler
from .study_samples import (StudySamplesHandler, StudySamplesInfoHandler,
                            StudySamplesCategoriesHandler)
from .study_person import StudyPersonHandler
from .study_preparation import (StudyPrepCreatorHandler,
                                StudyPrepArtifactCreatorHandler)


__all__ = ['StudyHandler', 'StudySamplesHandler', 'StudySamplesInfoHandler',
           'StudySamplesCategoriesHandler', 'StudyPersonHandler',
           'StudyCreatorHandler', 'StudyPrepCreatorHandler',
           'StudyPrepArtifactCreatorHandler', 'StudyStatusHandler']


ENDPOINTS = (
    (r"/api/v1/study$", StudyCreatorHandler),
    (r"/api/v1/study/([0-9]+)$", StudyHandler),
    (r"/api/v1/study/([0-9]+)/samples/categories=([a-zA-Z\-0-9\.:,_]*)",
        StudySamplesCategoriesHandler),
    (r"/api/v1/study/([0-9]+)/samples", StudySamplesHandler),
    (r"/api/v1/study/([0-9]+)/samples/info", StudySamplesInfoHandler),
    (r"/api/v1/person(.*)", StudyPersonHandler),
    (r"/api/v1/study/([0-9]+)/preparation/([0-9]+)/artifact",
        StudyPrepArtifactCreatorHandler),
    (r"/api/v1/study/([0-9]+)/preparation(.*)", StudyPrepCreatorHandler),
    (r"/api/v1/study/([0-9]+)/status$", StudyStatusHandler)
)
