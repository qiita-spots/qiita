# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from tornado.escape import json_encode

from qiita_db.handlers.oauth2 import authenticate_oauth
from .rest_handler import RESTHandler


class StudySamplesHandler(RESTHandler):
    # /api/v1/study/<int>/samples

    @authenticate_oauth
    def get(self, study_id):
        study = self.study_boilerplate(study_id)
        if study is None:
            return

        if study.sample_template is None:
            samples = []
        else:
            samples = list(study.sample_template.keys())

        self.write(json_encode(samples))
        self.finish()


class StudySamplesCategoriesHandler(RESTHandler):
    # /api/v1/study/<int>/samples?foo

    @authenticate_oauth
    def get(self, study_id, categories):
        if not categories:
            self.fail('No categories specified', 405)
            return

        study = self.study_boilerplate(study_id)
        if study is None:
            return

        categories = categories.split(',')

        if study.sample_template is None:
            self.fail('Category not found', 404)
            return

        available_categories = set(study.sample_template.categories())
        if not set(categories).issubset(available_categories):
            self.fail('Category not found', 404)
            return

        blob = {'header': categories,
                'samples': {}}
        df = study.sample_template.to_dataframe()
        for idx, row in df[categories].iterrows():
            blob['samples'][idx] = list(row)

        self.write(json_encode(blob))
        self.finish()


class StudySamplesInfoHandler(RESTHandler):
    # /api/v1/study/<int>/samples/info

    @authenticate_oauth
    def get(self, study_id):
        study = self.study_boilerplate(study_id)
        if study is None:
            return

        st = study.sample_template
        if st is None:
            info = {'number-of-samples': 0,
                    'categories': []}
        else:
            info = {'number-of-samples': len(st),
                    'categories': st.categories()}

        self.write(json_encode(info))
        self.finish()
