# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from __future__ import division
from collections import defaultdict

from future.utils import viewitems

from qiita_db.user import User
from qiita_db.study import Study
from qiita_db.metadata_template.prep_template import PrepTemplate
from qiita_db.util import (supported_filepath_types,
                           get_files_from_uploads_folders)
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
    study_info['ebi_study_accession'] = study.ebi_study_accession
    study_info['ebi_submission_status'] = study.ebi_submission_status

    # Clean up StudyPerson objects to string for display
    pi = study_info['principal_investigator']
    study_info['principal_investigator'] = {
        'name': pi.name,
        'email': pi.email,
        'affiliation': pi.affiliation}

    lab_person = study_info['lab_person']
    if lab_person:
        study_info['lab_person'] = {
            'name': lab_person.name,
            'email': lab_person.email,
            'affiliation': lab_person.affiliation}

    samples = study.sample_template
    study_info['num_samples'] = 0 if samples is None else len(list(samples))
    study_info['owner'] = study.owner.id

    return {'status': 'success',
            'message': '',
            'study_info': study_info,
            'editable': study.can_edit(User(user_id))}


def study_delete_req(study_id, user_id):
    """Delete a given study

    Parameters
    ----------
    study_id : int
        Study id to delete
    user_id : str
        User requesting the deletion

    Returns
    -------
    dict
        Status of deletion, in the format
        {status: status,
         message: message}
    """
    access_error = check_access(study_id, user_id)
    if access_error:
        return access_error

    status = 'success'
    try:
        Study.delete(int(study_id))
        msg = ''
    except Exception as e:
        status = 'error'
        msg = 'Unable to delete study: %s' % str(e)
    return {
        'status': status,
        'message': msg
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
    prep_info = defaultdict(list)
    editable = study.can_edit(User(user_id))
    for dtype in study.data_types:
        for prep in study.prep_templates(dtype):
            if prep.status != 'public' and not editable:
                continue
            start_artifact = prep.artifact
            info = {
                'name': 'PREP %d NAME' % prep.id,
                'id': prep.id,
                'status': prep.status,
            }
            if start_artifact is not None:
                youngest_artifact = prep.artifact.youngest_artifact
                info['start_artifact'] = start_artifact.artifact_type
                info['start_artifact_id'] = start_artifact.id
                info['youngest_artifact'] = '%s - %s' % (
                    youngest_artifact.name, youngest_artifact.artifact_type)
                info['ebi_experiment'] = bool(prep.ebi_experiment_accessions)
            else:
                info['start_artifact'] = None
                info['start_artifact_id'] = None
                info['youngest_artifact'] = None
                info['ebi_experiment'] = False

            prep_info[dtype].append(info)

    return {'status': 'success',
            'message': '',
            'info': prep_info}


def study_files_get_req(user_id, study_id, prep_template_id, artifact_type):
    """Returns the uploaded files for the study id categorized by artifact_type

    It retrieves the files uploaded for the given study and tries to do a
    guess on how those files should be added to the artifact of the given
    type. Uses information on the prep template to try to do a better guess.

    Parameters
    ----------
    user_id : str
        The id of the user making the request
    study_id : int
        The study id
    prep_template_id : int
        The prep template id
    artifact_type : str
        The artifact type

    Returns
    -------
    dict of {str: object}
        A dict of the form {'status': str,
                            'message': str,
                            'remaining': list of str,
                            'file_types': list of (str, bool, list of str),
                            'num_prefixes': int}
        where 'status' is a string specifying whether the query is successfull,
        'message' is a human-readable description of the error (optional),
        'remaining' is the list of files that could not be categorized,
        'file_types' is a list of the available filetypes, if it is required
        or not and the list of categorized files for the given artifact type
        and 'num_prefixes' is the number of different run prefix values in
        the given prep template.
    """
    supp_file_types = supported_filepath_types(artifact_type)
    selected = []
    remaining = []

    uploaded = get_files_from_uploads_folders(study_id)
    pt = PrepTemplate(prep_template_id).to_dataframe()

    ftypes_if = (ft.startswith('raw_') for ft, _ in supp_file_types
                 if ft != 'raw_sff')
    if any(ftypes_if) and 'run_prefix' in pt.columns:
        prep_prefixes = tuple(set(pt['run_prefix']))
        num_prefixes = len(prep_prefixes)
        for _, filename in uploaded:
            if filename.startswith(prep_prefixes):
                selected.append(filename)
            else:
                remaining.append(filename)
    else:
        num_prefixes = 0
        remaining = [f for _, f in uploaded]

    # At this point we can't do anything smart about selecting by default
    # the files for each type. The only thing that we can do is assume that
    # the first in the supp_file_types list is the default one where files
    # should be added in case of 'run_prefix' being present
    file_types = [(fp_type, req, []) for fp_type, req in supp_file_types[1:]]
    first = supp_file_types[0]
    # Note that this works even if `run_prefix` is not in the prep template
    # because selected is initialized to the empty list
    file_types.insert(0, (first[0], first[1], selected))

    # Create a list of artifacts that the user has access to, in case that
    # he wants to import the files from another artifact
    user = User(user_id)
    artifact_options = []
    user_artifacts = user.user_artifacts(artifact_type=artifact_type)
    study = Study(study_id)
    if study not in user_artifacts:
        user_artifacts[study] = study.artifacts(artifact_type=artifact_type)
    for study, artifacts in viewitems(user_artifacts):
        study_label = "%s (%d)" % (study.title, study.id)
        for a in artifacts:
            artifact_options.append(
                (a.id, "%s - %s (%d)" % (study_label, a.name, a.id)))

    return {'status': 'success',
            'message': '',
            'remaining': sorted(remaining),
            'file_types': file_types,
            'num_prefixes': num_prefixes,
            'artifacts': artifact_options}
