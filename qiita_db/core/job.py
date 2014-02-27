"""
Objects for dealing with Qiita jobs

This module provides the base object for dealing with Qiita jobs.
It standardizes the Jobs interface and all the different Qiita-db
backends should inherit from it in order to implement the job object.

The subclasses implementing this object should not provide any extra
public function in order to maintain back-end independence.

Classes
-------
- `QiitaJob` -- A Qiita Job class
"""
__author__ = "Jose Antonio Navas Molina"
__copyright__ = "Copyright 2013, The Qiita Project"
__credits__ = ["Jose Antonio Navas Molina", "Joshua Shorenstein"]
__license__ = "BSD"
__version__ = "0.1.0-dev"
__maintainer__ = "Jose Antonio Navas Molina"
__email__ = "josenavasmolina@gmail.edu"
__status__ = "Development"

from .base import QiitaStatusObject
from .exceptions import QiitaDBNotImplementedError


class QiitaJob(QiitaStatusObject):
    """
    Base analysis object to access to the Qiita Job information

    Standardizes the QiitaJob interface for all the back-ends.

    Parameters
    ----------
    id:
        The job identifier

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
