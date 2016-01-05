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
    list of str
        Data types available on the system
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
    dict of {str: object}
        Study information seperated by data type, in the form
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
    pi = study_info["principal_investigator"]
    study_info["principal_investigator"] = '%s (%s)' % (pi.name,
                                                        pi.affiliation)
    lab_person = study_info["lab_person"]
    study_info["lab_person"] = '%s (%s)' % (lab_person.name,
                                            lab_person.affiliation)

    samples = study.sample_template.keys()
    study_info['num_samples'] = 0 if samples is None else len(list(samples))
    return {'status': 'success',
            'message': '',
            'info': study_info
            }
