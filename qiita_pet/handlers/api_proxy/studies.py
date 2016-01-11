# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from __future__ import division

from qiita_db.study import Study
from qiita_pet.handlers.api_proxy.util import check_access


def data_types_get_req():
    """Returns data types available in the system

    Returns
    -------
    dict
        Data types information in the form
        {'status': status,
         'message': message,
         'data_types': list of str}
        status can be success, warning, or error depending on result
        message has the warnings or errors
        data_types is the list of available data types in the system
    """
    return {'status': 'success',
            'message': '',
            'data_types': Study.all_data_types()
            }


def study_get_req(study_id, user_id):
    """Returns information available for the given study

    Parameters
    ----------
    study_id : int
        Study id to get prep template info for
    user_id : str
        User requesting the info

    Returns
    -------
    dict
        Data types information in the form
        {'status': status,
         'message': message,
         'info': dict of objects
        status can be success, warning, or error depending on result
        message has the warnings or errors
        info contains study information seperated by data type, in the form
        {col_name: value, ...} with value being a string, int, or list of
        strings or ints
    """
    access_error = check_access(study_id, user_id)
    if access_error:
        return access_error
    # Can only pass ids over API, so need to instantiate object
    study = Study(study_id)
    study_info = study.info
    # Add needed info that is not part of the initial info pull
    study_info['publications'] = study.publications
    study_info['study_id'] = study.id
    study_info['study_title'] = study.title
    study_info['shared_with'] = [s.id for s in study.shared_with]
    study_info['status'] = study.status

    # Clean up StudyPerson objects to string for display
    pi = study_info['principal_investigator']
    study_info['principal_investigator'] = {
        'name': pi.name,
        'email': pi.email,
        'affiliation': pi.affiliation}

    lab_person = study_info['lab_person']
    study_info['lab_person'] = {
        'name': lab_person.name,
        'email': lab_person.email,
        'affiliation': lab_person.affiliation}

    samples = study.sample_template.keys()
    study_info['num_samples'] = 0 if samples is None else len(list(samples))
    return {'status': 'success',
            'message': '',
            'info': study_info
            }


def study_prep_get_req(study_id, user_id):
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
    return {'status': 'success',
            'message': '',
            'info': prep_info
            }
