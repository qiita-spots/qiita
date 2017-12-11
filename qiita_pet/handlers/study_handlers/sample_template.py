# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from os.path import basename
from json import loads, dumps

from tornado.web import authenticated, HTTPError
from natsort import natsorted

from qiita_core.qiita_settings import r_client
from qiita_pet.handlers.base_handlers import BaseHandler
from qiita_db.util import get_files_from_uploads_folders
from qiita_db.study import Study
from qiita_db.metadata_template.sample_template import SampleTemplate
from qiita_db.metadata_template.util import looks_like_qiime_mapping_file
from qiita_db.software import Software, Parameters
from qiita_db.processing_job import ProcessingJob
from qiita_db.exceptions import QiitaDBUnknownIDError

from qiita_pet.handlers.api_proxy import (
    data_types_get_req, sample_template_samples_get_req,
    prep_template_samples_get_req, study_prep_get_req,
    sample_template_meta_cats_get_req, sample_template_category_get_req,
    get_sample_template_processing_status,
    check_fp)


SAMPLE_TEMPLATE_KEY_FORMAT = 'sample_template_%s'


def sample_template_checks(study_id, user, check_exists=False):
    """Performs different checks and raises errors if any of the checks fail

    Parameters
    ----------
    study_id : int
        The study id
    user : qiita_db.user.User
        The user trying to access the study
    check_exists : bool, optional
        If true, check if the sample template exists

    Raises
    ------
    HTTPError
        404 if the study does not exist
        403 if the user does not have access to the study
        404 if check_exists == True and the sample template doesn't exist
    """
    try:
        study = Study(int(study_id))
    except QiitaDBUnknownIDError:
        raise HTTPError(404, 'Study does not exist')
    if not study.has_access(user):
        raise HTTPError(403, 'User does not have access to study')

    # Check if the sample template exists
    if check_exists and not SampleTemplate.exists(study_id):
        raise HTTPError(404, "Study %s doesn't have sample information"
                             % study_id)


def sample_template_handler_post_request(study_id, user, filepath,
                                         data_type=None):
    """Creates a new sample template

    Parameters
    ----------
    study_id: int
        The study to add the sample information
    user: qiita_db.user import User
        The user performing the request
    filepath: str
        The path to the sample template file
    data_type: str, optional
        If filepath is a QIIME mapping file, the data type of the prep
        information file

    Returns
    -------
    dict of {'job': str}
        job: the id of the job adding the sample information to the study

    Raises
    ------
    HTTPError
        404 if the filepath doesn't exist
    """
    # Check if the current user has access to the study
    sample_template_checks(study_id, user)

    # Check if the file exists
    fp_rsp = check_fp(study_id, filepath)
    if fp_rsp['status'] != 'success':
        raise HTTPError(404, 'Filepath not found')
    filepath = fp_rsp['file']

    is_mapping_file = looks_like_qiime_mapping_file(filepath)
    if is_mapping_file and not data_type:
        raise HTTPError(400, 'Please, choose a data type if uploading a '
                             'QIIME mapping file')

    qiita_plugin = Software.from_name_and_version('Qiita', 'alpha')
    cmd = qiita_plugin.get_command('create_sample_template')
    params = Parameters.load(
        cmd, values_dict={'fp': filepath, 'study_id': study_id,
                          'is_mapping_file': is_mapping_file,
                          'data_type': data_type})
    job = ProcessingJob.create(user, params, True)
    r_client.set(SAMPLE_TEMPLATE_KEY_FORMAT % study_id,
                 dumps({'job_id': job.id}))
    job.submit()
    return {'job': job.id}


def sample_template_handler_patch_request(user, req_op, req_path,
                                          req_value=None, req_from=None):
    """Patches the sample template

    Parameters
    ----------
    user: qiita_db.user.User
        The user performing the request
    req_op : str
        The operation to perform on the sample template
    req_path : str
        The path to the attribute to patch
    req_value : str, optional
        The new value
    req_from : str, optional
        The original path of the element

    Returns
    -------

    Raises
    ------
    HTTPError
        400 If the path parameter doens't follow the expected format
        400 If the given operation is not supported
    """
    req_path = [v for v in req_path.split('/') if v]
    # At this point we know the path should be at least length 2
    if len(req_path) < 2:
        raise HTTPError(400, 'Incorrect path parameter')

    study_id = int(req_path[0])
    # Check if the current user has access to the study and if the sample
    # template exists
    sample_template_checks(study_id, user, check_exists=True)

    if req_op == 'remove':
        # Path format
        # column: study_id/row_id/columns/column_name
        # sample: study_id/row_id/samples/sample_id
        if len(req_path) != 4:
            raise HTTPError(400, 'Incorrect path parameter')

        row_id = req_path[1]
        attribute = req_path[2]
        attr_id = req_path[3]

        qiita_plugin = Software.from_name_and_version('Qiita', 'alpha')
        cmd = qiita_plugin.get_command('delete_sample_or_column')
        params = Parameters.load(
            cmd, values_dict={'obj_class': 'SampleTemplate',
                              'obj_id': study_id,
                              'sample_or_col': attribute,
                              'name': attr_id})
        job = ProcessingJob.create(user, params, True)
        # Store the job id attaching it to the sample template id
        r_client.set(SAMPLE_TEMPLATE_KEY_FORMAT % study_id,
                     dumps({'job_id': job.id}))
        job.submit()
        return {'job': job.id, 'row_id': row_id}
    elif req_op == 'replace':
        # WARNING: Although the patch operation is a replace, is not a full
        # true replace. A replace is in theory equivalent to a remove + add.
        # In this case, the replace operation doesn't necessarily removes
        # anything (e.g. when only new columns/samples are being added to the)
        # sample information.
        # Path format: study_id/data
        # Forcing to specify data for extensibility. In the future we may want
        # to use this function to replace other elements of the sample
        # information
        if len(req_path) != 2:
            raise HTTPError(400, 'Incorrect path parameter')

        attribute = req_path[1]

        if attribute == 'data':
            # Update the sample information
            if req_value is None:
                raise HTTPError(400, "Value is required when updating "
                                     "sample information")

            # Check if the file exists
            fp_rsp = check_fp(study_id, req_value)
            if fp_rsp['status'] != 'success':
                raise HTTPError(404, 'Filepath not found')
            filepath = fp_rsp['file']

            qiita_plugin = Software.from_name_and_version('Qiita', 'alpha')
            cmd = qiita_plugin.get_command('update_sample_template')
            params = Parameters.load(
                cmd, values_dict={'study': study_id,
                                  'template_fp': filepath})
            job = ProcessingJob.create(user, params, True)

            # Store the job id attaching it to the sample template id
            r_client.set(SAMPLE_TEMPLATE_KEY_FORMAT % study_id,
                         dumps({'job_id': job.id}))

            job.submit()
            return {'job': job.id, 'row_id': None}
        else:
            raise HTTPError(404, 'Attribute %s not found' % attribute)

    else:
        raise HTTPError(400, 'Operation %s not supported. Current supported '
                             'operations: remove, replace' % req_op)


def sample_template_handler_delete_request(study_id, user):
    """Deletes the sample template

    Parameters
    ----------
    study_id: int
        The study to delete the sample information
    user: qiita_db.user
        The user performing the request

    Returns
    -------
    dict of {'job': str}
        job: the id of the job deleting the sample information to the study

    Raises
    ------
    HTTPError
        404 If the sample template doesn't exist
    """
    # Check if the current user has access to the study and if the sample
    # template exists
    sample_template_checks(study_id, user, check_exists=True)

    qiita_plugin = Software.from_name_and_version('Qiita', 'alpha')
    cmd = qiita_plugin.get_command('delete_sample_template')
    params = Parameters.load(cmd, values_dict={'study': int(study_id)})
    job = ProcessingJob.create(user, params, True)

    # Store the job if deleteing the sample template
    r_client.set(SAMPLE_TEMPLATE_KEY_FORMAT % study_id,
                 dumps({'job_id': job.id}))

    job.submit()

    return {'job': job.id}


class SampleTemplateHandler(BaseHandler):
    @authenticated
    def get(self):
        study_id = self.get_argument('study_id')

        # Check if the current user has access to the study
        sample_template_checks(study_id, self.current_user)

        self.render('study_ajax/sample_summary.html', study_id=study_id)

    @authenticated
    def post(self):
        study_id = int(self.get_argument('study_id'))
        filepath = self.get_argument('filepath')
        data_type = self.get_argument('data_type')

        self.write(sample_template_handler_post_request(
            study_id, self.current_user, filepath, data_type=data_type))

    @authenticated
    def patch(self):
        req_op = self.get_argument('op')
        req_path = self.get_argument('path')
        req_value = self.get_argument('value', None)
        req_from = self.get_argument('from', None)

        self.write(sample_template_handler_patch_request(
            self.current_user, req_op, req_path, req_value, req_from))

    @authenticated
    def delete(self):
        study_id = int(self.get_argument('study_id'))
        self.write(sample_template_handler_delete_request(
            study_id, self.current_user))


def sample_template_overview_handler_get_request(study_id, user):
    # Check if the current user has access to the sample template
    sample_template_checks(study_id, user)

    # Check if the sample template exists
    exists = SampleTemplate.exists(study_id)

    # The following information should always be provided:
    # The files that have been uploaded to the system and can be a
    # sample template file
    files = [f for _, f in get_files_from_uploads_folders(study_id)
             if f.endswith(('txt', 'tsv'))]
    # If there is a job associated with the sample information, the job id
    job = None
    job_info = r_client.get(SAMPLE_TEMPLATE_KEY_FORMAT % study_id)
    if job_info:
        job = loads(job_info)['job_id']

    # Specific information if it exists or not:
    data_types = []
    st_fp_id = None
    old_files = []
    num_samples = 0
    num_cols = 0
    if exists:
        # If it exists we need to provide:
        # The id of the sample template file so the user can download it and
        # the list of old filepaths
        st = SampleTemplate(study_id)
        all_st_files = st.get_filepaths()
        # The current sample template file is the first one in the list
        # (pop(0)) and we are interested only in the id ([0])
        st_fp_id = all_st_files.pop(0)[0]
        # For the old filepaths we are only interested in their basename
        old_files = [basename(fp) for _, fp in all_st_files]
        # The number of samples - this is a space efficient way of counting
        # the number of samples. Doing len(list(st.keys())) creates a list
        # that we are not using
        num_samples = sum(1 for _ in st.keys())
        # The number of columns
        num_cols = len(st.categories())
    else:
        # It doesn't exist, we also need to provide the data_types in case
        # the user uploads a QIIME mapping file
        data_types = sorted(data_types_get_req()['data_types'])

    return {'exists': exists,
            'uploaded_files': files,
            'data_types': data_types,
            'user_can_edit': Study(study_id).can_edit(user),
            'job': job,
            'download_id': st_fp_id,
            'old_files': old_files,
            'num_samples': num_samples,
            'num_columns': num_cols}


class SampleTemplateOverviewHandler(BaseHandler):
    @authenticated
    def get(self):
        study_id = int(self.get_argument('study_id'))
        self.write(
            sample_template_overview_handler_get_request(
                study_id, self.current_user))


def sample_template_summary_get_req(study_id, user):
    """Returns a summary of the sample template metadata columns

    Parameters
    ----------
    study_id: int
        The study to retrieve the sample information summary
    user: qiita_db.user
        The user performing the request

    Returns
    -------
    dict of {str: object}
        Keys are metadata categories and the values are list of tuples. Each
        tuple is an observed value in the category and the number of times
        it's seen.

    Raises
    ------
    HTTPError
        404 If the sample template doesn't exist
    """
    # Check if the current user has access to the study and if the sample
    # template exists
    sample_template_checks(study_id, user, check_exists=True)

    st = SampleTemplate(study_id)
    df = st.to_dataframe()

    # Drop the study_id column if it exists
    if 'study_id' in df.columns:
        df.drop('study_id', axis=1, inplace=True)

    res = {}
    for column in df.columns:
        counts = df[column].value_counts()
        res[str(column)] = [(str(key), counts[key])
                            for key in natsorted(
                                counts.index,
                                key=lambda x: unicode(x, errors='ignore'))]

    return res


class SampleTemplateSummaryHandler(BaseHandler):
    @authenticated
    def get(self):
        """Send formatted summary page of sample template"""
        study_id = int(self.get_argument('study_id'))
        self.write(
            sample_template_summary_get_req(study_id, self.current_user))


def _build_sample_summary(study_id, user_id):
    """Builds the initial table of samples associated with prep templates

    Parameters
    ----------
    study_id : int
        Study to get samples from
    user_id : str
        User requesting the information

    Returns
    -------
    columns : list of dict
        SlickGrid formatted list of columns
    samples_table : list of dict
        SlickGrid formatted table information
    """
    # Load all samples available into dictionary and set
    samps_table = {s: {'sample': s} for s in
                   sample_template_samples_get_req(
        study_id, user_id)['samples']}
    all_samps = set(samps_table.keys())
    columns = [{"id": "sample", "name": "Sample", "field": "sample",
                "width": 240, "sortable": False}]
    # Add one column per prep template highlighting what samples exist
    preps = study_prep_get_req(study_id, user_id)["info"]
    for dt in preps:
        for prep in preps[dt]:
            col_field = "prep%d" % prep["id"]
            col_name = "%s - %d" % (prep["name"], prep["id"])
            columns.append({"id": col_field,
                            "name": col_name,
                            "field": col_field,
                            "sortable": False,
                            "width": 240})

            prep_samples = prep_template_samples_get_req(
                prep['id'], user_id)['samples']
            # Empty cell for samples not in the prep template
            for s in all_samps.difference(prep_samples):
                samps_table[s][col_field] = ""
            # X in cell for samples in the prep template
            for s in all_samps.intersection(prep_samples):
                samps_table[s][col_field] = "X"

    return columns, samps_table.values()


class SampleAJAX(BaseHandler):
    @authenticated
    def get(self):
        """Show the sample summary page"""
        study_id = self.get_argument('study_id')

        res = sample_template_meta_cats_get_req(
            int(study_id), self.current_user.id)

        if res['status'] == 'error':
            if 'does not exist' in res['message']:
                raise HTTPError(404, res['message'])
            elif 'User does not have access to study' in res['message']:
                raise HTTPError(403, res['message'])
            else:
                raise HTTPError(500, res['message'])

        meta_cats = res['categories']
        cols, samps_table = _build_sample_summary(study_id,
                                                  self.current_user.id)
        _, alert_type, alert_msg = get_sample_template_processing_status(
            study_id)
        self.render('study_ajax/sample_prep_summary.html',
                    table=samps_table, cols=cols, meta_available=meta_cats,
                    study_id=study_id, alert_type=alert_type,
                    alert_message=alert_msg)

    @authenticated
    def post(self):
        study_id = int(self.get_argument('study_id'))
        meta_col = self.get_argument('meta_col')
        values = sample_template_category_get_req(meta_col, study_id,
                                                  self.current_user.id)
        if values['status'] != 'success':
            self.write(values)
        else:
            self.write({'status': 'success',
                        'message': '',
                        'values': values['values']
                        })
