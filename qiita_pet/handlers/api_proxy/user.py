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
def user_jobs_get_req(user):
    """Gets the json of jobs

    Parameters
    ----------
    prep_id : int
        PrepTemplate id to get info for
    user_id : str
        User requesting the sample template info

    Returns
    -------
    dict of objects
    {'status': status,
     'message': message,
     'template': {sample: {column: value, ...}, ...}
    """

    response = []
    cmds = {}
    for j in user.jobs():
        cmd = j.command
        if cmd not in cmds:
            cmds[cmd] = cmd
        ccmd = cmds[cmd]
        hb = j.heartbeat
        hb = "" if hb is None else hb.strftime("%Y-%m-%d %H:%M:%S")
        pjw = j.processing_job_worflow
        wid = '' if pjw is None else pjw.id
        response.append({
            'id': j.id,
            'name': ccmd.name,
            'params': j.parameters.values,
            'status': j.status,
            'heartbeat': hb,
            'processing_job_workflow_id': wid})

    return {'status': 'success',
            'message': '',
            'jobs': response}
