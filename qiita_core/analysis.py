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
from qiita_db import AnalysisStorage

STATUS = ("construction", "running", "completed", "lock")


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
        self.name = name
        self.biom_table = biom_table
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
        if info and not isinstance(info, dict):
            raise QiitaAnalysisError("info should be a dictionary. %s found"
                                     % type(info))
        self._info = info if info else {}

    #override functions
    #def __eq__(self):
    #def __ne__(self):
    #def __hash__(self):

    #properties for immutable and enum-type member variables
    @property
    def id(self):
        return self._id

    @property
    def status(self):
        #explanation b/c AnalysisStorage object not fleshed out yet.
        return self._status

    @status.setter
    def status(self, status):
        #makes sure status is a recognised type
        if status not in STATUS:
            raise IncompetentQiitaDeveloperError("Status not recognized %s" %
                                                 status)
        if self._status != status:
            self._status = status
            self.update_analysis_DB()

    #class-specific functions
    def update_analysis_DB(self):
        #This needs to be API-ed
        #Explanaiton below b/c the AnalysisStorage object isn't fleshed out yet

        #sends this analysis object back to the DB to update what is in there
        pass


    #Functions for the list and dict attributes
    def add_job(self, job):
        """Adds a job to the analysis
        Raises a QiitaAnalysisError if the analysis is locked
        Raises a IncompetentQiitaDeveloperError if job is not a QiitaJob object
        """
        if not isinstance(job, QiitaJob):
            IncompetentQiitaDeveloperError("job should be a QiitaJob: %s "
                                           "found" % type(job))
        if job not in self._jobs:
            self._jobs.append(job)
        else:
            raise QiitaAnalysisError("Adding a copy of an existing job!")

    def remove_job(self, job):
        """Removes a job from the analysis

        Input:
            job: a QiitaJob object

        Raises a QiitaAnalysisError if the analysis does not have the given job
        """
        try:
            self._jobs.remove(job)
        except ValueError:
            raise QiitaAnalysisError("The analysis does not contain job: %s"
                                     % job)

    def get_jobs(self, job):
        """Yields each job in the analysis"""
        for job in self._jobs:
            yield job

    def add_info(self, info):
        """Adds dictionary of info to existing info dictionary
        Input:
            info: dictionary of information to add
        NOTE: Overwrites any key already in the dictionary!
        """
        if not isinstance(info, dict):
            raise IncompetentQiitaDeveloperError("info must be a dictionary!")
        self._info.update(info)

    def remove_info(self, keys):
        """ Removes information in keys from the info stored
        Input:
            keys: single key or list of keys to remove from information dict
        """
        if not isinstance(keys, list):
            keys = [keys]
        for key in keys:
            try:
                self._info.pop(key)
            except KeyError:
                raise QiitaAnalysisError("Key not in info: %s" % key)

    def get_info(self):
        """Yields each item in info as two variables: key, info """
        for item in self._info:
            yield item, self._info[item]
