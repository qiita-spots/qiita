# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from __future__ import division
import warnings
from json import loads

from os import remove
from os.path import basename
from natsort import natsorted

from qiita_core.util import execute_as_transaction
from qiita_pet.handlers.api_proxy.util import check_access, check_fp
from qiita_db.metadata_template.util import load_template_to_dataframe
from qiita_db.util import convert_to_id, get_files_from_uploads_folders
from qiita_db.study import Study
from qiita_db.ontology import Ontology
from qiita_db.metadata_template.prep_template import PrepTemplate


def _get_ENA_ontology():
    ontology = Ontology(convert_to_id('ENA', 'ontology'))
    ena_terms = sorted(ontology.terms)
    # make "Other" last on the list
    ena_terms.remove('Other')
    ena_terms.append('Other')

    return {'ENA': ena_terms, 'User': sorted(ontology.user_defined_terms)}


def new_prep_template_get_req(study_id):
    """
    Parameters
    ----------
    study_id : int
        The study id

    Returns
    -------
    (list of str, list of str, dict of {str: list of str})
        The list of txt,csv files in the upload dir for the given study
        The list of available data types
        The investigation type ontology information
    """
    prep_files = [f for _, f in get_files_from_uploads_folders(study_id)
                  if f.endswith(('txt', 'tsv'))]
    data_types = sorted(Study.all_data_types())

    # Get all the ENA terms for the investigation type
    ontology_info = _get_ENA_ontology()

    return {'status': 'success',
            'prep_files': prep_files,
            'data_types': data_types,
            'ontology': ontology_info}


def prep_template_ajax_get_req(prep_id):
    """
    Parameters
    ----------
    prep_id : int
        The prep template id

    Returns
    -------
    """
    # Currently there is no name attribute, but it will be soon
    name = "Prep information %d" % prep_id
    pt = PrepTemplate(prep_id)
    artifact_attached = pt.artifact is not None
    study_id = pt.study_id
    files = [f for _, f in get_files_from_uploads_folders(study_id)
             if f.endswith(('txt', 'tsv'))]

    # The call to list is needed because keys is an iterator
    num_samples = len(list(pt.keys()))
    num_columns = len(pt.categories())
    investigation_type = ena_ontology_get_req()

    # Retrieve the information to download the prep template and QIIME
    # mapping file. See issue https://github.com/biocore/qiita/issues/1675
    download_prep = []
    download_qiime = []
    for fp_id, fp in pt.get_filepaths():
        if 'qiime' in basename(fp):
            download_qiime.append(fp_id)
        else:
            download_prep.append(fp_id)
    download_prep = download_prep[0]
    download_qiime = download_qiime[0]

    ontology = _get_ENA_ontology()

    # stats = prep_template_summary_get_req(prep_id, self.current_user.id)

    return {'status': 'success',
            'message': '',
            'name': name,
            'files': files,
            'download_prep': download_prep,
            'download_qiime': download_qiime,
            'num_samples': num_samples,
            'num_columns': num_columns,
            'investigation_type': investigation_type,
            'ontology': ontology,
            'artifact_attached': artifact_attached,
            'study_id': study_id}


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
    if inv_type == '':
        inv_type = None
    elif inv_type == 'Other' and user_def_type == 'New Type':
        # This is a new user defined investigation type so store it
        inv_type = new_type
        ontology = Ontology(convert_to_id('ENA', 'ontology'))
        ontology.add_user_defined_term(inv_type)
    elif inv_type == 'Other' and user_def_type != 'New Type':
        inv_type = user_def_type
    return inv_type


def _check_prep_template_exists(prep_id):
    """Make sure a prep template exists in the system

    Parameters
    ----------
    prep_id : int or str castable to int
        PrepTemplate id to check

    Returns
    -------
    dict
        {'status': status,
         'message': msg}
    """
    if not PrepTemplate.exists(int(prep_id)):
        return {'status': 'error',
                'message': 'Prep template %d does not exist' % int(prep_id)
                }
    return {'status': 'success',
            'message': ''}


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
    dict of objects
    {'status': status,
     'message': message,
     'template': {sample: {column: value, ...}, ...}
    """
    exists = _check_prep_template_exists(int(prep_id))
    if exists['status'] != 'success':
        return exists

    prep = PrepTemplate(int(prep_id))
    access_error = check_access(prep.study_id, user_id)
    if access_error:
        return access_error
    df = prep.to_dataframe()
    return {'status': 'success',
            'message': '',
            'template': df.to_dict(orient='index')}


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
    dict of objects
        Dictionary object where the keys are the metadata categories
        and the values are list of tuples. Each tuple is an observed value in
        the category and the number of times its seen.
        Format {'status': status,
                'message': message,
                'num_samples': value,
                'category': [(val1, count1), (val2, count2), ...], ...}
    """
    exists = _check_prep_template_exists(int(prep_id))
    if exists['status'] != 'success':
        return exists

    prep = PrepTemplate(int(prep_id))
    access_error = check_access(prep.study_id, user_id)
    if access_error:
        return access_error
    df = prep.to_dataframe()
    out = {'num_samples': df.shape[0],
           'summary': {},
           'status': 'success',
           'message': ''}

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
        Study to attach the prep template to
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

    Returns
    -------
    dict of str
        {'status': status,
         'message': message,
         'file': prep_template,
         'id': id}
    """
    access_error = check_access(study_id, user_id)
    if access_error:
        return access_error
    fp_rpt = check_fp(study_id, prep_template)
    if fp_rpt['status'] != 'success':
        # Unknown filepath, so return the error message
        return fp_rpt
    fp_rpt = fp_rpt['file']

    # Add new investigation type if needed
    investigation_type = _process_investigation_type(
        investigation_type, user_defined_investigation_type,
        new_investigation_type)

    msg = ''
    status = 'success'
    prep = None
    try:
        with warnings.catch_warnings(record=True) as warns:
            # deleting previous uploads and inserting new one
            prep = PrepTemplate.create(
                load_template_to_dataframe(fp_rpt), Study(study_id), data_type,
                investigation_type=investigation_type)
            remove(fp_rpt)

            # join all the warning messages into one. Note that this info
            # will be ignored if an exception is raised
            if warns:
                msg = '\n'.join(set(str(w.message) for w in warns))
                status = 'warning'
    except Exception as e:
        # Some error occurred while processing the prep template
        # Show the error to the user so he can fix the template
        status = 'error'
        msg = str(e)
    info = {'status': status,
            'message': msg,
            'file': prep_template,
            'id': prep.id if prep is not None else None}

    return info


def prep_template_patch_req(user_id, action):
    """Modifies an attribute of the prep template

    Parameters
    ----------
    user_id : str
        The id of the user performing the patch operation
    action: str
        JSON string containing the patch to apply using JSON PATCH [1]_

    References
    ----------
    .. [1] https://tools.ietf.org/html/rfc6902
    """
    as_json = loads(action)
    op = as_json['op']

    # Currently we are only supporting the replace operation
    if op != 'replace':
        return {'status': 'error',
                'message': 'Operation "%s" not supported. '
                           'Current supported operations: replace' % (op)}

    # Do some clean-up on the path for downstream easy handling
    path_str = as_json['path']
    if path_str.startswith('/'):
        path_str = path_str[1:]
    if path_str.endswith('/'):
        path_str = path_str[:-1]

    # The structure of the path should be /prep_id/attribute_to_modify/
    # so if we don't have those 2 elements, we should return an error
    path_list = path_str.split('/')
    if len(path_list) != 2:
        return {'status': 'error',
                'message': 'Incorrect path parameter'}

    # Extract all the parameters
    prep_id = path_list[0]
    attribute = path_list[1]
    value = as_json['value']

    # Check if the user actually has access to the prep template
    prep = PrepTemplate(prep_id)
    access_error = check_access(prep.study_id, user_id)
    if access_error:
        return access_error

    # Build a dictionary to point to the functions that will execute the
    # different operations
    if attribute == 'investigation_type':
        prep.investigation_type = value
    else:
        # We do not undertand the attribute so return an error
        return {'status': 'error',
                'message': 'Attribute "%s" not found. '
                           'Please, check the path parameter' % attribute}

    return {'status': 'success',
            'message': ''}


def prep_template_samples_get_req(prep_id, user_id):
    """Returns list of samples in the prep template

    Parameters
    ----------
    prep_id : int or str typecastable to int
        PrepTemplate id to get info for
    user_id : str
        User requesting the prep template info

    Returns
    -------
    dict
        Returns summary information in the form
        {'status': str,
         'message': str,
         'samples': list of str}
         samples is list of samples in the template
    """
    exists = _check_prep_template_exists(int(prep_id))
    if exists['status'] != 'success':
        return exists
    prep = PrepTemplate(int(prep_id))
    access_error = check_access(prep.study_id, user_id)
    if access_error:
        return access_error
    return {'status': 'success',
            'message': '',
            'samples': sorted(x for x in PrepTemplate(int(prep_id)))
            }


@execute_as_transaction
def prep_template_put_req(prep_id, user_id, prep_template=None,
                          investigation_type=None,
                          user_defined_investigation_type=None,
                          new_investigation_type=None):
    """Updates the prep template with the changes in the given file

    Parameters
    ----------
    prep_id : int
        The prep template to update
    user_id : str
        The current user object id
    prep_template : str, optional
        filepath to use for updating
    investigation_type: str, optional
        Existing investigation type to attach to the prep template
    user_defined_investigation_type: str, optional
        Existing user added investigation type to attach to the prep template
    new_investigation_type: str, optional
        Investigation type to add to the system

    Returns
    -------
    dict of str
        {'status': status,
         'message': message,
         'file': prep_template}
    """
    exists = _check_prep_template_exists(int(prep_id))
    if exists['status'] != 'success':
        return exists

    prep = PrepTemplate(int(prep_id))
    study_id = prep.study_id
    access_error = check_access(study_id, user_id)
    if access_error:
        return access_error

    if investigation_type:
        investigation_type = _process_investigation_type(
            investigation_type, user_defined_investigation_type,
            new_investigation_type)
        prep.investigation_type = investigation_type

    msg = ''
    status = 'success'
    if prep_template:
        fp = check_fp(study_id, prep_template)
        if fp['status'] != 'success':
            # Unknown filepath, so return the error message
            return fp
        fp = fp['file']
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

    Returns
    -------
    dict of str
        {'status': status,
         'message': message}
    """
    exists = _check_prep_template_exists(int(prep_id))
    if exists['status'] != 'success':
        return exists

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

    Returns
    -------
    dict of objects
        {'status': status,
         'message': message,
         'filepaths': [(filepath_id, filepath), ...]}
    """
    exists = _check_prep_template_exists(int(prep_id))
    if exists['status'] != 'success':
        return exists

    prep = PrepTemplate(int(prep_id))
    access_error = check_access(prep.study_id, user_id)
    if access_error:
        return access_error
    return {'status': 'success',
            'message': '',
            'filepaths': prep.get_filepaths()
            }


def ena_ontology_get_req():
    """Returns all system and user defined terms for prep template type

    Returns
    -------
    dict of objects
        {'status': status,
         'message': message,
         'ENA': [term1, term2, ...],
         'User': [userterm1, userterm2, ...]}
    """
    # Get all the ENA terms for the investigation type
    ontology = Ontology(convert_to_id('ENA', 'ontology'))
    ena_terms = sorted(ontology.terms)
    # make "Other" last on the list
    ena_terms.remove('Other')
    ena_terms.append('Other')

    return {'status': 'success',
            'message': '',
            'ENA': ena_terms,
            'User': sorted(ontology.user_defined_terms)
            }


def prep_template_graph_get_req(prep_id, user_id):
    """Returns graph of all artifacts created from the prep base artifact

    Parameters
    ----------
    prep_id : int
        Prep template ID to get graph for
    user_id : str
        User making the request

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
    exists = _check_prep_template_exists(int(prep_id))
    if exists['status'] != 'success':
        return exists

    prep = PrepTemplate(int(prep_id))
    access_error = check_access(prep.study_id, user_id)
    if access_error:
        return access_error
    G = prep.artifact.descendants
    node_labels = [(n.id, ' - '.join([n.name, n.artifact_type]))
                   for n in G.nodes()]
    return {'status': 'success',
            'message': '',
            'edge_list': [(n.id, m.id) for n, m in G.edges()],
            'node_labels': node_labels}
