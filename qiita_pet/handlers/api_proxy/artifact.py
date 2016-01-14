from qiita_db.artifact import Artifact
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

    Raises
    ------
    HTTPError
        Raises code 400 if unknown direction passed

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
