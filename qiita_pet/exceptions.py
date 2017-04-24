# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from __future__ import division

from tornado.web import HTTPError

from qiita_core.exceptions import QiitaError


class QiitaHTTPError(HTTPError):
    def __init__(self, status_code=500, log_message=None, *args, **kwargs):
        super(QiitaHTTPError, self).__init__(
            status_code, log_message, *args, **kwargs)
        # The HTTPError has an attribute named "reason" that will get send to
        # the requester if specified. However, the developer need to
        # specifically pass the keyword "reason" when raising the exception.
        # The vast majority of our code it is not using the keyword "reason"
        # but we are using "log_message". By setting up the attribute reason
        # with the value in log_message, we make sure that when the answer
        # is sent to the requester, it will contain a useful error message,
        # rather than a generic error message.
        if not self.reason:
            self.reason = log_message


class QiitaPetAuthorizationError(QiitaError):
    """When a user tries to access a resource without proper authorization"""
    def __init__(self, user_id, resource_name_str):
        super(QiitaPetAuthorizationError, self).__init__()
        self.args = ("User %s is not authorized to access %s"
                     % (user_id, resource_name_str),)
