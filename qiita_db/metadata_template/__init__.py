# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

__version__ = "0.0.1-dev"

from .metadata_template import (SampleTemplate, PrepTemplate,
                                load_template_to_dataframe,
                                TARGET_GENE_DATA_TYPES)

__all__ = ['SampleTemplate', 'PrepTemplate', 'load_template_to_dataframe',
           'TARGET_GENE_DATA_TYPES']
