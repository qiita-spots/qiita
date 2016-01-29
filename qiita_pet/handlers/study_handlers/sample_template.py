# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from tornado.web import authenticated, HTTPError

from qiita_pet.handlers.base_handlers import BaseHandler
from qiita_pet.util import is_localhost
from qiita_pet.handlers.util import download_link_or_path
from qiita_db.util import get_files_from_uploads_folders
from qiita_pet.handlers.api_proxy import (
    sample_template_summary_get_req,
    sample_template_post_req, sample_template_put_req,
    sample_template_delete_req, sample_template_filepaths_get_req,
    data_types_get_req, sample_template_samples_get_req,
    prep_template_samples_get_req, study_prep_get_req,
    sample_template_meta_cats_get_req, sample_template_category_get_req)


class SampleTemplateAJAX(BaseHandler):
    @authenticated
    def get(self):
        """Send formatted summary page of sample template"""
        study_id = self.get_argument('study_id')
        files = [f for _, f in get_files_from_uploads_folders(study_id)
                 if f.endswith(('txt', 'tsv'))]
        data_types = sorted(data_types_get_req()['data_types'])
        is_local = is_localhost(self.request.headers['host'])
        # Get the most recent version for download and build the link
        download = sample_template_filepaths_get_req(
            study_id, self.current_user.id)
        if 'filepaths' in download:
            download = download['filepaths'][-1]
        else:
            download = (-1, 'No sample information')
        dl_path = download_link_or_path(
            is_local, download[1], download[0], "Download sample information")

        stats = sample_template_summary_get_req(study_id, self.current_user.id)
        summary = stats['summary'] if 'summary' in stats else {}
        num_samples = stats['num_samples'] if 'num_samples' in stats else 0
        self.render('study_ajax/sample_summary.html', stats=summary,
                    num_samples=num_samples, dl_path=dl_path,
                    files=files, study_id=study_id, data_types=data_types)

    @authenticated
    def post(self):
        """Edit/delete/create sample template"""
        action = self.get_argument('action')
        study_id = self.get_argument('study_id')
        if action == 'create':
            filepath = self.get_argument('filepath')
            data_type = self.get_argument('data_type')
            result = sample_template_post_req(study_id, self.current_user.id,
                                              data_type, filepath)
        elif action == 'update':
            filepath = self.get_argument('filepath')
            result = sample_template_put_req(study_id, self.current_user.id,
                                             filepath)
        elif action == 'delete':
            result = sample_template_delete_req(study_id, self.current_user.id)
        else:
            raise HTTPError(400, 'Unknown sample template action: %s' % action)
        self.write(result)


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
    columns = [{'id': 'sample', 'name': 'Sample', 'field': 'sample',
                'width': 240, 'sortable': True}]
    # Add one column per prep template highlighting what samples exist
    preps = study_prep_get_req(study_id, user_id)['info']
    for dt in preps:
        for prep in preps[dt]:
            col_field = "prep%d" % prep['id']
            col_name = '%s - %d' % (prep['name'], prep['id'])
            columns.append({'id': col_field,
                            'name': col_name,
                            'field': col_field,
                            'sortable': True})

            prep_samples = prep_template_samples_get_req(
                prep['id'], user_id)['samples']
            # Empty cell for samples not in the prep template
            for s in all_samps.difference(prep_samples):
                samps_table[s][col_field] = ''
            # X in cell for samples in the prep template
            for s in all_samps.intersection(prep_samples):
                samps_table[s][col_field] = 'X'

    return columns, samps_table.values()


class SampleAJAX(BaseHandler):
    @authenticated
    def get(self):
        """Show the sample summary page"""
        study_id = self.get_argument('study_id')

        meta_cats = sample_template_meta_cats_get_req(
            int(study_id), self.current_user.id)['categories']
        cols, samps_table = _build_sample_summary(study_id,
                                                  self.current_user.id)
        self.render('study_ajax/sample_prep_summary.html',
                    table=samps_table, cols=cols, meta_available=meta_cats,
                    study_id=study_id)

    @authenticated
    def post(self):
        study_id = int(self.get_argument('study_id'))
        meta_col = self.get_argument('meta_col')
        values = sample_template_category_get_req(meta_col, study_id,
                                                  self.current_user.id)
        if values['status'] != 'success':
            self.write(values)
        else:
            # Format to list sorted by sample ID
            self.write({'status': 'success',
                        'message': '',
                        'values': [str(values['values'][s]) for s in
                                   sorted(values['values'])]
                        })
