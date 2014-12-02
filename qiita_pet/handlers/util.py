# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from __future__ import division
from functools import partial

from tornado.web import HTTPError

from qiita_pet.util import linkify


def check_access(user, study, no_public=False, raise_error=False):
    """make sure user has access to the study requested"""
    if not study.has_access(user, no_public):
        if raise_error:
            raise HTTPError(403, "User %s does not have access to study %d" %
                                 (user.id, study.id))
        else:
            return False
    return True


study_person_linkifier = partial(
    linkify, "<a target=\"_blank\" href=\"mailto:{0}\">{1}</a>")

pubmed_linkifier = partial(
    linkify, "<a target=\"_blank\" href=\"http://www.ncbi.nlm.nih.gov/"
    "pubmed/{0}\">{0}</a>")
