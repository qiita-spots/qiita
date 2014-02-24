#!/usr/bin/env python

__author__ = "Jose Antonio Navas Molina"
__copyright__ = "Copyright 2013, The Qiita Project"
__credits__ = ["Jose Antonio Navas Molina", "Joshua Shorenstein"]
__license__ = "BSD"
__version__ = "0.1.0-dev"
__maintainer__ = "Jose Antonio Navas Molina"
__email__ = "josenavasmolina@gmail.edu"
__status__ = "Development"

from qiita_core.exceptions import QiitaJobError, IncompetentQiitaDeveloperError
from qiita_core.qiita_settings import DATATYPES, FUNCTIONS

STATUS = ("construction", "running", "completed", "internal_error",
          "user_error")


# Details are TBD - function? options?
class QiitaJob(object):
    """Models a job of Qiita"""

    def __init__(self, datatype, function, j_id=None, options=None,
                 results=None, status=None, error_msg=None):
        """"""
        self._id = j_id
        if datatype not in DATATYPES:
            raise QiitaJobError("datatype not recognized: %s" % datatype)
        self._datatype = datatype
        # Maybe options are going to be included on function (pyqi)
        # TODO sanitize options
        if function not in FUNCTIONS:
            raise QiitaJobError("function not recognized: %s" % function)
        self._function = function
        # They might be object - default to a empty dict for lazyness
        self.options = options if options else {}
        self.results = results if results else []
        self._status = status if status else "construction"
        self.error_msg = error_msg

    #override functions
    def __eq__(self, other):
        if not isinstance(other, QiitaJob):
            return False
        if (self.datatype == other.datatype
           and self.function == other.function
           and self.options == other.options):
            return True
        return False

    def __ne__(self, other):
        if not isinstance(other, QiitaJob):
            return True
        if (self.datatype == other.datatype
           and self.function == other.function
           and self.options == other.options):
            return False
        return True

    #def __hash__(self):
    #    ???????

    #define property for member variables that are immutable/need sanity checks
    @property
    def id(self):
        return self._id

    @property
    def datatype(self):
        return self._datatype

    @property
    def function(self):
        return self._function

    @property
    def status(self):
        return self._status
    @status.setter
    def status(self, status):
        if status not in STATUS:
            raise IncompetentQiitaDeveloperError("Status not allowable: %s" %
                                                 status)
        self._status = status
