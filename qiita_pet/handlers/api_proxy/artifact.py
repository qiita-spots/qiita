# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from qiita_db.artifact import Artifact
from qiita_db.user import User
from qiita_db.exceptions import (QiitaDBOperationNotPermittedError,
                                 QiitaDBArtifactDeletionError)
from qiita_core.qiita_settings import qiita_config
from qiita_pet.handlers.api_proxy.util import check_access


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

    try:
        can_be_submitted_to_ebi = pd.can_be_submitted_to_ebi
        ebi_run_accessions = pd.ebi_run_accessions
    except QiitaDBOperationNotPermittedError:
        can_be_submitted_to_ebi = False
        ebi_run_accessions = None

    try:
        can_be_submitted_to_vamps = pd.can_be_submitted_to_vamps
        is_submitted_to_vamps = pd.is_submitted_to_vamps
    except QiitaDBOperationNotPermittedError:
        can_be_submitted_to_vamps = False
        is_submitted_to_vamps = False

    return {
        'timestamp': pd.timestamp,
        'processing_parameters': pd.processing_parameters,
        'visibility': pd.visibility,
        'artifact_type': pd.artifact_type,
        'data_type': pd.data_type,
        'can_be_submitted_to_ebi': can_be_submitted_to_ebi,
        'can_be_submitted_to_vamps': can_be_submitted_to_vamps,
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
    if visibility not in {'sandbox', 'awaiting_approval', 'private', 'public'}:
        return {'status': 'error',
                'message': 'Unknown visiblity value: %s' % visibility}

    pd = Artifact(int(artifact_id))
    access_error = check_access(pd.study.id, user_id)
    if access_error:
        return access_error
    user = User(str(user_id))
    # Set the approval to private if needs approval and admin
    if all([qiita_config.require_approval, visibility == 'private',
            user.level == 'admin']):
        pd.visibility = 'private'
        status = 'success'
        msg = 'Artifact visibility changed to private'
    # Set the approval to private if approval not required
    elif all([not qiita_config.require_approval,
              visibility == 'private']):
        pd.visibility = 'private'
        status = 'success'
        msg = 'Artifact visibility changed to private'
    # Trying to set approval without admin privileges
    elif visibility == 'private':
        status = 'error'
        msg = 'User does not have permissions to approve change'
    else:
        pd.visibility = visibility
        status = 'success'
        msg = 'Artifact visibility changed to %s' % visibility

    return {'status': status,
            'message': msg}
