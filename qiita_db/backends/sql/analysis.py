"""
Objects for dealing with analysis objects within an SQL backend

This module provides the implementation for the QiitaAnalysis base class
using an SQL backend

Classes
-------
- `Analysis` -- A Qiita Analysis class
"""

__author__ = "Jose Antonio Navas Molina"
__copyright__ = "Copyright 2013, The Qiita Project"
__credits__ = ["Jose Antonio Navas Molina", "Joshua Shorenstein"]
__license__ = "BSD"
__version__ = "0.1.0-dev"
__maintainer__ = "Jose Antonio Navas Molina"
__email__ = "josenavasmolina@gmail.edu"
__status__ = "Development"

from ...core.analysis import QiitaAnalysis
from ...core.exceptions import QiitaDBNotImplementedError


class Analysis(QiitaAnalysis):
    """
    Base analysis object to access to the Qiita Analysis information

    Standardizes the QiitaAnalysis interface for all the back-ends.

    Attributes
    ----------
    BiomTable
    Jobs
    Info

    Methods
    -------
    add_jobs(jobs)
        Adds a list of jobs to the analysis

    remove_jobs(jobs)
        Removes a list of jobs from the analysis

    """

    @property
    def BiomTable(self):
        """The biom table of the analysis"""
        raise QiitaDBNotImplementedError()

    @BiomTable.setter
    def BiomTable(self, biom_table):
        """Updates the biom table used in the analysis

        Parameters
        ----------
            biom_table :
        """
        raise QiitaDBNotImplementedError()

    @property
    def Jobs(self):
        """A list of jobs included in the analysis"""
        raise QiitaDBNotImplementedError()

    @property
    def Info(self):
        """Dict with any other information attached to the analysis"""
        raise QiitaDBNotImplementedError()

    @Info.setter
    def Info(self, info):
        """Updates the information attached to the analysis

        Parameters
        ----------
            info : dict
        """
        raise QiitaDBNotImplementedError()

    def add_jobs(self, jobs):
        """Adds a list of jobs to the analysis

        Parameters
        ----------
            jobs : list of QiitaJob
        """
        raise QiitaDBNotImplementedError()

    def remove_jobs(self, jobs):
        """Removes a list of jobs from the analysis

        Parameters
        ----------
            jobs : list of QiitaJob
        """
        raise QiitaDBNotImplementedError()
