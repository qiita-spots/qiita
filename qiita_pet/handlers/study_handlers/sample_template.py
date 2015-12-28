from json import dumps, loads

from tornado.web import authenticated, HTTPError
import pandas as pd

from qiita_pet.handlers.base_handlers import BaseHandler
from qiita_pet.util import is_localhost
from qiita_pet.handlers.util import download_link_or_path
from qiita_db.util import get_files_from_uploads_folders
from qiita_pet.handlers.api_proxy import (
    sample_template_summary_get_req,
    sample_template_post_req, sample_template_put_req,
    sample_template_delete_req, sample_template_filepaths_get_req,
    data_types_get_req, sample_template_get_req, prep_template_get_req,
    study_prep_get_req)


class SampleTemplateAJAX(BaseHandler):
    @authenticated
    def get(self):
        """Send formatted summary page of sample template"""
        study_id = self.get_argument('study_id')
        files = [f for _, f in get_files_from_uploads_folders(study_id)
                 if f.endswith(('txt', 'tsv'))]
        data_types = sorted(data_types_get_req())
        is_local = is_localhost(self.request.headers['host'])
        # Get the most recent version for download and build the link
        download = sample_template_filepaths_get_req(study_id,
                                                     self.current_user.id)[-1]
        dl_path = download_link_or_path(
            is_local, download[0], download[1], "Download sample information")

        stats = sample_template_summary_get_req(study_id, self.current_user.id)
        self.render('study_ajax/sample_summary.html', stats=stats['summary'],
                    num_samples=stats['num_samples'], dl_path=dl_path,
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


class SampleAJAX(BaseHandler):
    def get(self):
        """Show the sample summary page"""
        study_id = self.get_argument('study_id')
        meta_col = self.get_argument('meta_col', None)
        visible = self.get_argument('meta_visible', [])
        # Load sample template into dataframe and filter to wanted columns
        df = pd.DataFrame.from_dict(
            sample_template_get_req(int(study_id), self.current_user.id),
            orient='index', dtype=str)
        meta_available = set(df.columns)
        if visible:
            visible = loads(visible)
        if meta_col:
            visible.append(meta_col)

        # Add one column per prep template highlighting what samples exist
        prep_cols = []
        preps = study_prep_get_req(study_id, self.current_user.id)
        for dt in preps:
            for prep in preps[dt]:
                prep_samples = prep_template_get_req(
                    prep['id'], self.current_user.id).keys()
                prep_df = pd.Series(['X'] * len(prep_samples),
                                    index=prep_samples, dtype=str)
                col_name = ' - '.join([prep['name'], str(prep['id'])])
                prep_cols.append(col_name)
                df[col_name] = prep_df

        # Format the dataframe to html table
        meta_available = meta_available.difference(prep_cols)
        table = df.to_html(classes='table table-striped', na_rep='',
                           columns=prep_cols + visible)
        self.render('study_ajax/sample_prep_summary.html',
                    table=table, cols=sorted(meta_available),
                    meta_visible=dumps(visible), study_id=study_id)
