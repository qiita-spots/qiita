# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from __future__ import division
from qiita_core.exceptions import QiitaError


class QiitaDBError(QiitaError):
    """Base class for all qiita_db exceptions"""
    pass


class QiitaDBNotImplementedError(QiitaDBError):
    """"""
    pass


class QiitaDBExecutionError(QiitaDBError):
    """Exception for error when executing SQL queries"""
    pass


class QiitaDBConnectionError(QiitaDBError):
    """Exception for error when connecting to the db"""
    pass


class QiitaDBColumnError(QiitaDBError):
    """Exception when missing table information or excess information passed"""
    pass


class QiitaDBDuplicateError(QiitaDBError):
    """Exception when duplicating something in the database"""
    pass


class QiitaDBStatusError(QiitaDBError):
    """Exception when editing is done with an unallowed status"""
    pass


class QiitaDBUnknownIDError(QiitaDBError):
    """Exception for error when an object does not exists in the DB"""
    def __init__(self, missing_id, table):
        super(QiitaDBUnknownIDError, self).__init__()
        self.args = ("The object with ID '%s' does not exists in table '%s"
                     % (missing_id, table),)
