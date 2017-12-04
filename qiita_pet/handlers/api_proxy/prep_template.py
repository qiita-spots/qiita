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
from os.path import basename
from json import loads, dumps
from collections import defaultdict

from natsort import natsorted

from qiita_core.util import execute_as_transaction
from qiita_core.qiita_settings import r_client
from qiita_pet.handlers.api_proxy.util import check_access, check_fp
from qiita_pet.util import get_network_nodes_edges
from qiita_db.metadata_template.util import load_template_to_dataframe
from qiita_db.util import convert_to_id, get_files_from_uploads_folders
from qiita_db.study import Study
from qiita_db.user import User
from qiita_db.ontology import Ontology
from qiita_db.metadata_template.prep_template import PrepTemplate
from qiita_db.processing_job import ProcessingJob
from qiita_db.software import Software, Parameters

PREP_TEMPLATE_KEY_FORMAT = 'prep_template_%s'


def _get_ENA_ontology():
    """Returns the information of the ENA ontology

    Returns
    -------
    dict of {str: list of strings}
        A dictionary of the form {'ENA': list of str, 'User': list of str}
        with the ENA-defined terms and the User-defined terms, respectivelly.
    """
    ontology = Ontology(convert_to_id('ENA', 'ontology'))
    ena_terms = sorted(ontology.terms)
    # make "Other" last on the list
    ena_terms.remove('Other')
    ena_terms.append('Other')

    return {'ENA': ena_terms, 'User': sorted(ontology.user_defined_terms)}


def new_prep_template_get_req(study_id):
    """Returns the information needed to populate the new prep info template

    Parameters
    ----------
    study_id : int
        The study id

    Returns
    -------
    (list of str, list of str, dict of {str: list of str})
        The list of txt, tsv files in the upload dir for the given study
        The list of available data types
        The investigation type ontology information
    """
    prep_files = [f for _, f in get_files_from_uploads_folders(study_id)
                  if f.endswith(('.txt', '.tsv'))]
    data_types = sorted(Study.all_data_types())

    # Get all the ENA terms for the investigation type
    ontology_info = _get_ENA_ontology()

    return {'status': 'success',
            'prep_files': prep_files,
            'data_types': data_types,
            'ontology': ontology_info}


def prep_template_ajax_get_req(user_id, prep_id):
    """Returns the prep tempalte information needed for the AJAX handler

    Parameters
    ----------
    user_id : str
        The user id
    prep_id : int
        The prep template id

    Returns
    -------
    dict of {str: object}
        A dictionary with the following keys:
        - status: str, whether the request is successful or not
        - message: str, if the request is unsuccessful, a human readable error
        - name: str, the name of the prep template
        - files: list of str, the files available to update the prep template
        - download_prep: int, the filepath_id of the prep file
        - download_qiime, int, the filepath_id of the qiime mapping file
        - num_samples: int, the number of samples present in the template
        - num_columns: int, the number of columns present in the template
        - investigation_type: str, the investigation type of the template
        - ontology: str, dict of {str, list of str} containing the information
        of the ENA ontology
        - artifact_attached: bool, whether the template has an artifact
        attached
        - study_id: int, the study id of the template
    """
    # Currently there is no name attribute, but it will be soon
    name = "Prep information %d" % prep_id
    pt = PrepTemplate(prep_id)

    # Initialize variables here
    processing = False
    alert_type = ''
    alert_msg = ''
    job_info = r_client.get(PREP_TEMPLATE_KEY_FORMAT % prep_id)
    if job_info:
        job_info = defaultdict(lambda: '', loads(job_info))
        job_id = job_info['job_id']
        job = ProcessingJob(job_id)
        job_status = job.status
        processing = job_status not in ('success', 'error')
        if processing:
            alert_type = 'info'
            alert_msg = 'This prep template is currently being updated'
        elif job_status == 'error':
            alert_type = 'danger'
            alert_msg = job.log.msg.replace('\n', '</br>')
        else:
            alert_type = job_info['alert_type']
            alert_msg = job_info['alert_msg'].replace('\n', '</br>')

    artifact_attached = pt.artifact is not None
    study_id = pt.study_id
    files = [f for _, f in get_files_from_uploads_folders(study_id)
             if f.endswith(('.txt', '.tsv'))]

    # The call to list is needed because keys is an iterator
    num_samples = len(list(pt.keys()))
    num_columns = len(pt.categories())
    investigation_type = pt.investigation_type

    download_prep_id = None
    download_qiime_id = None
    other_filepaths = []
    for fp_id, fp in pt.get_filepaths():
        fp = basename(fp)
        if 'qiime' in fp:
            if download_qiime_id is None:
                download_qiime_id = fp_id
        else:
            if download_prep_id is None:
                download_prep_id = fp_id
            else:
                other_filepaths.append(fp)

    ontology = _get_ENA_ontology()

    editable = Study(study_id).can_edit(User(user_id)) and not processing

    return {'status': 'success',
            'message': '',
            'name': name,
            'files': files,
            'download_prep_id': download_prep_id,
            'download_qiime_id': download_qiime_id,
            'other_filepaths': other_filepaths,
            'num_samples': num_samples,
            'num_columns': num_columns,
            'investigation_type': investigation_type,
            'ontology': ontology,
            'artifact_attached': artifact_attached,
            'study_id': study_id,
            'editable': editable,
            'data_type': pt.data_type(),
            'alert_type': alert_type,
            'is_submitted_to_ebi': pt.is_submitted_to_ebi,
            'alert_message': alert_msg}


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
                'category': [(val1, count1), (val2, count2), ...],
                'editable': bool}
    """
    exists = _check_prep_template_exists(int(prep_id))
    if exists['status'] != 'success':
        return exists

    prep = PrepTemplate(int(prep_id))
    access_error = check_access(prep.study_id, user_id)
    if access_error:
        return access_error

    editable = Study(prep.study_id).can_edit(User(user_id))
    df = prep.to_dataframe()
    out = {'num_samples': df.shape[0],
           'summary': [],
           'status': 'success',
           'message': '',
           'editable': editable}

    cols = sorted(list(df.columns))
    for column in cols:
        counts = df[column].value_counts()
        out['summary'].append(
            (str(column), [(str(key), counts[key])
                           for key in natsorted(counts.index)]))
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


def prep_template_patch_req(user_id, req_op, req_path, req_value=None,
                            req_from=None):
    """Modifies an attribute of the prep template

    Parameters
    ----------
    user_id : str
        The id of the user performing the patch operation
    req_op : str
        The operation to perform on the prep information
    req_path : str
        The prep information and attribute to patch
    req_value : str, optional
        The value that needs to be modified
    req_from : str, optional
        The original path of the element

    Returns
    -------
    dict of {str, str, str}
        A dictionary with the following keys:
        - status: str, whether if the request is successful or not
        - message: str, if the request is unsuccessful, a human readable error
        - row_id: str, the row_id that we tried to delete
    """
    req_path = [v for v in req_path.split('/') if v]
    if req_op == 'replace':
        # The structure of the path should be /prep_id/attribute_to_modify/
        # so if we don't have those 2 elements, we should return an error
        if len(req_path) != 2:
            return {'status': 'error',
                    'message': 'Incorrect path parameter'}
        prep_id = int(req_path[0])
        attribute = req_path[1]

        # Check if the user actually has access to the prep template
        prep = PrepTemplate(prep_id)
        access_error = check_access(prep.study_id, user_id)
        if access_error:
            return access_error

        status = 'success'
        msg = ''
        if attribute == 'investigation_type':
            prep.investigation_type = req_value
        elif attribute == 'data':
            fp = check_fp(prep.study_id, req_value)
            if fp['status'] != 'success':
                return fp
            fp = fp['file']
            qiita_plugin = Software.from_name_and_version('Qiita', 'alpha')
            cmd = qiita_plugin.get_command('update_prep_template')
            params = Parameters.load(
                cmd, values_dict={'prep_template': prep_id, 'template_fp': fp})
            job = ProcessingJob.create(User(user_id), params, True)

            r_client.set(PREP_TEMPLATE_KEY_FORMAT % prep_id,
                         dumps({'job_id': job.id}))
            job.submit()
        else:
            # We don't understand the attribute so return an error
            return {'status': 'error',
                    'message': 'Attribute "%s" not found. '
                               'Please, check the path parameter' % attribute}

        return {'status': status, 'message': msg}
    elif req_op == 'remove':
        # The structure of the path should be:
        # /prep_id/row_id/{columns|samples}/name
        if len(req_path) != 4:
            return {'status': 'error',
                    'message': 'Incorrect path parameter'}
        prep_id = int(req_path[0])
        row_id = req_path[1]
        attribute = req_path[2]
        attr_id = req_path[3]

        # Check if the user actually has access to the study
        pt = PrepTemplate(prep_id)
        access_error = check_access(pt.study_id, user_id)
        if access_error:
            return access_error

        qiita_plugin = Software.from_name_and_version('Qiita', 'alpha')
        cmd = qiita_plugin.get_command('delete_sample_or_column')
        params = Parameters.load(
            cmd, values_dict={'obj_class': 'PrepTemplate',
                              'obj_id': prep_id,
                              'sample_or_col': attribute,
                              'name': attr_id})
        job = ProcessingJob.create(User(user_id), params, True)
        # Store the job id attaching it to the sample template id
        r_client.set(PREP_TEMPLATE_KEY_FORMAT % prep_id,
                     dumps({'job_id': job.id}))
        job.submit()
        return {'status': 'success', 'message': '', 'row_id': row_id}
    else:
        return {'status': 'error',
                'message': 'Operation "%s" not supported. '
                           'Current supported operations: replace, remove'
                           % req_op,
                'row_id': '0'}


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
        msg = str(e)
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

    # We should filter for only the public artifacts if the user
    # doesn't have full access to the study
    full_access = Study(prep.study_id).can_edit(User(user_id))

    artifact = prep.artifact

    if artifact is None:
        return {'edges': [], 'nodes': [],
                'status': 'success', 'message': ''}

    G = artifact.descendants_with_jobs

    nodes, edges, wf_id = get_network_nodes_edges(G, full_access)

    return {'edges': edges,
            'nodes': nodes,
            'workflow': wf_id,
            'status': 'success',
            'message': ''}


def prep_template_jobs_get_req(prep_id, user_id):
    """Returns graph of all artifacts created from the prep base artifact

    Parameters
    ----------
    prep_id : int
        Prep template ID to get graph for
    user_id : str
        User making the request

    Returns
    -------
    dict with the jobs information

    Notes
    -----
    Nodes are identified by the corresponding Artifact ID.
    """
    prep = PrepTemplate(int(prep_id))
    access_error = check_access(prep.study_id, user_id)
    if access_error:
        return access_error

    job_info = r_client.get(PREP_TEMPLATE_KEY_FORMAT % prep_id)
    result = {}
    if job_info:
        job_info = defaultdict(lambda: '', loads(job_info))
        job_id = job_info['job_id']
        job = ProcessingJob(job_id)
        result[job.id] = {'status': job.status, 'step': job.step,
                          'error': job.log.msg if job.log else ""}

    return result
