#!/usr/bin/env python
from __future__ import division

"""
Objects for dealing with Qiita jobs

This module provides the implementation of the Job class.

Classes
-------
- `Job` -- A Qiita Job class
"""
# -----------------------------------------------------------------------------
# Copyright (c) 2014, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from .base import QiitaStatusObject
from .exceptions import QiitaDBNotImplementedError


class Job(QiitaStatusObject):
    """
    Job object to access to the Qiita Job information

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
