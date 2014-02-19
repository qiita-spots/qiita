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
        self._options = options if options else {}
        self._results = results if results else []
        self._status = status if status else "construction"
        self._error_msg = error_msg

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
                    raise QiitaJobError("Job can't be changed. %s" %
                                        dec_self._status)
                return f(*args, **kwargs)
            return decorator

    #override functions
    def __eq__(self, other):
        if type(other) != QiitaJob:
            return False
        if (self.datatype == other.datatype
           and self.function == other.function
           and self._options == other._options
           and self._status == other._status
           and self._results == other._results
           and self._error_msg == other._error_msg):
            return True
        return False

    def __neq__(self, other):
        if type(other) != QiitaJob:
            return True
        if (self.datatype == other.datatype
           and self.function == other.function
           and self._options == other._options
           and self._status == other._status
           and self._results == other._results
           and self._error_msg == other._error_msg):
            return False
        return True

    # define get and set, and add/remove for results and update option
    @property
    def id(self):
        """  """
        return self._id

    @property
    def datatype(self):
        """  """
        return self._datatype

    @property
    def function(self):
        """  """
        return self._function

    @property
    def options(self):
        """  """
        return self._options
    @options.setter
    @verify_not_status(["completed", "user_error", "internal_error"])
    def options(self, opts):
        """  """
        self._options = opts

    @property
    def results(self):
        """  """
        return self._results
    @results.setter
    @verify_not_status(["completed", "user_error", "internal_error"])
    def results(self, results):
        """  """
        self._results = results

    @property
    def status(self):
        """  """
        return self._status
    @status.setter
    @verify_not_status(["completed", "user_error", "internal_error"])
    def status(self, status):
        """  """
        if status not in STATUS:
            raise IncompetentQiitaDeveloperError("Status not allowable: %s" %
                                                 status)
        self._status = status

    @property
    def error_msg(self):
        """  """
        return self._error_msg
    @error_msg.setter
    @verify_not_status(["completed", "user_error", "internal_error"])
    def error_msg(self, error_msg):
        """  """
        self._error_msg = error_msg
