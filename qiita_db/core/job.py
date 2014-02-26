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

from .base_object import QiitaStatusObject
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
    datatype
    function
    options
    results
    error_msg

    Methods
    -------
    add_results(results)
        Adds a list of results to the results

    remove_results(results)
        Removes a list of results from the results
    """

    @property
    def datatype(self):
        """The datatype of the job"""
        raise QiitaDBNotImplementedError()

    @property
    def function(self):
        """The function the job executes"""
        raise QiitaDBNotImplementedError()

    @property
    def options(self):
        """List of options used in the job"""
        raise QiitaDBNotImplementedError()

    @options.setter
    def options(self, options):
        """Updates the options used in the job

        Parameters
        ----------
            options : list
        """
        raise QiitaDBNotImplementedError()

    @property
    def results(self):
        """List of job results"""
        raise QiitaDBNotImplementedError()

    @property
    def error_msg(self):
        """String with an error message, if the job failed"""
        raise QiitaDBNotImplementedError()

    @error_msg.setter
    def error_msg(self, msg):
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
