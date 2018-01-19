# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from os.path import exists, isfile
from os import remove
from shutil import rmtree

from unittest import main
from json import loads, dumps

from qiita_db.handlers.tests.oauthbase import OauthTestingBase
from qiita_db.sql_connection import TRN
from qiita_db.archive import Archive


class APIArchiveObservationsTests(OauthTestingBase):
    def setUp(self):
        super(APIArchiveObservationsTests, self).setUp()

        self._clean_up_files = []

    def tearDown(self):
        super(APIArchiveObservationsTests, self).tearDown()
        for fp in self._clean_up_files:
            if exists(fp):
                if isfile(fp):
                    remove(fp)
                else:
                    rmtree(fp)

    def test_full_query_and_insertion(self):
        # let's archive different values from different jobs
        with TRN:
            # 3 - close reference picking
            # 3 - success
            sql = """SELECT processing_job_id
                     FROM qiita.processing_job
                     WHERE command_id = 3 AND processing_job_status_id = 3"""
            TRN.add(sql)
            jobs = TRN.execute_fetchflatten()

            exp_all_features = {}
            for j in jobs:
                featureA = 'AA - %s' % j
                featureB = 'BB - %s' % j

                # testing that nothing is there
                data = {'job_id': j, 'features': [featureA, featureB]}
                obs = self.post(
                    '/qiita_db/archive/observations/', headers=self.header,
                    data=data)
                exp = {}
                self.assertEqual(obs.code, 200)
                self.assertEqual(loads(obs.body), exp)

                # inserting and testing insertion
                data = {'job_id': j,
                        'features': dumps({featureA: 'CA', featureB: 'CB'})}
                obs = self.patch(
                    '/qiita_db/archive/observations/', headers=self.header,
                    data=data)
                exp = {featureA: 'CA', featureB: 'CB'}
                self.assertEqual(obs.code, 200)
                self.assertEqual(loads(obs.body), exp)

                exp_all_features[featureA] = 'CA'
                exp_all_features[featureB] = 'CB'

            # testing retrieve all featues
            obs = Archive.retrieve_feature_values()
            self.assertEqual(obs, exp_all_features)


if __name__ == '__main__':
    main()
