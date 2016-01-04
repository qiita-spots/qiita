from __future__ import division
import warnings

from os import remove
from os.path import exists, join

from natsort import natsorted
# This is the only folder in qiita_pet that should import from outside
# qiita_pet. The idea is this proxies the call and response dicts we expect
# from the Qiita API once we build it. This will be removed and replaced with
#  API calls when the API is complete.
from qiita_db.metadata_template.sample_template import SampleTemplate
from qiita_db.study import Study
from qiita_core.util import execute_as_transaction
from qiita_core.qiita_settings import qiita_config

from qiita_db.metadata_template.util import (load_template_to_dataframe,
                                             looks_like_qiime_mapping_file)
from qiita_db.util import get_mountpoint
from qiita_ware.metadata_pipeline import (
    create_templates_from_qiime_mapping_file)
from qiita_pet.util import convert_text_html
from qiita_pet.handlers.api_proxy.util import check_access


def sample_template_summary_get_req(samp_id, user_id):
    """Returns a summary of the sample template metadata columns

    Parameters
    ----------
    samp_id : int
        SampleTemplate id to get info for
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
    access_error = check_access(samp_id, user_id)
    if access_error:
        return access_error
    template = SampleTemplate(int(samp_id))
    df = template.to_dataframe()
    out = {'status': 'success',
           'message': '',
           'num_samples': df.shape[0],
           'summary': {}}

    # drop the samp_id column if it exists
    if 'study_id' in df.columns:
        df.drop('study_id', axis=1, inplace=True)
    cols = list(df.columns)
    for column in cols:
        counts = df[column].value_counts()
        out['summary'][str(column)] = [(str(key), counts[key])
                                       for key in natsorted(counts.index)]

    return out


@execute_as_transaction
def sample_template_post_req(study_id, user_id, data_type,
                             sample_template):
    """Creates the sample template from the given file

    Parameters
    ----------
    study_id : int
        The current study object id
    user_id : str
        The current user object id
    data_type : str
        Data type for the sample template
    sample_template : str
        filepath to use for creation

    Returns
    -------
    dict
        results dictonary in the format
        {'status': status,
         'message': msg,
         'file': sample_template}

    status can be success, warning, or error depending on result
    message has the warnings or errors
    file has the file name
    """
    access_error = check_access(int(study_id), user_id)
    if access_error:
        return access_error
    # Get the uploads folder
    _, base_fp = get_mountpoint("uploads")[0]
    # Get the path of the sample template in the uploads folder
    fp_rsp = join(base_fp, str(study_id), sample_template)

    if not exists(fp_rsp):
        # The file does not exist, fail nicely
        return {'status': 'error',
                'message': 'filepath does not exist',
                'file': sample_template}

    # Define here the message and message level in case of success
    msg = ''
    status = 'success'
    is_mapping_file = looks_like_qiime_mapping_file(fp_rsp)
    if is_mapping_file and not data_type:
        return {'status': 'error',
                'message': 'Please, choose a data type if uploading a '
                           'QIIME mapping file',
                'file': sample_template}

    study = Study(int(study_id))
    try:
        with warnings.catch_warnings(record=True) as warns:
            if is_mapping_file:
                create_templates_from_qiime_mapping_file(fp_rsp, study,
                                                         int(data_type))
            else:
                SampleTemplate.create(load_template_to_dataframe(fp_rsp),
                                      study)
            remove(fp_rsp)

            # join all the warning messages into one. Note that this
            # info will be ignored if an exception is raised
            if warns:
                msg = '; '.join([convert_text_html(str(w.message))
                                 for w in warns])
                status = 'warning'

    except Exception as e:
        # Some error occurred while processing the sample template
        # Show the error to the user so they can fix the template
        status = 'error'
        msg = str(e)
    return {'status': status,
            'message': msg,
            'file': sample_template}


@execute_as_transaction
def sample_template_put_req(study_id, user_id, sample_template):
    """Updates a sample template using the given file

    Parameters
    ----------
    study_id : int
        The current study object id
    user_id : str
        The current user object id
    sample_template : str
        filepath to use for updating

    Returns
    -------
    dict
        results dictonary in the format
        {'status': status,
         'message': msg,
         'file': sample_template}

    status can be success, warning, or error depending on result
    message has the warnings or errors
    file has the file name
    """
    access_error = check_access(study_id, user_id)
    if access_error:
        return access_error
    # Define here the message and message level in case of success
    status = "success"
    # Get the uploads folder
    _, base_fp = get_mountpoint("uploads")[0]
    # Get the path of the sample template in the uploads folder
    fp_rsp = join(base_fp, str(study_id), sample_template)

    if not exists(fp_rsp):
        # The file does not exist, fail nicely
        return {'status': 'error',
                'message': 'file does not exist',
                'file': sample_template}

    msg = ''
    try:
        with warnings.catch_warnings(record=True) as warns:
            # deleting previous uploads and inserting new one
            st = SampleTemplate(study_id)
            df = load_template_to_dataframe(fp_rsp)
            st.extend(df)
            st.update(df)
            remove(fp_rsp)

            # join all the warning messages into one. Note that this info
            # will be ignored if an exception is raised
            if warns:
                msg = '\n'.join(set(str(w.message) for w in warns))
                status = 'warning'

    except Exception as e:
            status = 'error'
            msg = str(e)
    return {'status': status,
            'message': msg,
            'file': sample_template}


@execute_as_transaction
def sample_template_delete_req(study_id, user_id):
    """Deletes the sample template attached to the study

    Parameters
    ----------
    study_id : int
        The current study object id
    user_id : str
        The current user object id

    Returns
    -------
    dict
        results dictonary in the format
        {'status': status,
         'message': msg}

    status can be success, warning, or error depending on result
    message has the warnings or errors
    """
    access_error = check_access(int(study_id), user_id)
    if access_error:
        return access_error
    try:
        SampleTemplate.delete(int(study_id))
    except Exception as e:
        return {'status': 'error', 'message': str(e)}
    return {'status': 'success'}


@execute_as_transaction
def sample_template_filepaths_get_req(study_id, user_id):
    """Returns all the filepaths attached to the sample template

    Parameters
    ----------
    study_id : int
        The current study object id
    user_id : str
        The current user object id

    Returns
    -------
    dict
        Filepaths in the form
        {'status': status, message: msg, filepaths: filepaths}
        Where filepaths is a list of tuple of int and str
        All files in the sample template, as [(id, URL), ...]
    """
    access_error = check_access(study_id, user_id)
    if access_error:
        return access_error
    filepaths = []
    for id_, fp in SampleTemplate(int(study_id)).get_filepaths():
        # Convert filepaths to downloadable URL
        url = join(qiita_config.base_url, 'download',
                   fp[len(qiita_config.base_data_dir):].strip('/'))
        filepaths.append((id_, url))
    return {'status': 'success', 'message': '', 'filepaths': filepaths}
