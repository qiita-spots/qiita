# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

__version__ = "0.2.0-dev"

from .prep_template import study_prep_proxy
from .sample_template import (
    process_sample_template, update_sample_template, sample_template_info,
    delete_sample_template, get_sample_template_filepaths)
from .studies import study_data_types_proxy, study_info_proxy

__all__ = ['study_prep_proxy', 'process_sample_template',
           'update_sample_template', 'study_data_types_proxy',
           'study_info_proxy', 'sample_template_info',
           'delete_sample_template', 'get_sample_template_filepaths']
