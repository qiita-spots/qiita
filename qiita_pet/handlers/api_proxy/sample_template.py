# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from __future__ import division
from json import loads, dumps
from collections import defaultdict

from natsort import natsorted

from qiita_core.util import execute_as_transaction
from qiita_core.qiita_settings import r_client
from qiita_db.metadata_template.sample_template import SampleTemplate
from qiita_db.exceptions import QiitaDBUnknownIDError
from qiita_db.study import Study
from qiita_db.exceptions import QiitaDBColumnError
from qiita_db.user import User
from qiita_db.software import Software, Parameters
from qiita_db.processing_job import ProcessingJob
from qiita_pet.handlers.api_proxy.util import check_access, check_fp

SAMPLE_TEMPLATE_KEY_FORMAT = 'sample_template_%s'


def _check_sample_template_exists(samp_id):
    """Make sure a sample template exists in the system

    Parameters
    ----------
    samp_id : int or str castable to int
        SampleTemplate id to check

    Returns
    -------
    dict
        {'status': status,
         'message': msg}
    """
    if not SampleTemplate.exists(int(samp_id)):
        return {'status': 'error',
                'message': 'Sample template %d does not exist' % int(samp_id)
                }
    return {'status': 'success',
            'message': ''}


def sample_template_get_req(samp_id, user_id):
    """Gets the json of the full sample template

    Parameters
    ----------
    samp_id : int or int castable string
        SampleTemplate id to get info for
    user_id : str
        User requesting the sample template info

    Returns
    -------
    dict of objects
        {'status': status,
         'message': msg,
         'template': dict of {str: {str: object, ...}, ...}

        template is dictionary where the keys access_error the metadata samples
        and the values are a dictionary of column and value.
        Format {sample: {column: value, ...}, ...}
    """
    exists = _check_sample_template_exists(int(samp_id))
    if exists['status'] != 'success':
        return exists
    access_error = check_access(int(samp_id), user_id)
    if access_error:
        return access_error

    template = SampleTemplate(int(samp_id))
    access_error = check_access(template.study_id, user_id)
    if access_error:
        return access_error
    df = template.to_dataframe()
    return {'status': 'success',
            'message': '',
            'template': df.to_dict(orient='index')}


def sample_template_samples_get_req(samp_id, user_id):
    """Returns list of samples in the sample template

    Parameters
    ----------
    samp_id : int or str typecastable to int
        SampleTemplate id to get info for
    user_id : str
        User requesting the sample template info

    Returns
    -------
    dict
        Returns summary information in the form
        {'status': str,
         'message': str,
         'samples': list of str}
         samples is list of samples in the template
    """
    exists = _check_sample_template_exists(int(samp_id))
    if exists['status'] != 'success':
        return exists
    access_error = check_access(samp_id, user_id)
    if access_error:
        return access_error

    return {'status': 'success',
            'message': '',
            'samples': sorted(x for x in SampleTemplate(int(samp_id)))
            }


def sample_template_meta_cats_get_req(samp_id, user_id):
    """Returns list of metadata categories in the sample template

    Parameters
    ----------
    samp_id : int or str typecastable to int
        SampleTemplate id to get info for
    user_id : str
        User requesting the sample template info

    Returns
    -------
    dict
        Returns information in the form
        {'status': str,
         'message': str,
         'categories': list of str}
         samples is list of metadata categories in the template
    """
    exists = _check_sample_template_exists(int(samp_id))
    if exists['status'] != 'success':
        return exists
    access_error = check_access(samp_id, user_id)
    if access_error:
        return access_error

    return {'status': 'success',
            'message': '',
            'categories': sorted(SampleTemplate(int(samp_id)).categories())
            }


def sample_template_category_get_req(category, samp_id, user_id):
    """Returns dict of values for each sample in the given category

    Parameters
    ----------
    category : str
        Metadata category to get values for
    samp_id : int or str typecastable to int
        SampleTemplate id to get info for
    user_id : str
        User requesting the sample template info

    Returns
    -------
    dict
        Returns information in the form
        {'status': str,
         'message': str,
         'values': dict of {str: object}}
    """
    exists = _check_sample_template_exists(int(samp_id))
    if exists['status'] != 'success':
        return exists
    access_error = check_access(samp_id, user_id)
    if access_error:
        return access_error

    st = SampleTemplate(int(samp_id))
    try:
        values = st.get_category(category)
    except QiitaDBColumnError:
        return {'status': 'error',
                'message': 'Category %s does not exist in sample template' %
                category}
    return {'status': 'success',
            'message': '',
            'values': values}


def get_sample_template_processing_status(st_id):
    # Initialize variables here
    processing = False
    alert_type = ''
    alert_msg = ''
    job_info = r_client.get(SAMPLE_TEMPLATE_KEY_FORMAT % st_id)
    if job_info:
        job_info = defaultdict(lambda: '', loads(job_info))
        job_id = job_info['job_id']
        job = ProcessingJob(job_id)
        job_status = job.status
        processing = job_status not in ('success', 'error')
        if processing:
            alert_type = 'info'
            alert_msg = 'This sample template is currently being processed'
        elif job_status == 'error':
            alert_type = 'danger'
            alert_msg = job.log.msg.replace('\n', '</br>')
        else:
            alert_type = job_info['alert_type']
            alert_msg = job_info['alert_msg'].replace('\n', '</br>')

    return processing, alert_type, alert_msg


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
    dict
        Returns summary information in the form
        {'status': str,
         'message': str,
         'info': dict of {str: object}
        status can be success, warning, or error depending on result
        message has the warnings or errors
        info dictionary contains the keys as the metadata categories
        and the values are list of tuples. Each tuple is an observed value in
        the category and the number of times its seen.
        Format {num_samples: value,
                category: [(val1, count1), (val2, count2), ...], ...}
    """
    access_error = check_access(samp_id, user_id)
    if access_error:
        return access_error

    processing, alert_type, alert_msg = get_sample_template_processing_status(
        samp_id)

    exists = _check_sample_template_exists(int(samp_id))
    if exists['status'] != 'success':
        return {'status': 'success',
                'message': '',
                'num_samples': 0,
                'num_columns': 0,
                'editable': not processing,
                'alert_type': alert_type,
                'alert_message': alert_msg,
                'stats': {}}

    template = SampleTemplate(int(samp_id))

    df = template.to_dataframe()

    editable = (Study(template.study_id).can_edit(User(user_id)) and not
                processing)

    out = {'status': 'success',
           'message': '',
           'num_samples': df.shape[0],
           'num_columns': df.shape[1],
           'editable': editable,
           'alert_type': alert_type,
           'alert_message': alert_msg,
           'stats': {}}

    # drop the samp_id column if it exists
    if 'study_id' in df.columns:
        df.drop('study_id', axis=1, inplace=True)
    for column in df.columns:
        counts = df[column].value_counts()
        out['stats'][str(column)] = [(str(key), counts[key])
                                     for key in natsorted(
                                        counts.index,
                                        key=lambda x: unicode(
                                            x, errors='ignore'))]

    return out


def sample_template_put_req(study_id, user_id, sample_template):
    """Updates a sample template using the given file

    Parameters
    ----------
    study_id : int
        The current study object id
    user_id : str
        The current user object id
    sample_template : str
        filename to use for updating

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
    exists = _check_sample_template_exists(int(study_id))
    if exists['status'] != 'success':
        return exists
    access_error = check_access(int(study_id), user_id)
    if access_error:
        return access_error

    fp_rsp = check_fp(study_id, sample_template)
    if fp_rsp['status'] != 'success':
        # Unknown filepath, so return the error message
        return fp_rsp
    fp_rsp = fp_rsp['file']

    msg = ''
    status = 'success'

    # Offload the update of the sample template to the cluster
    qiita_plugin = Software.from_name_and_version('Qiita', 'alpha')
    cmd = qiita_plugin.get_command('update_sample_template')
    params = Parameters.load(cmd, values_dict={'study': int(study_id),
                                               'template_fp': fp_rsp})
    job = ProcessingJob.create(User(user_id), params, True)

    # Store the job id attaching it to the sample template id
    r_client.set(SAMPLE_TEMPLATE_KEY_FORMAT % study_id,
                 dumps({'job_id': job.id}))

    job.submit()

    return {'status': status,
            'message': msg,
            'file': sample_template}


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
        {'status': status,
         'message': msg,
         'filepaths': filepaths}
        status can be success, warning, or error depending on result
        message has the warnings or errors
        filepaths is a list of tuple of int and str
        All files in the sample template, as [(id, URL), ...]
    """
    exists = _check_sample_template_exists(int(study_id))
    if exists['status'] != 'success':
        return exists
    access_error = check_access(study_id, user_id)
    if access_error:
        return access_error

    try:
        template = SampleTemplate(int(study_id))
    except QiitaDBUnknownIDError as e:
        return {'status': 'error',
                'message': str(e)}

    return {'status': 'success',
            'message': '',
            'filepaths': template.get_filepaths()
            }
