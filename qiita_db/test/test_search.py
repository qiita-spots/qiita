# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import TestCase, main
from pyparsing import ParseException

from qiita_db.user import User
from qiita_db.study import Study
from qiita_db.search import QiitaStudySearch


class SearchTest(TestCase):
    """Tests that the search object works as expected"""

    def setUp(self):
        self.search = QiitaStudySearch()

    def test_parse_search(self):
        samp_sql, meta = \
            self.search._parse_search("altitude > 0")
        exp_samp_sql = ("sr.altitude > 0")
        self.assertEqual(samp_sql, exp_samp_sql)
        self.assertEqual(meta, [('altitude', "('integer', 'float8')")])

        # test NOT
        samp_sql, meta = \
            self.search._parse_search("NOT altitude > 0")
        exp_samp_sql = ("NOT sr.altitude > 0")
        self.assertEqual(samp_sql, exp_samp_sql)
        self.assertEqual(meta, [('altitude', "('integer', 'float8')")])

        # test AND
        samp_sql, meta = \
            self.search._parse_search("ph > 7 and ph < 9")
        exp_samp_sql = ("(sr.ph > 7 AND sr.ph < 9)")
        self.assertEqual(samp_sql, exp_samp_sql)
        self.assertEqual(meta, [('ph', "('integer', 'float8')"),
                                ('ph', "('integer', 'float8')")])

        # test OR
        samp_sql, meta = \
            self.search._parse_search("ph > 7 or ph < 9")
        exp_samp_sql = ("(sr.ph > 7 OR sr.ph < 9)")
        self.assertEqual(samp_sql, exp_samp_sql)
        self.assertEqual(meta, [('ph', "('integer', 'float8')"),
                                ('ph', "('integer', 'float8')")])

        # test includes
        samp_sql, meta = \
            self.search._parse_search(
                'host_subject_id includes "Chicken little"')
        exp_samp_sql = ("LOWER(sr.host_subject_id) LIKE '%chicken little%'")
        self.assertEqual(samp_sql, exp_samp_sql)
        self.assertEqual(meta, [('host_subject_id', "('varchar')")])

        # Test complex query
        samp_sql, meta = \
            self.search._parse_search(
                'name = "Billy Bob" or name = "Timmy" or name=Jimbo and '
                'ph > 5 or ph < 5')
        exp_samp_sql = ("(sr.name = 'Billy Bob' OR sr.name = 'Timmy' OR "
                        "(sr.name = 'Jimbo' AND sr.ph > 5) OR sr.ph < 5)")
        self.assertEqual(samp_sql, exp_samp_sql)
        self.assertEqual(meta, [('name', "('varchar')"),
                                ('name', "('varchar')"),
                                ('name', "('varchar')"),
                                ('ph', "('integer', 'float8')"),
                                ('ph', "('integer', 'float8')")])

        # test case sensitivity
        samp_sql, meta = \
            self.search._parse_search("ph > 7 or pH < 9")
        exp_samp_sql = ("(sr.ph > 7 OR sr.ph < 9)")
        self.assertEqual(samp_sql, exp_samp_sql)
        self.assertEqual(meta, [('ph', "('integer', 'float8')"),
                                ('ph', "('integer', 'float8')")])

    def test_call(self):
        obs_res, obs_meta = self.search(
            '(sample_type = ENVO:soil AND COMMON_NAME = "rhizosphere '
            'metagenome" ) AND NOT Description_duplicate includes Burmese',
            User("test@foo.bar"))
        exp_meta = ["common_name", "description_duplicate", "sample_type"]
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

    def test_call_study(self):
        obs_res, obs_meta = self.search(
            '(sample_type = ENVO:soil AND COMMON_NAME = "rhizosphere '
            'metagenome" ) AND NOT Description_duplicate includes Burmese',
            User("test@foo.bar"), study=Study(1))
        exp_meta = ["common_name", "description_duplicate", "sample_type"]
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

    def test_call_mixed_types(self):
        with self.assertRaises(ParseException):
            self.search(
                'name = "Billy Bob" or name = "Timmy" or name=Jimbo and '
                'name > 5 or name < 5', User("test@foo.bar"))

    def test_call_bad_meta_category(self):
        obs_res, obs_meta = self.search(
            'BAD_NAME_THING = ENVO:soil', User("test@foo.bar"))
        self.assertEqual(obs_res, {})
        self.assertEqual(obs_meta, ["bad_name_thing"])

    def test_call_no_results(self):
        """makes sure a call on a required sample ID column that has no results
        actually returns no results"""
        obs_res, obs_meta = self.search('sample_type = unicorns_and_rainbows',
                                        User('test@foo.bar'))
        self.assertEqual(obs_res, {})
        self.assertEqual(obs_meta, ['sample_type'])


if __name__ == "__main__":
    main()
