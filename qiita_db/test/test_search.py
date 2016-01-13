# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import TestCase, main

import pandas as pd
from pandas.util.testing import assert_frame_equal

import qiita_db as qdb


class SearchTest(TestCase):
    """Tests that the search object works as expected"""

    def setUp(self):
        self.search = qdb.search.QiitaStudySearch()

    def test_parse_study_search_string(self):
        st_sql, samp_sql, meta = \
            self.search._parse_study_search_string("altitude > 0")
        exp_st_sql = ("SELECT study_id FROM qiita.study_sample_columns WHERE "
                      "lower(column_name) = lower('altitude') and column_type "
                      "in ('integer', 'float8') INTERSECT "
                      "SELECT study_id from qiita.study_portal "
                      "JOIN qiita.portal_type USING (portal_type_id) "
                      "WHERE portal = 'QIITA'")
        exp_samp_sql = ("SELECT ss.sample_id,sa.altitude "
                        "FROM qiita.study_sample ss "
                        "JOIN qiita.sample_{0} sa "
                        "ON ss.sample_id = sa.sample_id "
                        "JOIN qiita.study st ON st.study_id = ss.study_id "
                        "WHERE sa.altitude > 0")
        self.assertEqual(st_sql, exp_st_sql)
        self.assertEqual(samp_sql, exp_samp_sql)
        self.assertEqual(meta, ["altitude"])

        # test NOT
        st_sql, samp_sql, meta = \
            self.search._parse_study_search_string("NOT altitude > 0")
        exp_st_sql = ("SELECT study_id FROM qiita.study_sample_columns WHERE "
                      "lower(column_name) = lower('altitude') and column_type "
                      "in ('integer', 'float8') INTERSECT "
                      "SELECT study_id from qiita.study_portal "
                      "JOIN qiita.portal_type USING (portal_type_id) "
                      "WHERE portal = 'QIITA'")
        exp_samp_sql = ("SELECT ss.sample_id,sa.altitude "
                        "FROM qiita.study_sample ss "
                        "JOIN qiita.sample_{0} sa "
                        "ON ss.sample_id = sa.sample_id "
                        "JOIN qiita.study st ON st.study_id = ss.study_id "
                        "WHERE NOT sa.altitude > 0")
        self.assertEqual(st_sql, exp_st_sql)
        self.assertEqual(samp_sql, exp_samp_sql)
        self.assertEqual(meta, ["altitude"])

        # test AND
        st_sql, samp_sql, meta = \
            self.search._parse_study_search_string("ph > 7 and ph < 9")
        exp_st_sql = ("SELECT study_id FROM qiita.study_sample_columns WHERE "
                      "lower(column_name) = lower('ph') and column_type in "
                      "('integer', 'float8') INTERSECT "
                      "SELECT study_id from qiita.study_portal "
                      "JOIN qiita.portal_type USING (portal_type_id) "
                      "WHERE portal = 'QIITA'")
        exp_samp_sql = ("SELECT ss.sample_id,sa.ph "
                        "FROM qiita.study_sample ss "
                        "JOIN qiita.sample_{0} sa "
                        "ON ss.sample_id = sa.sample_id "
                        "JOIN qiita.study st ON st.study_id = ss.study_id "
                        "WHERE (sa.ph > 7 AND sa.ph < 9)")
        self.assertEqual(st_sql, exp_st_sql)
        self.assertEqual(samp_sql, exp_samp_sql)
        self.assertEqual(meta, ["ph"])

        # test OR
        st_sql, samp_sql, meta = \
            self.search._parse_study_search_string("ph > 7 or ph < 9")
        exp_st_sql = ("SELECT study_id FROM qiita.study_sample_columns WHERE "
                      "lower(column_name) = lower('ph') and column_type in "
                      "('integer', 'float8') INTERSECT "
                      "SELECT study_id from qiita.study_portal "
                      "JOIN qiita.portal_type USING (portal_type_id) "
                      "WHERE portal = 'QIITA'")
        exp_samp_sql = ("SELECT ss.sample_id,sa.ph "
                        "FROM qiita.study_sample ss "
                        "JOIN qiita.sample_{0} sa "
                        "ON ss.sample_id = sa.sample_id "
                        "JOIN qiita.study st ON st.study_id = ss.study_id "
                        "WHERE (sa.ph > 7 OR sa.ph < 9)")
        self.assertEqual(st_sql, exp_st_sql)
        self.assertEqual(samp_sql, exp_samp_sql)
        self.assertEqual(meta, ["ph"])

        # test includes
        st_sql, samp_sql, meta = \
            self.search._parse_study_search_string(
                'host_subject_id includes "Chicken little"')
        exp_st_sql = ("SELECT study_id FROM qiita.study_sample_columns "
                      "WHERE lower(column_name) = lower('host_subject_id') "
                      "and column_type in ('varchar') INTERSECT "
                      "SELECT study_id from qiita.study_portal "
                      "JOIN qiita.portal_type USING (portal_type_id) "
                      "WHERE portal = 'QIITA'")
        exp_samp_sql = ("SELECT ss.sample_id,sa.host_subject_id "
                        "FROM qiita.study_sample ss "
                        "JOIN qiita.sample_{0} sa "
                        "ON ss.sample_id = sa.sample_id "
                        "JOIN qiita.study st ON st.study_id = ss.study_id "
                        "WHERE LOWER(sa.host_subject_id) "
                        "LIKE '%chicken little%'")
        self.assertEqual(st_sql, exp_st_sql)
        self.assertEqual(samp_sql, exp_samp_sql)
        self.assertEqual(meta, ["host_subject_id"])

        # test complex query
        st_sql, samp_sql, meta = \
            self.search._parse_study_search_string(
                'name = "Billy Bob" or name = "Timmy" or name=Jimbo and '
                'name > 25 or name < 5')
        exp_st_sql = (
            "SELECT study_id FROM qiita.study_sample_columns WHERE "
            "lower(column_name) = lower('name') and column_type in "
            "('varchar') INTERSECT "
            "SELECT study_id from qiita.study_portal "
            "JOIN qiita.portal_type USING (portal_type_id) "
            "WHERE portal = 'QIITA'")
        exp_samp_sql = (
            "SELECT ss.sample_id,sa.name "
            "FROM qiita.study_sample ss "
            "JOIN qiita.sample_{0} sa "
            "ON ss.sample_id = sa.sample_id "
            "JOIN qiita.study st ON st.study_id = ss.study_id "
            "WHERE (sa.name = 'Billy Bob' OR sa.name = 'Timmy' OR "
            "(sa.name = 'Jimbo' AND sa.name > 25) OR sa.name < 5)")
        self.assertEqual(st_sql, exp_st_sql)
        self.assertEqual(samp_sql, exp_samp_sql)
        self.assertEqual(meta, ['name'])

        # test case sensitivity
        st_sql, samp_sql, meta = \
            self.search._parse_study_search_string("ph > 7 or pH < 9")
        # need to split sql because set used to create so can't guarantee order
        st_sql = st_sql.split(" INTERSECT ")

        exp_st_sql = ["SELECT study_id FROM qiita.study_sample_columns WHERE "
                      "lower(column_name) = lower('ph') and column_type in "
                      "('integer', 'float8')", "SELECT study_id FROM "
                      "qiita.study_sample_columns WHERE lower(column_name) = "
                      "lower('pH') and column_type in ('integer', 'float8')",
                      "SELECT study_id from qiita.study_portal "
                      "JOIN qiita.portal_type USING (portal_type_id) "
                      "WHERE portal = 'QIITA'"]
        exp_samp_sql = ("SELECT ss.sample_id,sa.pH,sa.ph "
                        "FROM qiita.study_sample ss "
                        "JOIN qiita.sample_{0} sa "
                        "ON ss.sample_id = sa.sample_id "
                        "JOIN qiita.study st ON st.study_id = ss.study_id "
                        "WHERE (sa.ph > 7 OR sa.ph < 9)")
        # use the split list to make sure the SQL is properly formed
        self.assertEqual(len(st_sql), 3)
        for pos, query in enumerate(exp_st_sql):
            self.assertEqual(st_sql[pos], query)
        self.assertEqual(samp_sql, exp_samp_sql)
        self.assertEqual(len(meta), 2)
        assert "ph" in meta
        assert "pH" in meta

    def test_call(self):
        obs_res, obs_meta = self.search(
            '(sample_type = ENVO:soil AND COMMON_NAME = "rhizosphere '
            'metagenome" ) AND NOT Description_duplicate includes Burmese',
            qdb.user.User("test@foo.bar"))
        exp_meta = ["COMMON_NAME", "Description_duplicate", "sample_type"]
        exp_res = {1:
                   [['1.SKM4.640180', 'rhizosphere metagenome', 'Bucu Rhizo',
                     'ENVO:soil'],
                    ['1.SKM5.640177', 'rhizosphere metagenome', 'Bucu Rhizo',
                     'ENVO:soil'],
                    ['1.SKD4.640185', 'rhizosphere metagenome', 'Diesel Rhizo',
                     'ENVO:soil'],
                    ['1.SKD6.640190', 'rhizosphere metagenome', 'Diesel Rhizo',
                    'ENVO:soil'],
                    ['1.SKM6.640187', 'rhizosphere metagenome', 'Bucu Rhizo',
                     'ENVO:soil'],
                    ['1.SKD5.640186', 'rhizosphere metagenome', 'Diesel Rhizo',
                     'ENVO:soil']]}
        self.assertEqual(obs_res, exp_res)
        self.assertEqual(obs_meta, exp_meta)

    def test_call_bad_meta_category(self):
        obs_res, obs_meta = self.search(
            'BAD_NAME_THING = ENVO:soil', qdb.user.User("test@foo.bar"))
        self.assertEqual(obs_res, {})
        self.assertEqual(obs_meta, ["BAD_NAME_THING"])

    def test_call_no_results(self):
        """makes sure a call on a required sample ID column that has no results
        actually returns no results"""
        obs_res, obs_meta = self.search('sample_type = unicorns_and_rainbows',
                                        qdb.user.User('test@foo.bar'))
        self.assertEqual(obs_res, {})
        self.assertEqual(obs_meta, ['sample_type'])

    def test_filter_by_processed_data(self):
        search = qdb.search.QiitaStudySearch()
        results, meta_cols = search(
            'study_id = 1', qdb.user.User('test@foo.bar'))
        spid, pds, meta = search.filter_by_processed_data()
        exp_spid = {1: {'18S': [4]}}
        exp_pds = {4: [
            '1.SKB1.640202', '1.SKB2.640194', '1.SKB3.640195', '1.SKB4.640189',
            '1.SKB5.640181', '1.SKB6.640176', '1.SKB7.640196', '1.SKB8.640193',
            '1.SKB9.640200', '1.SKD1.640179', '1.SKD2.640178', '1.SKD3.640198',
            '1.SKD4.640185', '1.SKD5.640186', '1.SKD6.640190', '1.SKD7.640191',
            '1.SKD8.640184', '1.SKD9.640182', '1.SKM1.640183', '1.SKM2.640199',
            '1.SKM3.640197', '1.SKM4.640180', '1.SKM5.640177', '1.SKM6.640187',
            '1.SKM7.640188', '1.SKM8.640201', '1.SKM9.640192']}
        exp_meta = pd.DataFrame.from_dict({x: 1 for x in exp_pds[4]},
                                          orient='index')
        exp_meta.rename(columns={0: 'study_id'}, inplace=True)

        self.assertEqual(spid, exp_spid)
        self.assertEqual(pds, exp_pds)
        self.assertEqual(meta.keys(), [1])
        assert_frame_equal(meta[1], exp_meta)


if __name__ == "__main__":
    main()
