# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
import io
from collections import defaultdict

import pandas as pd
from tornado.escape import json_decode, json_encode

from qiita_db.handlers.oauth2 import authenticate_oauth
from qiita_db.metadata_template.util import load_template_to_dataframe

from .rest_handler import RESTHandler


def _sample_details(study, samples):
    def detail_maker(**kwargs):
        base = {
            "sample_id": None,
            "sample_found": False,
            "ebi_sample_accession": None,
            "preparation_id": None,
            "ebi_experiment_accession": None,
            "preparation_visibility": None,
            "preparation_type": None,
        }

        assert set(kwargs).issubset(set(base)), "Unexpected key to set"

        base.update(kwargs)
        return base

    # cache sample detail for lookup
    study_samples = set(study.sample_template)
    sample_accessions = study.sample_template.ebi_sample_accessions

    # cache preparation information that we'll need

    # map of {sample_id: [indices, of, light, prep, info, ...]}
    sample_prep_mapping = defaultdict(list)
    pt_light = []
    offset = 0
    incoming_samples = set(samples)
    for pt in study.prep_templates():
        prep_samples = set(pt)
        overlap = incoming_samples & prep_samples

        if overlap:
            # cache if any of or query samples are present on the prep

            # reduce accessions to only samples of interest
            accessions = pt.ebi_experiment_accessions
            overlap_accessions = {i: accessions[i] for i in overlap}

            # store the detail we need
            pt_light.append((pt.id, overlap_accessions, pt.status, pt.data_type()))

            # only care about mapping the incoming samples
            for ptsample in overlap:
                sample_prep_mapping[ptsample].append(offset)

            offset += 1

    details = []
    for sample in samples:
        if sample in study_samples:
            # if the sample exists
            sample_acc = sample_accessions.get(sample)

            if sample in sample_prep_mapping:
                # if the sample is present in any prep, pull out the detail
                # specific to those preparations
                for pt_idx in sample_prep_mapping[sample]:
                    ptid, ptacc, ptstatus, ptdtype = pt_light[pt_idx]

                    details.append(
                        detail_maker(
                            sample_id=sample,
                            sample_found=True,
                            ebi_sample_accession=sample_acc,
                            preparation_id=ptid,
                            ebi_experiment_accession=ptacc.get(sample),
                            preparation_visibility=ptstatus,
                            preparation_type=ptdtype,
                        )
                    )
            else:
                # the sample is not present on any preparations
                details.append(
                    detail_maker(
                        sample_id=sample,
                        sample_found=True,
                        # it would be weird to have an EBI sample accession
                        # but not be present on a preparation...?
                        ebi_sample_accession=sample_acc,
                    )
                )
        else:
            # the is not present, let's note and move ona
            details.append(detail_maker(sample_id=sample))

    return details


class StudySampleDetailHandler(RESTHandler):
    @authenticate_oauth
    def get(self, study_id, sample_id):
        study = self.safe_get_study(study_id)
        sample_detail = _sample_details(
            study,
            [
                sample_id,
            ],
        )
        self.write(json_encode(sample_detail))
        self.finish()


class StudySamplesDetailHandler(RESTHandler):
    @authenticate_oauth
    def post(self, study_id):
        samples = json_decode(self.request.body)

        if "sample_ids" not in samples:
            self.fail("Missing sample_id key", 400)
            return

        study = self.safe_get_study(study_id)
        samples_detail = _sample_details(study, samples["sample_ids"])

        self.write(json_encode(samples_detail))
        self.finish()


class StudySamplesHandler(RESTHandler):
    @authenticate_oauth
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

    @authenticate_oauth
    def patch(self, study_id):
        study = self.safe_get_study(study_id)
        if study is None:
            return

        if study.sample_template is None:
            self.fail("No sample information found", 404)
            return
        else:
            sample_info = study.sample_template.to_dataframe()

        # convert from json into a format that qiita can validate
        rawdata = pd.DataFrame.from_dict(json_decode(self.request.body), orient="index")
        rawdata.index.name = "sample_name"
        if len(rawdata.index) == 0:
            self.fail("No samples provided", 400)
            return

        buffer = io.StringIO()
        rawdata.to_csv(buffer, sep="\t", index=True, header=True)
        buffer.seek(0)
        # validate on load
        data = load_template_to_dataframe(buffer)

        categories = set(study.sample_template.categories)

        # issuperset() will return True for true supersets or exact matches.
        # In either case, keep processing. Subsets of categories remain
        # invalid, however.
        if not set(data.columns).issuperset(categories):
            self.fail("Not all sample information categories provided", 400)
            return

        existing_samples = set(sample_info.index)
        overlapping_ids = set(data.index).intersection(existing_samples)
        new_ids = list(set(data.index) - existing_samples)
        status = 500

        # warnings generated are not currently caught
        # see https://github.com/biocore/qiita/issues/2096

        # processing new_ids first allows us to extend the sample_template
        # w/new columns before calling update(). update() will return an
        # error if unexpected columns are found.
        if new_ids:
            to_extend = data.loc[new_ids]
            study.sample_template.extend(to_extend)
            status = 201

        if overlapping_ids:
            to_update = data.loc[list(overlapping_ids)]
            study.sample_template.update(to_update)
            if status == 500:
                # don't overwrite a possible status = 201
                status = 200

        self.set_status(status)
        self.finish()


class StudySamplesCategoriesHandler(RESTHandler):
    @authenticate_oauth
    def get(self, study_id, categories):
        if not categories:
            self.fail("No categories specified", 405)
            return

        study = self.safe_get_study(study_id)
        if study is None:
            return

        categories = categories.split(",")

        if study.sample_template is None:
            self.fail("Study does not have sample information", 404)
            return

        available_categories = set(study.sample_template.categories)
        not_found = set(categories) - available_categories
        if not_found:
            self.fail("Category not found", 404, categories_not_found=sorted(not_found))
            return

        blob = {"header": categories, "samples": {}}
        df = study.sample_template.to_dataframe()
        for idx, row in df[categories].iterrows():
            blob["samples"][idx] = list(row)

        self.write(json_encode(blob))
        self.finish()


class StudySamplesInfoHandler(RESTHandler):
    @authenticate_oauth
    def get(self, study_id):
        study = self.safe_get_study(study_id)
        if study is None:
            return

        st = study.sample_template
        if st is None:
            info = {"number-of-samples": 0, "categories": []}
        else:
            info = {"number-of-samples": len(st), "categories": st.categories}

        self.write(json_encode(info))
        self.finish()
