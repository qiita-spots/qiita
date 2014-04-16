#!/usr/bin/env python
from __future__ import division

__author__ = "Jose Antonio Navas Molina"
__copyright__ = "Copyright 2013, The Qiita Project"
__credits__ = ["Jose Antonio Navas Molina"]
__license__ = "BSD"
__version__ = "0.0.1-dev"
__maintainer__ = "Jose Antonio Navas Molina"
__email__ = "josenavasmolina@gmail.edu"
__status__ = "Development"

from qiita.core.exceptions import QiitaError


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
