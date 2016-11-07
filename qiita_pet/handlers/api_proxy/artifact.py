# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from os.path import join, basename
from functools import partial
from json import dumps

from future.utils import viewitems
from moi import r_client

from qiita_core.util import execute_as_transaction
from qiita_core.qiita_settings import qiita_config
from qiita_pet.handlers.api_proxy.util import check_access, check_fp
from qiita_ware.context import safe_submit
from qiita_ware.dispatchable import (copy_raw_data, delete_artifact)
from qiita_db.artifact import Artifact
from qiita_db.user import User
from qiita_db.metadata_template.prep_template import PrepTemplate
from qiita_db.util import get_mountpoint, get_visibilities
from qiita_db.software import Command, Parameters
from qiita_db.processing_job import ProcessingJob


PREP_TEMPLATE_KEY_FORMAT = 'prep_template_%s'


def artifact_summary_get_request(user_id, artifact_id):
    """Returns the information for the artifact summary page

    Parameters
    ----------
    user_id : str
        The user making the request
    artifact_id : int or str
        The artifact id

    Returns
    -------
    dict of objects
        A dictionary containing the artifact summary information
        {'status': str,
         'message': str,
         'name': str,
         'summary': str,
         'job': list of [str, str, str]}
    """
    artifact_id = int(artifact_id)
    artifact = Artifact(artifact_id)

    access_error = check_access(artifact.study.id, user_id)
    if access_error:
        return access_error

    user = User(user_id)
    visibility = artifact.visibility
    summary = artifact.html_summary_fp
    job_info = None
    errored_jobs = []
    processing_jobs = []
    for j in artifact.jobs():
        if j.command.software.type == "artifact transformation":
            status = j.status
            if status == 'success':
                continue
            j_msg = j.log.msg if status == 'error' else None
            processing_jobs.append(
                [j.id, j.command.name, j.status, j.step, j_msg])

    # Check if the HTML summary exists
    if summary:
        with open(summary[1]) as f:
            summary = f.read()
    else:
        # Check if the summary is being generated
        command = Command.get_html_generator(artifact.artifact_type)
        all_jobs = set(artifact.jobs(cmd=command))
        jobs = [j for j in all_jobs if j.status in ['queued', 'running']]
        errored_jobs = [(j.id, j.log.msg)
                        for j in all_jobs if j.status in ['error']]
        if jobs:
            # There is already a job generating the HTML. Also, there should be
            # at most one job, because we are not allowing here to start more
            # than one
            job = jobs[0]
            job_info = [job.id, job.status, job.step]

    buttons = []
    btn_base = (
        '<button onclick="if (confirm(\'Are you sure you want to %s '
        'artifact id: {0}?\')) {{ set_artifact_visibility(\'%s\', {0}) }}" '
        'class="btn btn-primary btn-sm">%s</button>').format(artifact_id)

    if qiita_config.require_approval:
        if visibility == 'sandbox':
            # The request approval button only appears if the artifact is
            # sandboxed and the qiita_config specifies that the approval should
            # be requested
            buttons.append(
                btn_base % ('request approval for', 'awaiting_approval',
                            'Request approval'))

        elif user.level == 'admin' and visibility == 'awaiting_approval':
            # The approve artifact button only appears if the user is an admin
            # the artifact is waiting to be approvaed and the qiita config
            # requires artifact approval
            buttons.append(btn_base % ('approve', 'private',
                                       'Approve artifact'))

    if visibility == 'private':
        # The make public button only appears if the artifact is private
        buttons.append(btn_base % ('make public', 'public', 'Make public'))

    # The revert to sandbox button only appears if the artifact is not
    # sandboxed nor public
    if visibility not in {'sandbox', 'public'}:
        buttons.append(btn_base % ('revert to sandbox', 'sandbox',
                                   'Revert to sandbox'))

    if user.level == 'admin':
        if artifact.can_be_submitted_to_ebi:
            if not artifact.is_submitted_to_ebi:
                buttons.append(
                    '<a class="btn btn-primary btn-sm" '
                    'href="/ebi_submission/%d">'
                    '<span class="glyphicon glyphicon-export"></span>'
                    ' Submit to EBI</a>' % artifact_id)
        if artifact.can_be_submitted_to_vamps:
            if not artifact.is_submitted_to_vamps:
                buttons.append(
                    '<a class="btn btn-primary btn-sm" href="/vamps/%d">'
                    '<span class="glyphicon glyphicon-export"></span>'
                    ' Submit to VAMPS</a>' % artifact_id)

    files = [(f_id, "%s (%s)" % (basename(fp), f_type.replace('_', ' ')))
             for f_id, fp, f_type in artifact.filepaths
             if f_type != 'directory']

    # TODO: https://github.com/biocore/qiita/issues/1724 Remove this hardcoded
    # values to actually get the information from the database once it stores
    # the information
    if artifact.artifact_type in ['SFF', 'FASTQ', 'FASTA', 'FASTA_Sanger',
                                  'per_sample_FASTQ']:
        # If the artifact is one of the "raw" types, only the owner of the
        # study and users that has been shared with can see the files
        if not artifact.study.has_access(user, no_public=True):
            files = []

    processing_parameters = (artifact.processing_parameters.values
                             if artifact.processing_parameters is not None
                             else {})

    return {'status': 'success',
            'message': '',
            'name': artifact.name,
            'summary': summary,
            'job': job_info,
            'errored_jobs': errored_jobs,
            'processing_jobs': processing_jobs,
            'visibility': visibility,
            'buttons': ' '.join(buttons),
            'files': files,
            'editable': artifact.study.can_edit(user),
            'study_id': artifact.study.id,
            'prep_id': artifact.prep_templates[0].id,
            'processing_parameters': processing_parameters}


def artifact_summary_post_request(user_id, artifact_id):
    """Launches the HTML summary generation and returns the job information

    Parameters
    ----------
    user_id : str
        The user making the request
    artifact_id : int or str
        The artifact id

    Returns
    -------
    dict of objects
        A dictionary containing the artifact summary information
        {'status': str,
         'message': str,
         'job': list of [str, str, str]}
    """
    artifact_id = int(artifact_id)
    artifact = Artifact(artifact_id)

    access_error = check_access(artifact.study.id, user_id)
    if access_error:
        return access_error

    # Check if the summary is being generated or has been already generated
    command = Command.get_html_generator(artifact.artifact_type)
    jobs = artifact.jobs(cmd=command)
    jobs = [j for j in jobs if j.status in ['queued', 'running', 'success']]
    if jobs:
        # The HTML summary is either being generated or already generated.
        # Return the information of that job so we only generate the HTML
        # once
        job = jobs[0]
    else:
        # Create a new job to generate the HTML summary and return the newly
        # created job information
        job = ProcessingJob.create(
            User(user_id),
            Parameters.load(command, values_dict={'input_data': artifact_id}))
        job.submit()

    return {'status': 'success',
            'message': '',
            'job': [job.id, job.status, job.step]}


def artifact_get_req(user_id, artifact_id):
    """Returns all base information about an artifact

    Parameters
    ----------
    user_id : str
        user making the request
    artifact_id : int or str coercable to int
        Atrtifact to get information for

    Returns
    -------
    dict of objects
        A dictionary containing the artifact information
        {'status': status,
         'message': message,
         'artifact': {info key: val, ...}}
    """
    artifact_id = int(artifact_id)
    artifact = Artifact(artifact_id)

    access_error = check_access(artifact.study.id, user_id)
    if access_error:
        return access_error

    can_submit_ebi = artifact.can_be_submitted_to_ebi
    ebi_run_accessions = (artifact.ebi_run_accessions
                          if can_submit_ebi else None)
    can_submit_vamps = artifact.can_be_submitted_to_vamps
    is_submitted_vamps = (artifact.is_submitted_to_vamps
                          if can_submit_vamps else False)

    return {'id': artifact_id,
            'timestamp': artifact.timestamp,
            'processing_parameters': artifact.processing_parameters,
            'visibility': artifact.visibility,
            'type': artifact.artifact_type,
            'data_type': artifact.data_type,
            'filepaths': artifact.filepaths,
            'parents': [a.id for a in artifact.parents],
            'study': artifact.study.id if artifact.study else None,
            'can_submit_ebi': can_submit_ebi,
            'ebi_run_accessions': ebi_run_accessions,
            'can_submit_vamps': can_submit_vamps,
            'is_submitted_vamps': is_submitted_vamps}


@execute_as_transaction
def artifact_post_req(user_id, filepaths, artifact_type, name,
                      prep_template_id, artifact_id=None):
    """Creates the initial artifact for the prep template

    Parameters
    ----------
    user_id : str
        User adding the atrifact
    filepaths : dict of str
        Comma-separated list of files to attach to the artifact,
        keyed by file type
    artifact_type : str
        The type of the artifact
    name : str
        Name to give the artifact
    prep_template_id : int or str castable to int
        Prep template to attach the artifact to
    artifact_id : int or str castable to int, optional
        The id of the imported artifact

    Returns
    -------
    dict of objects
        A dictionary containing the new artifact ID
        {'status': status,
         'message': message,
         'artifact': id}
    """
    prep_template_id = int(prep_template_id)
    prep = PrepTemplate(prep_template_id)
    study_id = prep.study_id

    # First check if the user has access to the study
    access_error = check_access(study_id, user_id)
    if access_error:
        return access_error

    if artifact_id:
        # if the artifact id has been provided, import the artifact
        job_id = safe_submit(user_id, copy_raw_data, prep, artifact_id)
        is_qiita_job = False
    else:
        uploads_path = get_mountpoint('uploads')[0][1]
        path_builder = partial(join, uploads_path, str(study_id))
        cleaned_filepaths = {}
        for ftype, file_list in viewitems(filepaths):
            # JavaScript sends us this list as a comma-separated list
            for fp in file_list.split(','):
                # JavaScript will send this value as an empty string if the
                # list of files was empty. In such case, the split will
                # generate a single element containing the empty string. Check
                # for that case here and, if fp is not the empty string,
                # proceed to check if the file exists
                if fp:
                    # Check if filepath being passed exists for study
                    full_fp = path_builder(fp)
                    exists = check_fp(study_id, full_fp)
                    if exists['status'] != 'success':
                        return {'status': 'error',
                                'message': 'File does not exist: %s' % fp}
                    if ftype not in cleaned_filepaths:
                        cleaned_filepaths[ftype] = []
                    cleaned_filepaths[ftype].append(full_fp)

        # This should never happen, but it doesn't hurt to actually have
        # a explicit check, in case there is something odd with the JS
        if not cleaned_filepaths:
            return {'status': 'error',
                    'message': "Can't create artifact, no files provided."}

        command = Command.get_validator(artifact_type)
        job = ProcessingJob.create(
            User(user_id),
            Parameters.load(command, values_dict={
                'template': prep_template_id,
                'files': dumps(cleaned_filepaths),
                'artifact_type': artifact_type
                }))
        job.submit()
        job_id = job.id
        is_qiita_job = True

    r_client.set(PREP_TEMPLATE_KEY_FORMAT % prep.id,
                 dumps({'job_id': job_id, 'is_qiita_job': is_qiita_job}))

    return {'status': 'success', 'message': ''}


def artifact_patch_request(user_id, req_op, req_path, req_value=None,
                           req_from=None):
    """Modifies an attribute of the artifact

    Parameters
    ----------
    user_id : str
        The id of the user performing the patch operation
    req_op : str
        The operation to perform on the artifact
    req_path : str
        The prep information and attribute to patch
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
        if len(req_path) != 2:
            return {'status': 'error',
                    'message': 'Incorrect path parameter'}

        artifact_id = req_path[0]
        attribute = req_path[1]

        # Check if the user actually has access to the artifact
        artifact = Artifact(artifact_id)
        access_error = check_access(artifact.study.id, user_id)
        if access_error:
            return access_error

        if not req_value:
            return {'status': 'error',
                    'message': 'A value is required'}

        if attribute == 'name':
            artifact.name = req_value
            return {'status': 'success',
                    'message': ''}
        else:
            # We don't understand the attribute so return an error
            return {'status': 'error',
                    'message': 'Attribute "%s" not found. '
                               'Please, check the path parameter' % attribute}
    else:
        return {'status': 'error',
                'message': 'Operation "%s" not supported. '
                           'Current supported operations: replace' % req_op}


def artifact_types_get_req():
    """Gets artifact types and descriptions available

    Returns
    -------
    dict of objects
        {'status': status,
         'message': message,
         'types': [[str, str], ...]}
        types holds type and description of the artifact type, in the form
        [[artifact_type, description], ...]
    """
    return {'status': 'success',
            'message': '',
            'types': Artifact.types()}


def artifact_graph_get_req(artifact_id, direction, user_id):
    """Creates graphs of ancestor or descendant artifacts from given one

    Parameters
    ----------
    artifact_id : int
        Artifact ID to get graph for
    direction : {'ancestors', 'descendants'}
        What direction to get the graph in

    Returns
    -------
    dict of lists of tuples
        A dictionary containing the edge list representation of the graph,
        and the node labels. Formatted as:
        {'status': status,
         'message': message,
         'edge_list': [(0, 1), (0, 2)...],
         'node_labels': [(0, 'label0'), (1, 'label1'), ...]}

    Notes
    -----
    Nodes are identified by the corresponding Artifact ID.
    """
    access_error = check_access(Artifact(artifact_id).study.id, user_id)
    if access_error:
        return access_error

    if direction == 'descendants':
        G = Artifact(int(artifact_id)).descendants
    elif direction == 'ancestors':
        G = Artifact(int(artifact_id)).ancestors
    else:
        return {
            'status': 'error',
            'message': 'Unknown directon %s' % direction
        }

    node_labels = [(n.id, ' - '.join([n.name, n.artifact_type]))
                   for n in G.nodes()]
    return {'edge_list': [(n.id, m.id) for n, m in G.edges()],
            'node_labels': node_labels,
            'status': 'success',
            'message': ''}


def artifact_delete_req(artifact_id, user_id):
    """Deletes the artifact

    Parameters
    ----------
    artifact_id : int
        Artifact being acted on
    user_id : str
        The user requesting the action

    Returns
    -------
    dict
        Status of action, in the form {'status': status, 'message': msg}
        status: status of the action, either success or error
        message: Human readable message for status
    """
    pd = Artifact(int(artifact_id))
    pt_id = pd.prep_templates[0].id
    access_error = check_access(pd.study.id, user_id)
    if access_error:
        return access_error

    job_id = safe_submit(user_id, delete_artifact, artifact_id)
    r_client.set(PREP_TEMPLATE_KEY_FORMAT % pt_id,
                 dumps({'job_id': job_id, 'is_qiita_job': False}))

    return {'status': 'success',
            'message': ''}


def artifact_status_put_req(artifact_id, user_id, visibility):
    """Set the status of the artifact given

    Parameters
    ----------
    artifact_id : int
        Artifact being acted on
    user_id : str
        The user requesting the action
    visibility : {'sandbox', 'awaiting_approval', 'private', 'public'}
        What to change the visibility to

    Returns
    -------
    dict
        Status of action, in the form {'status': status, 'message': msg}
        status: status of the action, either success or error
        message: Human readable message for status
    """
    if visibility not in get_visibilities():
        return {'status': 'error',
                'message': 'Unknown visiblity value: %s' % visibility}

    pd = Artifact(int(artifact_id))
    access_error = check_access(pd.study.id, user_id)
    if access_error:
        return access_error
    user = User(str(user_id))
    status = 'success'
    msg = 'Artifact visibility changed to %s' % visibility
    # Set the approval to private if needs approval and admin
    if visibility == 'private':
        if not qiita_config.require_approval:
            pd.visibility = 'private'
        # Set the approval to private if approval not required
        elif user.level == 'admin':
            pd.visibility = 'private'
        # Trying to set approval without admin privileges
        else:
            status = 'error'
            msg = 'User does not have permissions to approve change'
    else:
        pd.visibility = visibility

    return {'status': status,
            'message': msg}
