# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

import pandas as pd

from .metadata_template import SampleTemplate
from .study import Study


def sample_template_adder(sample_temp_path, study_id):
    r"""Adds a sample template to the database

    Parameters
    ----------
    sample_temp_path : str
        Path to the sample template file
    study_id : int
        The study id to wich the sample template belongs to
    """
    sample_temp = pd.DataFrame.from_csv(sample_temp_path, sep='\t',
                                        infer_datetime_format=True)
    return SampleTemplate.create(sample_temp, Study(study_id))
