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


class QiitaWareError(QiitaError):
    """Base clase for all Qiita-ware exceptions"""
    pass


class UserDoesNotExistsError(QiitaWareError):
    """Error used when a user does not exist"""
    pass


class AnalysisDoesNotExistsError(QiitaWareError):
    """Error used when an analysis does not exist"""
    pass


class JobDoesNotExistsError(QiitaWareError):
    """Error used when a job does not exist"""
    pass


class StudyDoesNotExistsError(QiitaWareError):
    """Error used when a study does not exist"""
    pass


class ComputeError(QiitaWareError):
    """A compute error happened"""
    pass


class EBISubmissionError(QiitaWareError):
    """Error used when EBI cannot be submitted"""
    pass
