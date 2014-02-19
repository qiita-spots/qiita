#!/usr/bin/env python

__author__ = "Jose Antonio Navas Molina"
__copyright__ = "Copyright 2013, The Qiita Project"
__credits__ = ["Jose Antonio Navas Molina", "Joshua Shorenstein"]
__license__ = "BSD"
__version__ = "0.1.0-dev"
__maintainer__ = "Jose Antonio Navas Molina"
__email__ = "josenavasmolina@gmail.edu"
__status__ = "Development"

from qiita.core.exceptions import QiitaStudyError

STATUS = ['proposed', 'private', 'public']


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
        self._name = name
        if not isinstance(sample_ids, list):
            raise QiitaStudyError("samples should be a list")
        self._samples = sample_ids
        if status and status not in STATUS:
            raise QiitaStudyError("status not recognized: %s" % status)
        self._status = status if status else "proposed"

    #decorators
    class verify_not_status(object):
        def __init__(self, statuses):
            if isinstance(statuses, list):
                self.statuses = statuses
            else:
                self.statuses = [statuses]

        def __call__(self, f):
            def decorator(dec_self, *args, **kwargs):
                if dec_self._status in self.statuses:
                    # bail
                    raise QiitaStudyError("Job can't be changed. %s" %
                                          dec_self._status)
                return f(*args, **kwargs)
            return decorator

    #properties
    @property
    def id(self):
        return self._id

    @property
    def name(self):
        return self._name
    @name.setter
    @verify_not_status(["public", "private"])
    def name(self, value):
        self._name = value

    @property
    def samples(self):
        return self._samples
    @samples.setter
    @verify_not_status(["public", "private"])
    def samples(self, value):
        self._samples = value

    @property
    def status(self):
        return self._status
    @status.setter
    @verify_not_status(["public", "private"])
    def status(self, value):
        self._status = value

    #add/rem from lists
    @verify_not_status(["public", "private"])
    def add_sample(self, sample):
        self._samples.append(sample)

    @verify_not_status(["public", "private"])
    def remove_sample(self, sample):
        try:
            self._samples.remove(sample)
        except ValueError:
            raise QiitaStudyError("The study does not contain sample: %s"
                                  % sample)
