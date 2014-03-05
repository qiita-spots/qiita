"""
Objects for dealing with Qiita jobs

This module provides the implementation of the Job class, which allows
to interact with the SQL backend

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

from .base import QiitaStatusObject
from .exceptions import QiitaDBNotImplementedError


class Job(QiitaStatusObject):
    """
    Job object to access to the Qiita Job information

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

    @staticmethod
    def create(datatype, function, analysis):
        """Creates a new job on the storage system

        Parameters
        ----------
        datatype : string
            The datatype in which this job applies
        function : string
            The identifier of the function executed in this job
        analysis : string
            The analysis which this job belongs to
        """
        raise QiitaDBNotImplementedError()

    @staticmethod
    def delete(id_):
        """Deletes the object `id` from the storage system

        Parameters
        ----------
        id_ :
            The object identifier
        """
        raise QiitaDBNotImplementedError()

    @property
    def Datatype(self):
        """The datatype of the job"""
        raise QiitaDBNotImplementedError()

    @property
    def Function(self):
        """The function the job executes"""
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
