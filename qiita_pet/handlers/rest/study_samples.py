# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from tornado.escape import json_encode, json_decode
import pandas as pd

from qiita_db.handlers.oauth2 import authenticate_oauth2
from .rest_handler import RESTHandler


class StudySamplesHandler(RESTHandler):

    @authenticate_oauth2(default_public=False, inject_user=False)
    def get(self, study_id):
        study = self.safe_get_study(study_id)
        if study is None:
            return

        if study.sample_template is None:
            samples = []
        else:
            samples = list(study.sample_template.keys())

        self.write(json_encode(samples))
        self.finish()

    @authenticate_oauth2(default_public=False, inject_user=False)
    def patch(self, study_id):
        study = self.safe_get_study(study_id)
        if study is None:
            return

        if study.sample_template is None:
            self.fail('No sample information found', 404)
            return
        else:
            sample_info = study.sample_template.to_dataframe()

        data = pd.DataFrame.from_dict(json_decode(self.request.body),
                                      orient='index')

        if len(data.index) == 0:
            self.fail('No samples provided', 400)
            return

        categories = set(study.sample_template.categories())

        if set(data.columns) != categories:
            if set(data.columns).issubset(categories):
                self.fail('Not all sample information categories provided',
                          400)
            else:
                unknown = set(data.columns) - categories
                self.fail("Some categories do not exist in the sample "
                          "information", 400,
                          categories_not_found=sorted(unknown))
            return

        existing_samples = set(sample_info.index)
        overlapping_ids = set(data.index).intersection(existing_samples)
        new_ids = set(data.index) - existing_samples
        status = 500

        # warnings generated are not currently caught
        # see https://github.com/biocore/qiita/issues/2096
        if overlapping_ids:
            to_update = data.loc[overlapping_ids]
            study.sample_template.update(to_update)
            status = 200

        if new_ids:
            to_extend = data.loc[new_ids]
            study.sample_template.extend(to_extend)
            status = 201

        self.set_status(status)
        self.finish()


class StudySamplesCategoriesHandler(RESTHandler):

    @authenticate_oauth2(default_public=False, inject_user=False)
    def get(self, study_id, categories):
        if not categories:
            self.fail('No categories specified', 405)
            return

        study = self.safe_get_study(study_id)
        if study is None:
            return

        categories = categories.split(',')

        if study.sample_template is None:
            self.fail('Study does not have sample information', 404)
            return

        available_categories = set(study.sample_template.categories())
        not_found = set(categories) - available_categories
        if not_found:
            self.fail('Category not found', 404,
                      categories_not_found=sorted(not_found))
            return

        blob = {'header': categories,
                'samples': {}}
        df = study.sample_template.to_dataframe()
        for idx, row in df[categories].iterrows():
            blob['samples'][idx] = list(row)

        self.write(json_encode(blob))
        self.finish()


class StudySamplesInfoHandler(RESTHandler):

    @authenticate_oauth2(default_public=False, inject_user=False)
    def get(self, study_id):
        study = self.safe_get_study(study_id)
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
