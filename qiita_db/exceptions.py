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


class QiitaDBConnectionError(QiitaDBError):
    """Exception for error when connecting to the db"""
    pass
