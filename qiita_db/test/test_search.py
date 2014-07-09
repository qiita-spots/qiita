# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import TestCase, main

from qiita_core.util import qiita_test_checker
from qiita_db.search import QiitaStudySearch


@qiita_test_checker()
class SearchTest(TestCase):
    """Tests that the search object works as expected"""

    def setUp(self):
        self.search = QiitaStudySearch()

    def test_parse_study_search_string(self):
        search = QiitaStudySearch()
        st_sql, samp_sql, meta = \
            search._parse_study_search_string("altitude > 0")
        exp_st_sql = ("SELECT study_id FROM qiita.study_sample_columns WHERE "
                      "column_name = 'altitude'")
        exp_samp_sql = ("SELECT r.sample_id FROM qiita.required_sample_info r "
                        "JOIN qiita.sample_%s s ON s.sample_id = r.sample_id "
                        "WHERE s.altitude > 0")
        self.assertEqual(st_sql, exp_st_sql)
        self.assertEqual(samp_sql, exp_samp_sql)
        self.assertEqual(meta, {"altitude"})

        # test NOT
        st_sql, samp_sql, meta = \
            search._parse_study_search_string("NOT altitude > 0")
        exp_st_sql = ("SELECT study_id FROM qiita.study_sample_columns WHERE "
                      "column_name = 'altitude'")
        exp_samp_sql = ("SELECT r.sample_id FROM qiita.required_sample_info r "
                        "JOIN qiita.sample_%s s ON s.sample_id = r.sample_id "
                        "WHERE NOT s.altitude > 0")
        self.assertEqual(st_sql, exp_st_sql)
        self.assertEqual(samp_sql, exp_samp_sql)
        self.assertEqual(meta, {"altitude"})

        # test AND
        st_sql, samp_sql, meta = \
            search._parse_study_search_string("ph > 7 and ph < 9")
        exp_st_sql = ("SELECT study_id FROM qiita.study_sample_columns WHERE "
                      "column_name = 'ph'")
        exp_samp_sql = ("SELECT r.sample_id FROM qiita.required_sample_info r "
                        "JOIN qiita.sample_%s s ON s.sample_id = r.sample_id "
                        "WHERE (s.ph > 7 AND s.ph < 9)")
        self.assertEqual(st_sql, exp_st_sql)
        self.assertEqual(samp_sql, exp_samp_sql)
        self.assertEqual(meta, {"ph"})

        # test OR
        st_sql, samp_sql, meta = \
            search._parse_study_search_string("ph > 7 or ph < 9")
        exp_st_sql = ("SELECT study_id FROM qiita.study_sample_columns WHERE "
                      "column_name = 'ph'")
        exp_samp_sql = ("SELECT r.sample_id FROM qiita.required_sample_info r "
                        "JOIN qiita.sample_%s s ON s.sample_id = r.sample_id "
                        "WHERE (s.ph > 7 OR s.ph < 9)")
        self.assertEqual(st_sql, exp_st_sql)
        self.assertEqual(samp_sql, exp_samp_sql)
        self.assertEqual(meta, {"ph"})

        # test includes
        st_sql, samp_sql, meta = \
            search._parse_study_search_string(
                'host_subject_id includes "Chicken little"')
        exp_st_sql = ""
        exp_samp_sql = ("SELECT r.sample_id FROM qiita.required_sample_info r "
                        "JOIN qiita.sample_%s s ON s.sample_id = r.sample_id "
                        "WHERE r.host_subject_id LIKE 'Chicken little'")
        self.assertEqual(st_sql, exp_st_sql)
        self.assertEqual(samp_sql, exp_samp_sql)
        self.assertEqual(meta, {"host_subject_id"})

        # test case sensitivity
        st_sql, samp_sql, meta = \
            search._parse_study_search_string("ph > 7 or pH < 9")
        # need to split sql because set used to create so can't guarantee order
        st_sql = st_sql.split(" INTERSECT ")

        exp_st_sql = ["SELECT study_id FROM qiita.study_sample_columns WHERE "
                      "column_name = 'pH'", "SELECT study_id FROM "
                      "qiita.study_sample_columns WHERE column_name = 'ph'"]
        exp_samp_sql = ("SELECT r.sample_id FROM qiita.required_sample_info r "
                        "JOIN qiita.sample_%s s ON s.sample_id = r.sample_id "
                        "WHERE (s.ph > 7 OR s.ph < 9)")
        # use the split list to make sure the SQL is properly formed
        self.assertEqual(len(st_sql), 2)
        pos = exp_st_sql.index(st_sql[0])
        del exp_st_sql[pos]
        pos = exp_st_sql.index(st_sql[1])
        self.assertEqual(samp_sql, exp_samp_sql)
        self.assertEqual(meta, {"ph", "pH"})

    def test_call(self):
        obs_res, obs_meta = self.search(
            '(sample_type = ENVO:soil AND COMMON_NAME = "rhizosphere '
            'metagenome" ) AND NOT Description_duplicate includes Burmese',
            "test@foo.bar")
        exp_res = {1: ['SKM4.640180', 'SKB4.640189', 'SKB5.640181',
                       'SKB6.640176', 'SKM5.640177', 'SKD4.640185',
                       'SKD6.640190', 'SKM6.640187', 'SKD5.640186']}
        self.assertEqual(obs_res, exp_res)
        self.assertEqual(obs_meta, {"sample_type", "COMMON_NAME",
                                    "Description_duplicate"})

    def test_call_bad_meta_category(self):
        obs_res, obs_meta = self.search(
            'BAD_NAME_THING = ENVO:soil', "test@foo.bar")
        self.assertEqual(obs_res, {})
        self.assertEqual(obs_meta, {"BAD_NAME_THING"})


if __name__ == "__main__":
    main()
