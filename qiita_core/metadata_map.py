#!/usr/bin/env python

__author__ = "Jose Antonio Navas Molina"
__copyright__ = "Copyright 2013, The Qiita Project"
__credits__ = ["Jose Antonio Navas Molina"]
__license__ = "BSD"
__version__ = "0.1.0-dev"
__maintainer__ = "Jose Antonio Navas Molina"
__email__ = "josenavasmolina@gmail.edu"
__status__ = "Development"

from qiime.util import MetadataMap as QiimeMetadataMap


class MetadataMap(QiimeMetadataMap):
    """Extends the MetadataMap to include the id_ attribute"""

    def __init__(self, **kwargs):
        super(MetadataMap, self).__init__(kwargs)
        self._id = None

    def set_id(self, study_id, num):
        """Set the MetadataMap id"""
        self._id = (study_id, num)

    def get_id(self):
        """Returns the id of the MetadataMap"""
        return self._id
