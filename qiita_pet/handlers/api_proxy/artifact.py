# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from os.path import join

from qiita_core.util import execute_as_transaction
from qiita_core.qiita_settings import qiita_config
from qiita_pet.handlers.api_proxy.util import check_access, check_fp
from qiita_db.artifact import Artifact
from qiita_db.user import User
from qiita_db.exceptions import QiitaDBArtifactDeletionError
from qiita_db.metadata_template.prep_template import PrepTemplate
from qiita_db.util import get_mountpoint, get_visibilities


@execute_as_transaction
def artifact_post_req(user_id, filepaths, artifact_type, name,
                      prep_template_id):
    """Creates the initial artifact for the prep template

    Parameters
    ----------
    user_id : str
        User adding the atrifact
    filepaths : dict of {str: [str, ...], ...}
        List of files to attach to the artifact, keyed to the file type
    }
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
    access_error = check_access(prep.study_id, user_id)
    if access_error:
        return access_error
    study_id = PrepTemplate.study_id
    uploads_path = get_mountpoint('uploads')[0][1]
    cleaned_filepaths = []
    for ftype in filepaths:
        # Check if filepath being passed exists for study
        for fp in filepaths[ftype]:
            full_fp = join(uploads_path, fp)
            exists = check_fp(study_id, full_fp)
            if exists['status'] != 'success':
                return {'status': 'error',
                        'message': 'File does not exist: %s' % fp}
            cleaned_filepaths.append((full_fp, ftype))

    artifact = Artifact.create(cleaned_filepaths, artifact_type, name=name,
                               prep_template=prep)
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


def artifact_get_req(artifact_id, user_id):
    """Get information about the artifact

    Parameters
    ----------
    artifact_id : int
        Artifact being acted on
    user_id : str
        The user requesting the action

    Returns
    -------
    dict
        information about the artifact
    """
    pd = Artifact(int(artifact_id))
    access_error = check_access(pd.study.id, user_id)
    if access_error:
        return access_error

    can_submit_to_ebi = pd.can_be_submitted_to_ebi
    ebi_run_accessions = pd.ebi_run_accessions if can_submit_to_ebi else None

    can_submit_to_vamps = pd.can_be_submitted_to_vamps
    is_submitted_to_vamps = pd.is_submitted_to_vamps if can_submit_to_vamps \
        else False

    return {
        'timestamp': pd.timestamp,
        'processing_parameters': pd.processing_parameters,
        'visibility': pd.visibility,
        'artifact_type': pd.artifact_type,
        'data_type': pd.data_type,
        'can_be_submitted_to_ebi': can_submit_to_ebi,
        'can_be_submitted_to_vamps': can_submit_to_vamps,
        'is_submitted_to_vamps': is_submitted_to_vamps,
        'filepaths': pd.filepaths,
        'parents': [a.id for a in pd.parents],
        'prep_templates': [p.id for p in pd.prep_templates],
        'ebi_run_accessions': ebi_run_accessions,
        'study': pd.study.id}


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
