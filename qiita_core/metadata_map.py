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

    def __init__(self, m_id, **kwargs):
        super(MetadataMap, self).__init__(kwargs)
        self._id = m_id

    #id is imutable
    @property
    def id(self):
        return self._id
