# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from collections import defaultdict
from json import dumps, loads

from qiita_core.exceptions import IncompetentQiitaDeveloperError
from qiita_core.util import execute_as_transaction
from qiita_core.qiita_settings import r_client
from qiita_db.user import User
from qiita_db.study import Study
from qiita_db.exceptions import QiitaDBColumnError, QiitaDBLookupError
from qiita_db.metadata_template.prep_template import PrepTemplate
from qiita_db.processing_job import ProcessingJob
from qiita_db.software import Software, Parameters
from qiita_db.util import (supported_filepath_types,
                           get_files_from_uploads_folders)
from qiita_pet.handlers.api_proxy.util import check_access


STUDY_KEY_FORMAT = 'study_%s'


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
            'data_types': Study.all_data_types()}


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
    study_info['publication_doi'] = []
    study_info['publication_pid'] = []
    for pub, is_doi in study.publications:
        if is_doi:
            study_info['publication_doi'].append(pub)
        else:
            study_info['publication_pid'].append(pub)
    study_info['study_id'] = study.id
    study_info['study_title'] = study.title
    study_info['shared_with'] = [s.id for s in study.shared_with]
    study_info['status'] = study.status
    study_info['ebi_study_accession'] = study.ebi_study_accession
    study_info['ebi_submission_status'] = study.ebi_submission_status
    study_info['public_raw_download'] = study.public_raw_download
    study_info['notes'] = study.notes
    study_info['autoloaded'] = study.autoloaded

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
    # Study.has_access no_public=True, will return True only if the user_id is
    # the owner of the study or if the study is shared with the user_id; this
    # with study.public_raw_download will define has_access_to_raw_data
    study_info['has_access_to_raw_data'] = study.has_access(
        User(user_id), True) or study.public_raw_download

    study_info['show_biom_download_button'] = 'BIOM' in [
        a.artifact_type for a in study.artifacts()]
    study_info['show_raw_download_button'] = any([
        True for pt in study.prep_templates() if pt.artifact is not None])

    # getting study processing status from redis
    processing = False
    study_info['level'] = ''
    study_info['message'] = ''
    job_info = r_client.get(STUDY_KEY_FORMAT % study_id)
    if job_info:
        job_info = defaultdict(lambda: '', loads(job_info))
        job_id = job_info['job_id']
        job = ProcessingJob(job_id)
        job_status = job.status
        processing = job_status not in ('success', 'error')
        if processing:
            study_info['level'] = 'info'
            study_info['message'] = 'This study is currently being processed'
        elif job_status == 'error':
            study_info['level'] = 'danger'
            study_info['message'] = job.log.msg.replace('\n', '</br>')
        else:
            study_info['level'] = job_info['alert_type']
            study_info['message'] = job_info['alert_msg'].replace(
                '\n', '</br>')

    return {'status': 'success',
            'message': '',
            'study_info': study_info,
            'editable': study.can_edit(User(user_id))}


@execute_as_transaction
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

    qiita_plugin = Software.from_name_and_version('Qiita', 'alpha')
    cmd = qiita_plugin.get_command('delete_study')
    params = Parameters.load(cmd, values_dict={'study': study_id})
    job = ProcessingJob.create(User(user_id), params, True)
    # Store the job id attaching it to the sample template id
    r_client.set(STUDY_KEY_FORMAT % study_id,
                 dumps({'job_id': job.id}))

    job.submit()

    return {'status': 'success', 'message': ''}


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
        dtype_infos = list()
        for prep in study.prep_templates(dtype):
            if prep.status != 'public' and not editable:
                continue
            start_artifact = prep.artifact
            info = {
                'name': prep.name,
                'id': prep.id,
                'status': prep.status,
                'total_samples': len(prep),
                'creation_timestamp': prep.creation_timestamp,
                'modification_timestamp': prep.modification_timestamp
            }
            if start_artifact is not None:
                youngest_artifact = prep.artifact.youngest_artifact
                info['start_artifact'] = start_artifact.artifact_type
                info['start_artifact_id'] = start_artifact.id
                info['num_artifact_children'] = len(start_artifact.children)
                info['youngest_artifact_name'] = youngest_artifact.name
                info['youngest_artifact_type'] = \
                    youngest_artifact.artifact_type
                info['youngest_artifact'] = '%s - %s' % (
                    youngest_artifact.name, youngest_artifact.artifact_type)
                info['ebi_experiment'] = len(
                    [v for _, v in prep.ebi_experiment_accessions.items()
                     if v is not None])
            else:
                info['start_artifact'] = None
                info['start_artifact_id'] = None
                info['youngest_artifact'] = None
                info['num_artifact_children'] = 0
                info['youngest_artifact_name'] = None
                info['youngest_artifact_type'] = None
                info['ebi_experiment'] = 0

            dtype_infos.append(info)

        # default sort is in ascending order of creation timestamp
        sorted_info = sorted(dtype_infos,
                             key=lambda k: k['creation_timestamp'],
                             reverse=False)
        prep_info[dtype] = sorted_info

    return {'status': 'success',
            'message': '',
            'info': prep_info}


def study_files_get_req(user_id, study_id, prep_template_id, artifact_type):
    """Returns the uploaded files for the study id categorized by artifact_type

    It retrieves the files uploaded for the given study and tries to
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
    message = []

    pt = PrepTemplate(prep_template_id)
    if pt.study_id != study_id:
        raise IncompetentQiitaDeveloperError(
            "The requested prep id (%d) doesn't belong to the study "
            "(%d)" % (pt.study_id, study_id))

    uploaded = get_files_from_uploads_folders(study_id)
    pt = pt.to_dataframe()
    ftypes_if = (ft.startswith('raw_') for ft, _ in supp_file_types
                 if ft != 'raw_sff')
    if any(ftypes_if) and 'run_prefix' in pt.columns:
        prep_prefixes = tuple(set(pt['run_prefix']))
        num_prefixes = len(prep_prefixes)
        # sorting prefixes by length to avoid collisions like: 100 1002
        # 10003
        prep_prefixes = sorted(prep_prefixes, key=len, reverse=True)
        # group files by prefix
        sfiles = defaultdict(list)
        for p in prep_prefixes:
            to_remove = []
            for fid, f, _ in uploaded:
                if f.startswith(p):
                    sfiles[p].append(f)
                    to_remove.append((fid, f))
            uploaded = [x for x in uploaded if x not in to_remove]
        inuse = [y for x in sfiles.values() for y in x]
        remaining.extend([f for _, f, _ in uploaded if f not in inuse])
        supp_file_types_len = len(supp_file_types)

        for k, v in sfiles.items():
            len_files = len(v)
            # if the number of files in the k group is larger than the
            # available columns add to the remaining group, if not put them in
            # the selected group
            if len_files > supp_file_types_len:
                remaining.extend(v)
                message.append("'%s' has %d matches." % (k, len_files))
            else:
                v.sort()
                selected.append(v)
    else:
        num_prefixes = 0
        remaining = [f for _, f, _ in uploaded]

    # get file_types, format: filetype, required, list of files
    file_types = [(t, req, [x[i] for x in selected if i+1 <= len(x)])
                  for i, (t, req) in enumerate(supp_file_types)]

    # Create a list of artifacts that the user has access to, in case that
    # he wants to import the files from another artifact
    user = User(user_id)
    artifact_options = []
    user_artifacts = user.user_artifacts(artifact_type=artifact_type)
    study = Study(study_id)
    if study not in user_artifacts:
        user_artifacts[study] = study.artifacts(artifact_type=artifact_type)
    for study, artifacts in user_artifacts.items():
        study_label = "%s (%d)" % (study.title, study.id)
        for a in artifacts:
            artifact_options.append(
                (a.id, "%s - %s (%d)" % (study_label, a.name, a.id)))

    message = ('' if not message
               else '\n'.join(['Check these run_prefix:'] + message))

    return {'status': 'success',
            'message': message,
            'remaining': sorted(remaining),
            'file_types': file_types,
            'num_prefixes': num_prefixes,
            'artifacts': artifact_options}


def study_tags_request():
    """Retrieve available study tags

    Returns
    -------
    dict of {str, str}
        A dictionary with the following keys:
        - status: str, whether if the request is successful or not
        - message: str, if the request is unsuccessful, a human readable error
        - tags: {level: value, ..., ...}
    """
    return {'status': 'success',
            'message': '',
            'tags': Study.get_tags()}


def study_get_tags_request(user_id, study_id):
    """Retrieve available study tags for study_id

    Parameters
    ----------
    user_id : int
        The id of the user performing the operation
    study_id : int
        The id of the study on which we will be performing the operation

    Returns
    -------
    dict of {str, str}
        A dictionary with the following keys:
        - status: str, whether if the request is successful or not
        - message: str, if the request is unsuccessful, a human readable error
        - tags: [value, ..., ...]
    """

    access_error = check_access(study_id, user_id)
    if access_error:
        return access_error
    study = Study(study_id)

    return {'status': 'success',
            'message': '',
            'tags': study.tags}


def study_patch_request(user_id, study_id,
                        req_op, req_path, req_value=None, req_from=None):
    """Modifies an attribute of the study object

    Parameters
    ----------
    user_id : int
        The id of the user performing the patch operation
    study_id : int
        The id of the study on which we will be performing the patch operation
    req_op : str
        The operation to perform on the study
    req_path : str
        The attribute to patch
    req_value : str, optional
        The value that needs to be modified
    req_from : str, optional
        The original path of the element

    Returns
    -------
    dict of {str, str}
        A dictionary with the following keys:
        - status: str, whether if the request is successful or not
        - message: str, if the request is unsuccessful, a human readable error
    """
    if req_op == 'replace':
        req_path = [v for v in req_path.split('/') if v]
        if len(req_path) != 1:
            return {'status': 'error',
                    'message': 'Incorrect path parameter'}

        attribute = req_path[0]

        # Check if the user actually has access to the study
        access_error = check_access(study_id, user_id)
        if access_error:
            return access_error
        study = Study(study_id)

        if attribute == 'tags':
            message = study.update_tags(User(user_id), req_value)
            return {'status': 'success',
                    'message': message}
        elif attribute == 'toggle_public_raw_download':
            try:
                study.public_raw_download = not study.public_raw_download
                return {'status': 'success',
                        'message': 'Successfully updated public_raw_download'}
            except (QiitaDBLookupError, QiitaDBColumnError) as e:
                return {'status': 'error',
                        'message': str(e)}
        else:
            # We don't understand the attribute so return an error
            return {'status': 'error',
                    'message': 'Attribute "%s" not found. '
                               'Please, check the path parameter' % attribute}
    else:
        return {'status': 'error',
                'message': 'Operation "%s" not supported. '
                           'Current supported operations: replace' % req_op}
