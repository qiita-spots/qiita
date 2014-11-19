# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from __future__ import division
from qiita_core.exceptions import QiitaError


class QiitaPetAuthorizationError(QiitaError):
    """When a user tries to access a resource without proper authorization"""
    def __init__(self, user_id, resource_name_str):
        super(QiitaPetAuthorizationError, self).__init__()
        self.args = ("User %s is not authorized to access %s"
                     % (user_id, resource_name_str),)
