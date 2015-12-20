# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from __future__ import division

# This is the only folder in qiita_pet that should import outside qiita_pet
# The idea is that this proxies the call and response dicts we expect from the
# Qiita API once we build it. This will be removed and replaced with API calls
# when the API is complete.
from qiita_db.study import Study
from qiita_db.user import User


def study_prep_proxy(study_id, user_id):
    """Equivalent to GET request to '/study/(ID)/prep_template'

    Parameters
    ----------
    study_id : int
        Study id to get prep template info for
    user_id : str
        User id requesting the prep templates

    Returns
    -------
    dict of list of dict
        prep template information seperated by data type, in the form
        {data_type: [{prep 1 info dict}, ....], ...}
    """
    # Can only pass ids over API, so need to instantiate object
    study = Study(study_id)
    if not study.has_access(User(user_id)):
        return {'status': 'error', 'message':
                'User does not have access to study'}
    prep_info = {}
    for dtype in study.data_types:
        prep_info[dtype] = []
        for prep in study.prep_templates(dtype):
            start_artifact = prep.artifact
            info = {
                'name': 'PREP %d NAME' % prep.id,
                'id': prep.id,
                'status': prep.status,
                'start_artifact': start_artifact.artifact_type,
                'start_artifact_id': start_artifact.id,
                'last_artifact': 'TODO new gui'
            }
            prep_info[dtype].append(info)
    return prep_info
