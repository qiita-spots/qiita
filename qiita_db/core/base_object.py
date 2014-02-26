#!/usr/bin/env python

__author__ = "Jose Antonio Navas Molina"
__copyright__ = "Copyright 2013, The Qiita Project"
__credits__ = ["Jose Antonio Navas Molina"]
__license__ = "BSD"
__version__ = "0.1.0-dev"
__maintainer__ = "Jose Antonio Navas Molina"
__email__ = "josenavasmolina@gmail.edu"
__status__ = "Development"


class QiitaObject(object):
    """Models an object of Qiita"""

    def __init__(self, id_):
        """Initializes the object

        Parameters
        ----------
        _id: the object identifier
        """
        self._id = id_

    @property
    def id(self):
        """The id of the analysis in the storage system"""
        return self.id_
