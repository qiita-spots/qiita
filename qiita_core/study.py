#!/usr/bin/env python

__author__ = "Jose Antonio Navas Molina"
__copyright__ = "Copyright 2013, The Qiita Project"
__credits__ = ["Jose Antonio Navas Molina", "Joshua Shorenstein"]
__license__ = "BSD"
__version__ = "0.1.0-dev"
__maintainer__ = "Jose Antonio Navas Molina"
__email__ = "josenavasmolina@gmail.edu"
__status__ = "Development"

from qiita.core.exceptions import (QiitaStudyError,
                                   IncompetentQiitaDeveloperError)

STATUS = ('proposed', 'private', 'public')


# TBD
class QiitaStudy(object):
    """Models a study of Qiita"""

    def __init__(self, name, study_id=None, sample_ids=None, status=None):
        """Initializes the QiitaStudy object

        Inputs:
            name:
            study_id:
            sample_ids:
            status:
        """
        self._id = study_id
        self.name = name
        if not isinstance(sample_ids, list):
            raise QiitaStudyError("samples should be a list")
        self._samples = sample_ids
        if status and status not in STATUS:
            raise QiitaStudyError("status not recognized: %s" % status)
        self._status = status if status else "proposed"

    #properties
    @property
    def id(self):
        return self._id

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, status):
        if status not in STATUS:
            raise IncompetentQiitaDeveloperError("Status not allowable: %s" %
                                                 status)
        self._status = status

    #functions for samples
    def add_sample(self, sample):
        """  """
        pass

    def remove_sample(self, sample):
        try:
            self._samples.remove(sample)
        except ValueError:
            raise QiitaStudyError("The study does not contain sample: %s"
                                  % sample)

    def get_samples(self):
        """  """
        for sample in self._samples:
            yield sample
