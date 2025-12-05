# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
import json
from datetime import datetime
from unittest import main

from tornado.escape import json_decode

from qiita_db.study import Study, StudyPerson
from qiita_db.user import User
from qiita_pet.test.rest.test_base import RESTHandlerTestCase


def _sample_creator(ids, categories=None):
    if categories is None:
        categories = [
            "season_environment",
            "env_package",
            "assigned_from_geo",
            "texture",
            "taxon_id",
            "depth",
            "host_taxid",
            "common_name",
            "water_content_soil",
            "elevation",
            "temp",
            "tot_nitro",
            "samp_salinity",
            "altitude",
            "env_biome",
            "country",
            "ph",
            "anonymized_name",
            "tot_org_carb",
            "description_duplicate",
            "env_feature",
            "physical_specimen_location",
            "physical_specimen_remaining",
            "dna_extracted",
            "sample_type",
            "collection_timestamp",
            "host_subject_id",
            "description",
            "latitude",
            "longitude",
            "scientific_name",
        ]
    return {i: {c: 1 for c in categories} for i in ids}


class StudySamplesHandlerTests(RESTHandlerTestCase):
    def _get_sample_categories(self, study_id):
        response = self.get("/api/v1/study/1/samples/info", headers=self.headers)
        self.assertEqual(response.code, 200)
        obs = json_decode(response.body)
        return obs["categories"]

    def test_patch_accept_new_categories(self):
        body = {
            "1.SKM1.999998": {
                "dna_extracted": "foo",
                "host_taxid": "foo",
                "altitude": "foo",
                "description_duplicate": "foo",
                "temp": "foo",
                "country": "foo",
                "texture": "foo",
                "latitude": "32.7157",
                "assigned_from_geo": "foo",
                "tot_org_carb": "foo",
                "env_feature": "foo",
                "depth": "foo",
                "tot_nitro": "foo",
                "anonymized_name": "foo",
                "scientific_name": "foo",
                "samp_salinity": "foo",
                "ph": "foo",
                "taxon_id": "9999",
                "season_environment": "foo",
                "physical_specimen_remaining": "foo",
                "host_subject_id": "foo",
                "water_content_soil": "foo",
                "env_biome": "foo",
                "env_package": "foo",
                "elevation": "foo",
                "collection_timestamp": ("2014-05-29 12:24:15"),
                "sample_type": "foo",
                "physical_specimen_location": "foo",
                "longitude": "117.1611",
                "common_name": "foo",
                "description": "foo",
            }
        }

        # first, confirm this should patch successfully: all fields present
        # note that response is 201 if using patch to add new samples, 200 if
        # updating existing samples.
        response = self.patch(
            "/api/v1/study/1/samples", headers=self.headers, data=body, asjson=True
        )
        self.assertEqual(response.code, 201)

        body = {
            "1.SKM1.999999": {
                "dna_extracted": "foo",
                "host_taxid": "foo",
                "altitude": "foo",
                "description_duplicate": "foo",
                "temp": "foo",
                "country": "foo",
                "texture": "foo",
                "latitude": "32.7157",
                "assigned_from_geo": "foo",
                "tot_org_carb": "foo",
                "env_feature": "foo",
                "depth": "foo",
                "tot_nitro": "foo",
                "anonymized_name": "foo",
                "scientific_name": "foo",
                "samp_salinity": "foo",
                "ph": "foo",
                "taxon_id": "9999",
                "season_environment": "foo",
                "physical_specimen_remaining": "foo",
                "host_subject_id": "foo",
                "water_content_soil": "foo",
                "env_biome": "foo",
                "env_package": "foo",
                "elevation": "foo",
                "collection_timestamp": ("2014-05-29 12:24:15"),
                "sample_type": "foo",
                "physical_specimen_location": "foo",
                "longitude": "117.1611",
                "common_name": "foo",
                "description": "foo",
            }
        }

        # add a new field to one sample_id, making body a superset of values.
        body["1.SKM1.999999"]["new_field1"] = "some_value"
        body["1.SKM1.999999"]["new_field2"] = "another_value"

        # this test should pass.
        response = self.patch(
            "/api/v1/study/1/samples", headers=self.headers, data=body, asjson=True
        )
        self.assertEqual(response.code, 201)

        # confirm new samples were added.
        response = self.get("/api/v1/study/1/samples", headers=self.headers)
        self.assertEqual(response.code, 200)
        obs = json_decode(response.body)
        self.assertIn("1.SKM1.999998", obs)
        self.assertIn("1.SKM1.999999", obs)

        # confirm new categories are a part of the samples.
        response = self.get("/api/v1/study/1/samples/info", headers=self.headers)
        self.assertEqual(response.code, 200)
        obs = json_decode(response.body)
        self.assertIn("new_field1", obs["categories"])
        self.assertIn("new_field2", obs["categories"])

        # remove a few existing fields, representing retired fields.
        for sample_id in body:
            del body[sample_id]["ph"]
            del body[sample_id]["water_content_soil"]

        exp = {"message": "Not all sample information categories provided"}
        response = self.patch(
            "/api/v1/study/1/samples", headers=self.headers, data=body, asjson=True
        )
        self.assertEqual(response.code, 400)
        obs = json_decode(response.body)
        self.assertEqual(obs, exp)

    def test_patch_no_study(self):
        body = {
            "sampleid1": {"category_a": "value_a"},
            "sampleid2": {"category_b": "value_b"},
        }

        exp = {"message": "Study not found"}
        response = self.patch(
            "/api/v1/study/0/samples", headers=self.headers, data=body, asjson=True
        )
        self.assertEqual(response.code, 404)
        obs = json_decode(response.body)
        self.assertEqual(obs, exp)

    def test_patch_no_samples(self):
        body = {}
        exp = {"message": "No samples provided"}
        response = self.patch(
            "/api/v1/study/1/samples", headers=self.headers, data=body, asjson=True
        )
        self.assertEqual(response.code, 400)
        obs = json_decode(response.body)
        self.assertEqual(obs, exp)

    def test_patch_no_sample_template(self):
        info = {
            "timeseries_type_id": 1,
            "metadata_complete": True,
            "mixs_compliant": True,
            "study_alias": "FCM",
            "study_description": "DESC",
            "study_abstract": "ABS",
            "principal_investigator_id": StudyPerson(3),
            "first_contact": datetime(2015, 5, 19, 16, 10),
            "most_recent_contact": datetime(2015, 5, 19, 16, 11),
        }

        new_study = Study.create(
            User("test@foo.bar"), "Some New Study for test jr", info
        )

        body = {
            "sampleid1": {"category_a": "value_a"},
            "sampleid2": {"category_b": "value_b"},
        }

        exp = {"message": "No sample information found"}
        response = self.patch(
            "/api/v1/study/%d/samples" % new_study.id,
            headers=self.headers,
            data=body,
            asjson=True,
        )
        self.assertEqual(response.code, 404)
        obs = json_decode(response.body)
        self.assertEqual(obs, exp)

    def test_patch_sample_ids_exist_incomplete_metadata(self):
        body = {
            "1.SKM3.640197": {"elevation": "xyz"},
            "1.SKM1.640183": {"elevation": "foo"},
        }

        exp = {"message": "Not all sample information categories provided"}
        response = self.patch(
            "/api/v1/study/1/samples", headers=self.headers, data=body, asjson=True
        )
        self.assertEqual(response.code, 400)
        obs = json_decode(response.body)
        self.assertEqual(obs, exp)

    def test_patch_sample_ids_complete_metadata_and_unknown_metadata(self):
        current = self._get_sample_categories(1)
        # If no new categories, both new and existing samples should succeed.
        # 640201 is an existing sample. blank.a1 is a new sample
        body = _sample_creator(["1.SKM8.640201", "blank.a1"], categories=current)
        response = self.patch(
            "/api/v1/study/1/samples", headers=self.headers, data=body, asjson=True
        )
        self.assertEqual(response.code, 201)
        # successful response should be empty string
        self.assertEqual(response.body, b"")

        # If new categories are added, patch() should succeed.
        # New and existing samples should have new categories.
        # 640201 is an existing sample. blank.a2 is a new sample
        body = _sample_creator(["1.SKM8.640201", "blank.a2"], categories=current)
        # body['blank.a2']['DOES_NOT_EXIST'] will be '', not None.
        # body['1.SKM8.640201']['WHAT'] will be '', not None.
        body["1.SKM8.640201"]["DOES_NOT_EXIST"] = "foo"
        body["blank.a2"]["WHAT"] = "bar"

        response = self.patch(
            "/api/v1/study/1/samples", headers=self.headers, data=body, asjson=True
        )
        self.assertEqual(response.code, 201)
        # successful response should be empty string
        self.assertEqual(response.body, b"")

        response = self.get(
            ("/api/v1/study/1/samples/categories=does_not_exist,what"),
            headers=self.headers,
        )
        self.assertEqual(response.code, 200)

        # decode results manually from bytes, replacing non-JSON-spec 'NaN'
        # values with JSON-spec 'null'. These will convert to Python None
        # values when load()ed.
        obs = response.body.decode("utf-8").replace("NaN", "null")
        obs = json.loads(obs)

        self.assertEqual(obs["header"], ["does_not_exist", "what"])

        self.assertEqual(obs["samples"]["1.blank.a2"], ["", "bar"])
        self.assertEqual(obs["samples"]["1.SKM8.640201"], ["foo", ""])

        # as the number and names of samples is dynamic, simply confirm the
        # other samples are unchanged.
        for sample in obs["samples"]:
            if sample not in ["1.blank.a2", "1.SKM8.640201"]:
                print(sample)
                self.assertEqual(obs["samples"][sample], [None, None])

        # If categories were removed, both existing and new samples should
        # fail.
        # 640201 is an existing sample. blank.a3 is a new sample
        current = self._get_sample_categories(1)
        body = _sample_creator(["1.SKM8.640201", "blank.a3"], categories=current)
        del body["1.SKM8.640201"]["env_biome"]
        del body["blank.a3"]["env_biome"]

        exp = {"message": "Not all sample information categories provided"}
        response = self.patch(
            "/api/v1/study/1/samples", headers=self.headers, data=body, asjson=True
        )
        self.assertEqual(response.code, 400)
        obs = json_decode(response.body)
        self.assertEqual(obs, exp)

    def test_patch_sample_ids_already_exist(self):
        current = self._get_sample_categories(1)
        body = _sample_creator(["1.SKM8.640201", "1.SKM3.640197"], categories=current)
        response = self.patch(
            "/api/v1/study/1/samples", headers=self.headers, data=body, asjson=True
        )
        self.assertEqual(response.code, 200)
        df = Study(1).sample_template.to_dataframe()
        self.assertEqual(df.loc["1.SKM8.640201"]["elevation"], "1")
        self.assertEqual(df.loc["1.SKM3.640197"]["elevation"], "1")

        # make sure we didn't touch other samples
        self.assertNotEqual(df.loc["1.SKM4.640180"]["elevation"], "1")

    def test_patch_sample_ids_do_not_exist(self):
        current = self._get_sample_categories(1)
        body = _sample_creator(["blank.a1"], categories=current)
        response = self.patch(
            "/api/v1/study/1/samples", headers=self.headers, data=body, asjson=True
        )
        self.assertEqual(response.code, 201)
        df = Study(1).sample_template.to_dataframe()
        self.assertNotEqual(df.loc["1.SKD7.640191"]["elevation"], "1")
        self.assertEqual(df.loc["1.blank.a1"]["elevation"], "1")

    def test_patch_sample_ids_partially_exist(self):
        current = self._get_sample_categories(1)
        body = _sample_creator(
            ["blank.b1", "1.SKM5.640177", "1.SKB9.640200"], categories=current
        )
        response = self.patch(
            "/api/v1/study/1/samples", headers=self.headers, data=body, asjson=True
        )
        self.assertEqual(response.code, 201)
        df = Study(1).sample_template.to_dataframe()
        self.assertEqual(df.loc["1.blank.b1"]["elevation"], "1")
        self.assertEqual(df.loc["1.SKM5.640177"]["elevation"], "1")
        self.assertEqual(df.loc["1.SKB9.640200"]["elevation"], "1")

        # make sure we didn't touch other samples
        self.assertNotEqual(df.loc["1.SKD3.640198"]["elevation"], "1")

    def test_get_valid(self):
        exp = sorted(
            [
                "1.SKB2.640194",
                "1.SKM4.640180",
                "1.SKB3.640195",
                "1.SKB6.640176",
                "1.SKD6.640190",
                "1.SKM6.640187",
                "1.SKD9.640182",
                "1.SKM8.640201",
                "1.SKM2.640199",
                "1.SKD2.640178",
                "1.SKB7.640196",
                "1.SKD4.640185",
                "1.SKB8.640193",
                "1.SKM3.640197",
                "1.SKD5.640186",
                "1.SKB1.640202",
                "1.SKM1.640183",
                "1.SKD1.640179",
                "1.SKD3.640198",
                "1.SKB5.640181",
                "1.SKB4.640189",
                "1.SKB9.640200",
                "1.SKM9.640192",
                "1.SKD8.640184",
                "1.SKM5.640177",
                "1.SKM7.640188",
                "1.SKD7.640191",
            ]
        )
        response = self.get("/api/v1/study/1/samples", headers=self.headers)
        self.assertEqual(response.code, 200)
        obs = json_decode(response.body)
        self.assertEqual(sorted(obs), exp)

    def test_get_invalid_no_study(self):
        exp = {"message": "Study not found"}
        response = self.get("/api/v1/study/0/samples", headers=self.headers)
        self.assertEqual(response.code, 404)
        obs = json_decode(response.body)
        self.assertEqual(obs, exp)

    def test_get_study_no_samples(self):
        info = {
            "timeseries_type_id": 1,
            "metadata_complete": True,
            "mixs_compliant": True,
            "study_alias": "FCM",
            "study_description": "DESC",
            "study_abstract": "ABS",
            "principal_investigator_id": StudyPerson(3),
            "first_contact": datetime(2015, 5, 19, 16, 10),
            "most_recent_contact": datetime(2015, 5, 19, 16, 11),
        }

        new_study = Study.create(User("test@foo.bar"), "Some New Study for test", info)

        exp = []
        response = self.get(
            "/api/v1/study/%d/samples" % new_study.id, headers=self.headers
        )
        self.assertEqual(response.code, 200)
        obs = json_decode(response.body)
        self.assertEqual(obs, exp)


class StudySamplesInfoHandlerTests(RESTHandlerTestCase):
    def test_get_valid(self):
        exp = {
            "number-of-samples": 27,
            "categories": [
                "season_environment",
                "assigned_from_geo",
                "texture",
                "taxon_id",
                "depth",
                "host_taxid",
                "common_name",
                "water_content_soil",
                "elevation",
                "temp",
                "tot_nitro",
                "samp_salinity",
                "altitude",
                "env_biome",
                "country",
                "ph",
                "anonymized_name",
                "tot_org_carb",
                "description_duplicate",
                "env_feature",
                "physical_specimen_location",
                "physical_specimen_remaining",
                "dna_extracted",
                "sample_type",
                "collection_timestamp",
                "host_subject_id",
                "description",
                "env_package",
                "latitude",
                "longitude",
                "scientific_name",
            ],
        }
        response = self.get("/api/v1/study/1/samples/info", headers=self.headers)
        self.assertEqual(response.code, 200)
        obs = json_decode(response.body)
        self.assertEqual(obs.keys(), exp.keys())
        self.assertEqual(obs["number-of-samples"], exp["number-of-samples"])
        self.assertCountEqual(obs["categories"], exp["categories"])

    def test_get_study_does_not_exist(self):
        exp = {"message": "Study not found"}
        response = self.get("/api/v1/study/0/samples/info", headers=self.headers)
        self.assertEqual(response.code, 404)
        obs = json_decode(response.body)
        self.assertEqual(obs, exp)

    def test_get_no_samples(self):
        # /api/v1/study/%d/samples/info -> {'number-of-samples':<int>,
        #                                   'categories': [<str>]}
        info = {
            "timeseries_type_id": 1,
            "metadata_complete": True,
            "mixs_compliant": True,
            "study_alias": "FCM",
            "study_description": "DESC",
            "study_abstract": "ABS",
            "principal_investigator_id": StudyPerson(3),
            "first_contact": datetime(2015, 5, 19, 16, 10),
            "most_recent_contact": datetime(2015, 5, 19, 16, 11),
        }

        new_study = Study.create(User("test@foo.bar"), "Some New Study for test", info)
        exp = {"number-of-samples": 0, "categories": []}
        response = self.get(
            "/api/v1/study/%d/samples/info" % new_study.id, headers=self.headers
        )
        self.assertEqual(response.code, 200)
        obs = json_decode(response.body)
        self.assertEqual(obs, exp)


class StudySamplesCategoriesHandlerTests(RESTHandlerTestCase):
    def test_get_valid_two_arg(self):
        df = Study(1).sample_template.to_dataframe()
        df = df[["ph", "country"]]
        df = {idx: [row["ph"], row["country"]] for idx, row in df.iterrows()}
        exp = {"header": ["ph", "country"], "samples": df}

        response = self.get(
            "/api/v1/study/1/samples/categories=ph,country", headers=self.headers
        )
        self.assertEqual(response.code, 200)
        obs = json_decode(response.body)
        self.assertEqual(obs, exp)

    def test_get_valid_one_arg(self):
        df = Study(1).sample_template.to_dataframe()
        df = df[["ph", "country"]]
        df = {idx: [row["country"]] for idx, row in df.iterrows()}
        exp = {"header": ["country"], "samples": df}

        response = self.get(
            "/api/v1/study/1/samples/categories=country", headers=self.headers
        )
        self.assertEqual(response.code, 200)
        obs = json_decode(response.body)
        self.assertEqual(obs, exp)

    def test_get_valid_two_arg_one_bad(self):
        exp = {"message": "Category not found", "categories_not_found": ["foo"]}
        response = self.get(
            "/api/v1/study/1/samples/categories=country,foo", headers=self.headers
        )
        self.assertEqual(response.code, 404)
        obs = json_decode(response.body)
        self.assertEqual(obs, exp)

    def test_get_study_does_not_exist(self):
        exp = {"message": "Study not found"}
        response = self.get(
            "/api/v1/study/0/samples/categories=foo", headers=self.headers
        )
        self.assertEqual(response.code, 404)
        obs = json_decode(response.body)
        self.assertEqual(obs, exp)

    def test_get_bad_category(self):
        exp = {"message": "Category not found", "categories_not_found": ["foo"]}
        response = self.get(
            "/api/v1/study/1/samples/categories=foo", headers=self.headers
        )
        self.assertEqual(response.code, 404)
        obs = json_decode(response.body)
        self.assertEqual(obs, exp)

    def test_get_no_category(self):
        exp = {"message": "No categories specified"}
        response = self.get("/api/v1/study/1/samples/categories=", headers=self.headers)
        self.assertEqual(response.code, 405)
        obs = json_decode(response.body)
        self.assertEqual(obs, exp)

    def test_get_no_samples(self):
        # /api/v1/study/%d/samples/info -> {'number-of-samples':<int>,
        #                                   'categories': [<str>]}
        info = {
            "timeseries_type_id": 1,
            "metadata_complete": True,
            "mixs_compliant": True,
            "study_alias": "FCM",
            "study_description": "DESC",
            "study_abstract": "ABS",
            "principal_investigator_id": StudyPerson(3),
            "first_contact": datetime(2015, 5, 19, 16, 10),
            "most_recent_contact": datetime(2015, 5, 19, 16, 11),
        }

        new_study = Study.create(User("test@foo.bar"), "Some New Study for test", info)

        exp = {"message": "Study does not have sample information"}
        response = self.get(
            "/api/v1/study/%d/samples/categories=foo" % new_study.id,
            headers=self.headers,
        )
        self.assertEqual(response.code, 404)
        obs = json_decode(response.body)
        self.assertEqual(obs, exp)


if __name__ == "__main__":
    main()
