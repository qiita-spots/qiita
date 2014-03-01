"""
Objects for dealing with job objects within an SQL backend

This module provides the implementation for the QiitaJob base class using an
SQL backend

Classes
-------
- `Job` -- A Qiita Job class
"""
__author__ = "Jose Antonio Navas Molina"
__copyright__ = "Copyright 2013, The Qiita Project"
__credits__ = ["Jose Antonio Navas Molina", "Joshua Shorenstein"]
__license__ = "BSD"
__version__ = "0.1.0-dev"
__maintainer__ = "Jose Antonio Navas Molina"
__email__ = "josenavasmolina@gmail.edu"
__status__ = "Development"

from ...core.job import QiitaJob
from ...core.exceptions import QiitaDBNotImplementedError


class Job(QiitaJob):
    """
    Base analysis object to access to the Qiita Job information

    Standardizes the QiitaJob interface for all the back-ends.

    Attributes
    ----------
    Datatype
    Function
    Options
    Results
    ErrorMsg

    Methods
    -------
    add_results(results)
        Adds a list of results to the results

    remove_results(results)
        Removes a list of results from the results
    """

    @property
    def Datatype(self):
        """The datatype of the job"""
        raise QiitaDBNotImplementedError()

    @Datatype.setter
    def Datatype(self, datatype):
        """Updates the datatype of the job

        Parameters
        ----------
            datatype :
        """
        raise QiitaDBNotImplementedError()

    @property
    def Function(self):
        """The function the job executes"""
        raise QiitaDBNotImplementedError()

    @Function.setter
    def Function(self, function):
        """Updates the function used in the job

        Parameters
        ----------
            function :
        """
        raise QiitaDBNotImplementedError()

    @property
    def Options(self):
        """List of options used in the job"""
        raise QiitaDBNotImplementedError()

    @Options.setter
    def Options(self, options):
        """Updates the options used in the job

        Parameters
        ----------
            options : list
        """
        raise QiitaDBNotImplementedError()

    @property
    def Results(self):
        """List of job results"""
        raise QiitaDBNotImplementedError()

    @property
    def ErrorMsg(self):
        """String with an error message, if the job failed"""
        raise QiitaDBNotImplementedError()

    @ErrorMsg.setter
    def ErrorMsg(self, msg):
        """String with an error message, if the job failed

        Parameters
        ----------
            msg : String
                Error message
        """
        raise QiitaDBNotImplementedError()

    def add_results(self, results):
        """Adds a list of results to the results

        Parameters
        ----------
            results : list
                results to be added to the job
        """
        raise QiitaDBNotImplementedError()

    def remove_results(self, results):
        """Removes a list of results from the results

        Parameters
        ----------
            results : list
                results to be removed from the job
        """
        raise QiitaDBNotImplementedError()
