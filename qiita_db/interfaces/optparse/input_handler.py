#!/usr/bin/env python
from __future__ import division

__author__ = "Jose Antonio Navas Molina"
__copyright__ = "Copyright 2013, The Qiita project"
__credits__ = ["Jose Antonio Navas Molina", "Adam Robbins-Pianka"]
__license__ = "BSD"
__version__ = "0.1.0-dev"
__maintainer__ = "Jose Antonio Navas Molina"
__email__ = "josenavasmolina@gmail.com"

from qiime.util import MetadataMap as QiimeMetadataMap


def load_mapping_file(mapping_fp):
    """Loads the mapping file information stored in the file mapping_fp

    Returns:
        A qiime.util.MetadataMap object
    """
    # Parse the mapping file contents
    with open(mapping_fp, 'U') as map_lines:
        return QiimeMetadataMap.parseMetadataMap(map_lines)
