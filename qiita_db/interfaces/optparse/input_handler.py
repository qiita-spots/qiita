#!/usr/bin/env python
from __future__ import division

# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from qiime.util import MetadataMap


def load_mapping_file(mapping_fp):
    """Loads the mapping file information stored in the file mapping_fp

    Returns:
        A qiime.util.MetadataMap object
    """
    # Parse the mapping file contents
    with open(mapping_fp, 'U') as map_lines:
        return MetadataMap.parseMetadataMap(map_lines)
