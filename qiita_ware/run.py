#!/usr/bin/env python
from __future__ import division

from subprocess import Popen
from tempfile import mkstemp

from qiita_db.analysis import Analysis
from qiita_db.job import Job

from qiita_core.exceptions import IncompetentQiitaDeveloperError


# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

def run_analysis(analysis):
    """ Run the commands within an Analsis object"""

    output_folder = mkstemp()
    for j in analysis.jobs:
        job = Job(j)
        if job.command == 'beta_diversity_through_plots.py':
        elif job.command == 'transform_coordinate_matrices.py':
        else:
            raise IncompetentQiitaDeveloperError("that command doesn't exist")


        print job.command, job.results, job.status
