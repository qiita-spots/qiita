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

    #decorators
    class verify_not_status(object):
        def __init__(self, status):
            self.status = status

        def __call__(self, f):
            def decorator(dec_self, *args, **kwargs):
                if dec_self._status != self.status:
                    # bail
                    raise QiitaAnalysisError("Analysis is locked!")
                return f(*args, **kwargs)
            return decorator

    # Get functions
    @property
    def id(self):
        """Retrieves the analysis id"""
        return self._id

    @property
    def name(self):
        """Retrieves the analysis name"""
        return self._name
    @name.setter
    @verify_not_status("lock")
    def name(self, name):
        self._name = name

    @property
    def biom_table(self):
        """Retrieves the biom table used in the analysis"""
        return self._biom_table
    @biom_table.setter
    @verify_not_status("lock")
    def biom_table(self, biom_table):
        self._biom_table = biom_table

    @property
    def jobs(self):
        """Retrieves the jobs that build up the analysis"""
        for job in self._jobs:
            yield job
    @jobs.setter
    @verify_not_status("locked")
    def jobs(self, jobs):
        self._jobs = jobs

    @property
    def status(self):
        """Retrieves the status of the analysis"""
        return self._status
    @status.setter
    @verify_not_status("lock")
    def status(self, status):
        """ Sets the status of the analysis
        Raises a QiitaAnalysisError if the analysis is locked
        Raises a IncompetentQiitaDeveloperError if status is not a recognized
            status
        """
        if status not in STATUS:
            raise IncompetentQiitaDeveloperError("Status not recognized %s" %
                                                 status)
        self._status = status

    @property
    def info(self):
        """Retrieves the information attached to the analysis"""
        return self._info
    @info.setter
    @verify_not_status("lock")
    def info(self, info):
        """Sets the information of the analysis
        Raises a QiitaAnalysisError if the analysis is locked
        Raises a IncompetentQiitaDeveloperError if info is not a dictionary
        """
        if type(info) is not dict:
            raise IncompetentQiitaDeveloperError("info should be a dictionary."
                                                 " %s found" % type(info))
        self._info = info

    # Add/remove functions for the list attributes
    @verify_not_status("lock")
    def add_job(self, job):
        """Adds a job to the analysis
        Raises a QiitaAnalysisError if the analysis is locked
        Raises a IncompetentQiitaDeveloperError if job is not a QiitaJob object
        """
        if type(job) is not QiitaJob:
            IncompetentQiitaDeveloperError("job should be a QiitaJob: %s "
                                           "found" % type(job))
        self._jobs.append(job)

    @verify_not_status("lock")
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
