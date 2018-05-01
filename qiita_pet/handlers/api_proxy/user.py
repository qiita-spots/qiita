# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from __future__ import division

from qiita_core.util import execute_as_transaction


@execute_as_transaction
def user_jobs_get_req(user, limit=30):
    """Gets the json of jobs

    Parameters
    ----------
    user : User
        The user from which you want to return all jobs
    limit : int, optional
        Maximum jobs to send, negative values will return all

    Returns
    -------
    dict of objects
    {'status': status,
     'message': message,
     'jobs': {{column: value, ...}, ...}
    """

    response = []
    for i, j in enumerate(user.jobs(limit=limit)):
        name = j.command.name
        hb = j.heartbeat
        hb = "" if hb is None else hb.strftime("%Y-%m-%d %H:%M:%S")
        pjw = j.processing_job_workflow
        wid = '' if pjw is None else pjw.id
        response.append({
            'id': j.id,
            'name': name,
            'params': j.parameters.values,
            'status': j.status,
            'heartbeat': hb,
            'step': j.step,
            'processing_job_workflow_id': wid})

    return {'status': 'success',
            'message': '',
            'jobs': response}
