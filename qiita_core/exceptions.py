#!/usr/bin/env python
from __future__ import division

__author__ = "Jose Antonio Navas Molina"
__copyright__ = "Copyright 2013, The Qiita Project"
__credits__ = ["Jose Antonio Navas Molina"]
__license__ = "BSD"
__version__ = "0.1.0-dev"
__maintainer__ = "Jose Antonio Navas Molina"
__email__ = "josenavasmolina@gmail.edu"
__status__ = "Development"


class QiitaError(Exception):
    """Base clase for all Qiita exceptions"""
    pass


class IncompetentQiitaDeveloperError(QiitaError):
    """Exception for developer errors"""
    pass


class QiitaSearchError(QiitaError):
    """Exception for errors when using search objects"""
    pass


class QiitaUserError(QiitaError):
    """Exception for error when handling with user objects"""
    pass


class QiitaAnalysisError(QiitaError):
    """Exception for error when handling with analysis objects"""
    pass


class QiitaJobError(QiitaError):
    """Exception for error when handling with job objects"""
    pass


class QiitaStudyError(QiitaError):
    """Exception for error when handling with study objects"""
    pass
