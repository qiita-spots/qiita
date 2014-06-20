#!/usr/bin/env python
from __future__ import division

from tempfile import mkdtemp

from qiita_db.job import Job

from qiita_ware.cluster import qiita_compute
from qiita_ware.exceptions import ComputeError


# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------


def run_analysis(analysis):
    """Run the commands within an Analysis object"""
    for job_id in analysis.jobs:
        job = Job(job_id)
        if job.status == 'queued':
            name, command = job.command
            options = job.options

            options['--output_dir'] = mkdtemp()

            o_fmt = ' '.join(['%s %s' % (k, v) for k, v in options.items()])
            c_fmt = str("echo %s %s" % (command, o_fmt))

            try:
                job.status = 'running'
                qiita_compute.submit_sync(c_fmt)
                job.add_results([(options['--output_dir'], 7)])
            except:
                job.status = 'error'
                raise ComputeError("Failed compute on job id %d" % job_id)
            else:
                job.status = 'completed'
