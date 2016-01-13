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
from qiita_core.util import execute_as_transaction


@execute_as_transaction
def check_access(user, study, no_public=False, raise_error=False):
    """make sure user has access to the study requested"""
    if not study.has_access(user, no_public):
        if raise_error:
            raise HTTPError(403, "User %s does not have access to study %d" %
                                 (user.id, study.id))
        else:
            return False
    return True


def download_link_or_path(is_local_request, filepath, fp_id, label):
    """Generates a download link or shows the path based on is_local_request

    Parameters
    ----------
    is_local_request : bool
        Whether the request is local or not
    filepath : str
        The local filepath
    fp_id : int
        The filepath id
    label : str
        The label to show in the button

    Returns
    -------
    str
        If is a local request, a string with the filepath. Otherwise a string
        with the html code to create a download link
    """
    if is_local_request:
        resp = "<b>%s:</b> %s" % (label, filepath)
    else:
        resp = ('<a class="btn btn-default glyphicon glyphicon-download-alt" '
                'href="/download/%s" style="word-spacing: -10px;"> %s</a>'
                % (fp_id, label))
    return resp


study_person_linkifier = partial(
    linkify, "<a target=\"_blank\" href=\"mailto:{0}\">{1}</a>")

pubmed_linkifier = partial(
    linkify, "<a target=\"_blank\" href=\"http://www.ncbi.nlm.nih.gov/"
    "pubmed/{0}\">{0}</a>")

doi_linkifier = partial(
    linkify, "<a target=\"_blank\" href=\"http://dx.doi.org/{0}\">{0}</a>")
