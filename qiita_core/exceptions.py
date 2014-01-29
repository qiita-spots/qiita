#!/usr/bin/env python

__author__ = "Jose Antonio Navas Molina"
__copyright__ = "Copyright 2013, The QiiTa Project"
__credits__ = ["Jose Antonio Navas Molina"]
__license__ = "BSD"
__version__ = "0.1.0-dev"
__maintainer__ = "Jose Antonio Navas Molina"
__email__ = "josenavasmolina@gmail.edu"
__status__ = "Development"


class QiiTaError(Exception):
    """Base clase for all QiiTa exceptions"""
    pass


class IncompetentQiiTaDeveloper(QiiTaError):
    """Exception for developer errors"""
    pass


class QiiTaSearchError(QiiTaError):
    """Exception for errors when using search objects"""
    pass


class QiiTaUserError(QiiTaError):
    """Exception for error when handling with user objects"""
    pass


class QiiTaAnalysisError(QiiTaError):
    """Exception for error when handling with analysis objects"""
    pass


class QiitaJobError(QiiTaError):
    """Exception for error when handling with job objects"""
    pass


class QiiTaStudyError(QiiTaError):
    """Exception for error when handling with study objects"""
    pass
