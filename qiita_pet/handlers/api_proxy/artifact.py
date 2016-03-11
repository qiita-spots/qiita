# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from os.path import join
from functools import partial

from future.utils import viewitems

from qiita_core.util import execute_as_transaction
from qiita_core.qiita_settings import qiita_config
from qiita_pet.handlers.api_proxy.util import check_access, check_fp
from qiita_db.artifact import Artifact
from qiita_db.user import User
from qiita_db.exceptions import QiitaDBArtifactDeletionError
from qiita_db.metadata_template.prep_template import PrepTemplate
from qiita_db.util import get_mountpoint, get_visibilities


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
                      prep_template_id):
    """Creates the initial artifact for the prep template

    Parameters
    ----------
    user_id : str
        User adding the atrifact
    filepaths : str
        Comma-separated list of files to attach to the artifact,
        keyed by file type
    artifact_type : str
        The type of the artifact
    name : str
        Name to give the artifact
    prep_template_id : int or str castable to int
        Prep template to attach the artifact to

    Returns
    -------
    dict of objects
        A dictionary containing the new artifact ID
        {'status': status,
         'message': message,
         'artifact': id}
    """
    prep = PrepTemplate(int(prep_template_id))
    study_id = prep.study_id

    # First check if the user has access to the study
    access_error = check_access(study_id, user_id)
    if access_error:
        return access_error

    uploads_path = get_mountpoint('uploads')[0][1]
    path_builder = partial(join, uploads_path, str(study_id))
    cleaned_filepaths = []
    for ftype, file_list in viewitems(filepaths):
        # JavaScript sends us this list as a comma-separated list
        for fp in file_list.split(','):
            # JavaScript will send this value as an empty string if the
            # list of files was empty. In such case, the split will generate
            # a single element containing the empty string. Check for that case
            # here and, if fp is not the empty string, proceed to check if
            # the file exists
            if fp:
                # Check if filepath being passed exists for study
                full_fp = path_builder(fp)
                exists = check_fp(study_id, full_fp)
                if exists['status'] != 'success':
                    return {'status': 'error',
                            'message': 'File does not exist: %s' % fp}
                cleaned_filepaths.append((full_fp, ftype))

    # This should never happen, but it doesn't hurt to actually have
    # a explicit check, in case there is something odd with the JS
    if not cleaned_filepaths:
        return {'status': 'error',
                'message': "Can't create artifact, no files provided."}

    try:
        artifact = Artifact.create(cleaned_filepaths, artifact_type, name=name,
                                   prep_template=prep)
    except Exception as e:
        # We should hit this exception rarelly (that's why is an exception)
        # since at this point we have done multiple checks. However, it can
        # occur in weird cases, so better let the GUI know that this fail
        return {'status': 'error',
                'message': "Error creating artifact: %s" % str(e)}

    return {'status': 'success',
            'message': '',
            'artifact': artifact.id}


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
    access_error = check_access(pd.study.id, user_id)
    if access_error:
        return access_error
    try:
        Artifact.delete(int(artifact_id))
    except QiitaDBArtifactDeletionError as e:
        return {'status': 'error',
                'message': str(e)}
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
