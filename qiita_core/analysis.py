#!/usr/bin/env python

__author__ = "Jose Antonio Navas Molina"
__copyright__ = "Copyright 2013, The Qiita Project"
__credits__ = ["Jose Antonio Navas Molina", "Joshua Shorenstein"]
__license__ = "BSD"
__version__ = "0.1.0-dev"
__maintainer__ = "Jose Antonio Navas Molina"
__email__ = "josenavasmolina@gmail.edu"
__status__ = "Development"

from qiita_core.job import QiitaJob
from qiita_core.exceptions import (QiitaAnalysisError,
                                   IncompetentQiitaDeveloperError)

STATUS = ["construction", "running", "completed", "lock"]


class QiitaAnalysis(object):
    """Models an analysis of Qiita"""

    def __init__(self, name, a_id=None, biom_table=None,
                 jobs=None, status=None, info=None):
        """Initializes the QiitaAnalysis object

        Inputs:
            name: name of the analysis
            a_id: the analysis id
            biom_table: the biom table used in the analysis
            jobs: the list of jobs run to perform the analysis
            status: current stats of the analysis
            info: a dictionary with any extra information

        Raise a IncompetentQiitaDeveloperError in any of the following cases:
            - jobs is provided and it is not a list
            - status is provided and it is not a recognized status
            - info is provided and it is not a dictionary
        """
        self._id = a_id
        self._name = name
        self._biom_table = biom_table
        # If jobs is provided, check that it is a list
        if jobs and type(jobs) is not list:
            raise QiitaAnalysisError("jobs should be a list. %s found"
                                     % type(jobs))
        self._jobs = jobs if jobs else []
        # Check that the status provided is a known status
        if status and status not in STATUS:
            raise QiitaAnalysisError("Status not recognized %s" % status)
        self._status = status if status else "construction"
        # Check that info is a dictionary
        if info and type(info) is not dict:
            raise QiitaAnalysisError("info should be a dictionary. %s found"
                                     % type(info))
        self._info = info if info else {}

    # Get functions
    def get_id(self):
        """Retrieves the analysis id"""
        return self._id

    def get_name(self):
        """Retrieves the analysis name"""
        return self._name

    def get_biom_table(self):
        """Retrieves the biom table used in the analysis"""
        return self._biom_table

    def get_jobs(self):
        """Retrieves the jobs that build up the analysis"""
        for job in self._jobs:
            yield job

    def get_status(self):
        """Retrieves the status of the analysis"""
        return self._status

    def get_info(self):
        """Retrieves the information attached to the analysis"""
        return self._info

    # Set functions
    def set_id(self, a_id):
        """Raises a QiitaAnalysisError, the analysis id can't be changed"""
        raise QiitaAnalysisError("The id of an object can't be changed")

    def set_name(self, name):
        """Sets the name of the analysis to 'name'

        Inputs:
            name: the new name for the analysis

        Raises a QiitaAnalysisError if the analysis is locked
        """
        if self._status == "lock":
            raise QiitaAnalysisError("analysis can't be changed. It's locked")
        self._name = name

    def set_biom_table(self, biom_table):
        """Sets the biom table of the analysis

        Inputs:
            biom_table: the new biom-table

        Raises a QiitaAnalysisError if the analysis is locked
        Raises a IncompetentQiitaDeveloperError if biom_table is not a
            biom-table
        """
        self._biom_table = biom_table

    def set_status(self, status):
        """ Sets the status of the analysis

        Inputs:
            status: the new status of the analysis

        Raises a QiitaAnalysisError if the analysis is locked
        Raises a IncompetentQiitaDeveloperError if status is not a recognized
            status
        """
        if self._status == "lock":
            raise QiitaAnalysisError("analysis can't be changed. It's locked")
        if status not in STATUS:
            raise IncompetentQiitaDeveloperError("Status not recognized %s" %
                                                 status)
        self._status = status

    def set_info(self, info):
        """Sets the information of the analysis

        Inputs:
            info: the dictionary with the analysis info

        Raises a QiitaAnalysisError if the analysis is locked
        Raises a IncompetentQiitaDeveloperError if info is not a dictionary
        """
        if self._status == "lock":
            raise QiitaAnalysisError("analysis can't be changed. It's locked")
        if type(info) is not dict:
            raise IncompetentQiitaDeveloperError("info should be a dictionary."
                                                 " %s found" % type(info))

    # Add/remove functions for the list attributes
    def add_job(self, job):
        """Adds a job to the analysis

        Input:
            job: a QiitaJob object

        Raises a QiitaAnalysisError if the analysis is locked
        Raises a IncompetentQiitaDeveloperError if job is not a QiitaJob object
        """
        if self._status == "lock":
            raise QiitaAnalysisError("analysis can't be changed. It's locked")
        if type(job) is not QiitaJob:
            IncompetentQiitaDeveloperError("job should be a QiitaJob: %s "
                                           "found" % type(job))
        self._jobs.append(job)

    def remove_job(self, job):
        """Removes a job from the analysis

        Input:
            job: a QiitaJob object

        Raises a QiitaAnalysisError if:
            - the analysis is locked
            - the analysis does not have the given job
        """
        if self._status == "lock":
            raise QiitaAnalysisError("analysis can't be changed. It's locked")
        try:
            self._jobs.remove(job)
        except ValueError, e:
            raise QiitaAnalysisError("The analysis does not contain job: %s"
                                     % job)
