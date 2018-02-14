# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from tornado.web import HTTPError


def check_analysis_access(user, analysis):
    """Checks whether user has access to an analysis

    Parameters
    ----------
    user : User object
        User to check
    analysis : Analysis object
        Analysis to check access for

    Raises
    ------
    RuntimeError
        Tried to access analysis that user does not have access to
    """
    if not analysis.has_access(user):
        raise HTTPError(403, reason="Analysis access denied to %s" % (
            analysis.id))
