# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import TestCase, main

from qiita_db.user import User
from qiita_core.util import qiita_test_checker
from qiita_db.search import QiitaStudySearch


@qiita_test_checker()
class SearchTest(TestCase):
    """Tests that the search object works as expected"""

    def setUp(self):
        self.search = QiitaStudySearch()

    def test_call(self):
        obs_res, obs_meta = self.search(
            '(sample_type = ENVO:soil AND COMMON_NAME = "rhizosphere '
            'metagenome" ) AND NOT Description_duplicate includes Burmese',
            User("test@foo.bar"))
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
            'BAD_NAME_THING = ENVO:soil', User("test@foo.bar"))
        self.assertEqual(obs_res, {})
        self.assertEqual(obs_meta, ["BAD_NAME_THING"])

    def test_call_no_results(self):
        """makes sure a call on a required sample ID column that has no results
        actually returns no results"""
        obs_res, obs_meta = self.search('sample_type = unicorns_and_rainbows',
                                        User('test@foo.bar'))
        self.assertEqual(obs_res, {})
        self.assertEqual(obs_meta, ['sample_type'])


if __name__ == "__main__":
    main()
