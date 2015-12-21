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
from qiita_db.metadata_template.prep_template import PrepTemplate


def study_prep_proxy(study_id, user_id):
    """Equivalent to GET request to '/study/(ID)/prep_template'

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


def prep_graph_proxy(prep_id, user_id):
    """Equivalent to GET request to '/study/(ID)/prep_template/graph'

    Parameters
    ----------
    study_id : int
        Study the prep template belongs to
    prep_id : int
        Prep template ID to get graph for
    user_id : str
        User making the request

    Returns
    -------
    dict of lists of tuples
        A dictionary containing the edge list representation of the graph,
        and the node labels. Formatted as:
        {'edge_list': [(0, 1), (0, 2)...],
         'node_labels': [(0, 'label0'), (1, 'label1'), ...]}

    Raises
    ------
    HTTPError
        Raises code 400 if unknown direction passed

    Notes
    -----
    Nodes are identified by the corresponding Artifact ID.
    """
    prep = PrepTemplate(int(prep_id))
    access_error = check_access(prep.study_id, user_id)
    if access_error:
        return access_error
    G = prep.artifact.descendants
    node_labels = [(n.id, 'Artifact Name for %d - %s' % (n.id,
                                                         n.artifact_type))
                   for n in G.nodes()]
    return {'edge_list': [(n.id, m.id) for n, m in G.edges()],
            'node_labels': node_labels}
    return {'edge_list': G.edges(), 'node_labels': node_labels}
