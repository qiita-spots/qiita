#!/usr/bin/env python

__author__ = "Jose Antonio Navas Molina"
__copyright__ = "Copyright 2013, The QiiTa Project"
__credits__ = ["Jose Antonio Navas Molina", "Joshua Shorenstein"]
__license__ = "BSD"
__version__ = "0.1.0-dev"
__maintainer__ = "Jose Antonio Navas Molina"
__email__ = "josenavasmolina@gmail.edu"
__status__ = "Development"

from qiita.core.exceptions import QiiTaStudyError

STATUS = ['proposed', 'private', 'public']


# TBD
class QiiTaStudy(object):
    """Models a study of QiiTa"""

    def __init__(self, name, study_id=None, sample_ids=None, status=None):
        """Initializes the QiiTaStudy object

        Inputs:
            name:
            study_id:
            sample_ids:
            status:
        """
        self._id = s_id
        self._name = name
        if type(samples) is not list:
            raise QiiTaStudyError("samples should be a list")
        self._samples = samples
        if status and status not in STATUS:
            raise QiiTaStudyError("status not recognized: %s" % status)
        self.status = status if status else "proposed"

    # All the set/get add/remove samples - be sure to check study status
