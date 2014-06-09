#!/usr/bin/env python
from __future__ import division

# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

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


class QiitaDBStatusError(QiitaDBError):
    """Exception for error when trying to run dissalowed functions"""
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
