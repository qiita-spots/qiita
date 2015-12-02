# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from .split_libraries import split_libraries
from .split_libraries_fastq import split_libraries_fastq

__all__ = ['split_libraries', 'split_libraries_fastq']
