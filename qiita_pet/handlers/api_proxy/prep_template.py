# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from __future__ import division
import warnings

from os import remove
from os.path import exists, join
from natsort import natsorted

# This is the only folder in qiita_pet that should import outside qiita_pet
# The idea is that this proxies the call and response dicts we expect from the
# Qiita API once we build it. This will be removed and replaced with API calls
# when the API is complete.
from qiita_core.util import execute_as_transaction
from qiita_pet.handlers.api_proxy.util import check_access
from qiita_db.metadata_template.util import load_template_to_dataframe
from qiita_db.util import convert_to_id, get_mountpoint
from qiita_db.study import Study
from qiita_db.ontology import Ontology
from qiita_db.metadata_template.prep_template import PrepTemplate


@execute_as_transaction
def _process_investigation_type(inv_type, user_def_type, new_type):
    """Return the investigation_type and add it to the ontology if needed

    Parameters
    ----------
    inv_type : str
        The investigation type
    user_def_type : str
        The user-defined investigation type
    new_type : str
        The new user-defined investigation_type

    Returns
    -------
    str
        The investigation type chosen by the user
    """
    if inv_type == 'None Selected':
        inv_type = None
    elif inv_type == 'Other' and user_def_type == 'New Type':
        # This is a nre user defined investigation type so store it
        inv_type = new_type
        ontology = Ontology(convert_to_id('ENA', 'ontology'))
        ontology.add_user_defined_term(inv_type)
    elif inv_type == 'Other' and user_def_type != 'New Type':
        inv_type = user_def_type
    return inv_type


def prep_template_get_req(prep_id, user_id):
    """Gets the json of the full prep template

    Parameters
    ----------
    prep_id : int
        PrepTemplate id to get info for
    user_id : str
        User requesting the sample template info

    Returns
    -------
    dict of dictionaries
        Dictionary object where the keys are the metadata samples
        and the values are a dictionary of column and value.
        Format {sample: {column: value, ...}, ...}
    """
    prep = PrepTemplate(int(prep_id))
    access_error = check_access(prep.study_id, user_id)
    if access_error:
        return access_error
    df = prep.to_dataframe()
    return df.to_dict(orient='index')


def prep_template_summary_get_req(prep_id, user_id):
    """Get the summarized prep template data for each metadata column

    Parameters
    ----------
    prep_id : int
        PrepTemplate id to get info for
    user_id : str
        User requesting the sample template info

    Returns
    -------
    dict of list of tuples
        Dictionary object where the keys are the metadata categories
        and the values are list of tuples. Each tuple is an observed value in
        the category and the number of times its seen.
        Format {num_samples: value,
                category: [(val1, count1), (val2, count2), ...], ...}
    """
    prep = PrepTemplate(int(prep_id))
    access_error = check_access(prep.study_id, user_id)
    if access_error:
        return access_error
    df = prep.to_dataframe()
    out = {'num_samples': df.shape[0],
           'summary': {}}

    # drop the prep_id column if it exists
    if 'study_id' in df.columns:
        df.drop('study_id', axis=1, inplace=True)
    cols = list(df.columns)
    for column in cols:
        counts = df[column].value_counts()
        out['summary'][str(column)] = [(str(key), counts[key])
                                       for key in natsorted(counts.index)]

    return out


@execute_as_transaction
def prep_template_post_req(study_id, user_id, prep_template, data_type,
                           investigation_type=None,
                           user_defined_investigation_type=None,
                           new_investigation_type=None):
    """Adds a prep template to the system

    Parameters
    ----------
    study_id : int
        Study to attach the pre ptemplate to
    user_id : str
        User adding the prep template
    prep_template : str
        Filepath to the prep template being added
    data_type : str
        Data type of the processed samples
    investigation_type: str, optional
        Existing investigation type to attach to the prep template
    user_defined_investigation_type: str, optional
        Existing user added investigation type to attach to the prep template
    new_investigation_type: str, optional
        Investigation type to add to the system
    """
    access_error = check_access(study_id, user_id)
    if access_error:
        return access_error
    msg = "Your prep template was added"
    status = "success"

    investigation_type = _process_investigation_type(
        investigation_type, user_defined_investigation_type,
        new_investigation_type)

    # Get the upload base directory
    _, base_path = get_mountpoint("uploads")[0]
    # Get the path to the prep template
    fp_rpt = join(base_path, str(study_id), prep_template)
    if not exists(fp_rpt):
        # The file does not exist, fail nicely
        return {'status': 'error',
                'error': 'filepath does not exist',
                'filepath': prep_template}

    msg = ''
    status = 'success'
    try:
        with warnings.catch_warnings(record=True) as warns:
            # force all warnings to always be triggered
            warnings.simplefilter("always")
            data_type_id = convert_to_id(data_type, 'data_type')
            # deleting previous uploads and inserting new one
            PrepTemplate.create(load_template_to_dataframe(fp_rpt),
                                Study(int(study_id)), int(data_type_id),
                                investigation_type=investigation_type)
            remove(fp_rpt)

            # join all the warning messages into one. Note that this info
            # will be ignored if an exception is raised
            if warns:
                msg = '; '.join([str(w.message) for w in warns])
                status = 'warning'
    except Exception as e:
        # Some error occurred while processing the prep template
        # Show the error to the user so he can fix the template
        status = 'error'
        msg = str(e)
    return {'status': status,
            'message': msg,
            'file': prep_template}


@execute_as_transaction
def prep_template_put_req(prep_id, user_id, prep_template):
    """Updates the prep template with the changes in the given file

    Parameters
    ----------
    prep_id : int
        The prep template to update
    user_id : str
        The current user object id
    prep_template : str
        filepath to use for updating
    """
    # Get the uploads folder
    prep = PrepTemplate(int(prep_id))
    access_error = check_access(prep.study_id, user_id)
    if access_error:
        return access_error
    _, base_fp = get_mountpoint("uploads")[0]
    # Get the path of the prep template in the uploads folder
    fp = join(base_fp, str(prep.study_id), prep_template)

    if not exists(fp):
        # The file does not exist, fail nicely
        return {'status': 'error',
                'message': 'file does not exist',
                'file': prep_template}

    msg = ''
    status = 'success'
    try:
        with warnings.catch_warnings(record=True) as warns:
            pt = PrepTemplate(int(prep_id))
            df = load_template_to_dataframe(fp)
            pt.extend(df)
            pt.update(df)
            remove(fp)

            # join all the warning messages into one. Note that this info
            # will be ignored if an exception is raised
            if warns:
                msg = '\n'.join(set(str(w.message) for w in warns))
                status = 'warning'

    except Exception as e:
        # Some error occurred while processing the sample template
        # Show the error to the user so they can fix the template
        status = 'error'
        msg = str(e)
    return {'status': status,
            'message': msg,
            'file': prep_template}


def prep_template_delete_req(prep_id, user_id):
    """Delete the prep template

    Parameters
    ----------
    prep_id : int
        The prep template to update
    user_id : str
        The current user object id
    """
    prep = PrepTemplate(int(prep_id))
    access_error = check_access(prep.study_id, user_id)
    if access_error:
        return access_error

    msg = ''
    status = 'success'
    try:
        PrepTemplate.delete(prep.id)
    except Exception as e:
        msg = ("Couldn't remove prep template: %s" % str(e))
        status = 'error'

    return {'status': status,
            'message': msg}


@execute_as_transaction
def prep_template_filepaths_get_req(prep_id, user_id):
    """Returns all filepaths attached to a prep template

    Parameters
    ----------
    prep_id : int
        The current prep template id
    user_id : int
        The current user object id
    """
    prep = PrepTemplate(int(prep_id))
    access_error = check_access(prep.study_id, user_id)
    if access_error:
        return access_error
    return prep.get_filepaths()


def prep_template_graph_get_req(prep_id, user_id):
    """Returns graph of all artifacts created from the prep base artifact

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
