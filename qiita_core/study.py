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
        self._id = s_id
        self._name = name
        if type(samples) is not list:
            raise QiitaStudyError("samples should be a list")
        self._samples = samples
        if status and status not in STATUS:
            raise QiitaStudyError("status not recognized: %s" % status)
        self.status = status if status else "proposed"

    # All the set/get add/remove samples - be sure to check study status
