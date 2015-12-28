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
from qiita_pet.handlers.api_proxy.util import check_access
from qiita_db.study import Study


def prep_template_get_req(study_id, user_id):
    """Gives a summary of each prep template attached to the study

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
    access_error = check_access(study_id, user_id)
    if access_error:
        return access_error
    # Can only pass ids over API, so need to instantiate object
    study = Study(int(study_id))
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
