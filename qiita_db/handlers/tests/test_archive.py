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
from json import loads

from qiita_db.handlers.tests.oauthbase import OauthTestingBase
from qiita_db.sql_connection import TRN


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

    def test_post(self):
        # let's archive different values from different jobs
        with TRN:
            # 3 - close reference picking
            # 3 - success
            sql = """SELECT processing_job_id
                     FROM qiita.processing_job
                     WHERE command_id = 3 AND processing_job_status_id = 3"""
            TRN.add(sql)
            jobs = TRN.execute_fetchflatten()

            for j in jobs:
                special_feature = 'AA - %s' % j
                data = {'job_id': j, 'features': [special_feature, 'CA']}
                obs = self.post(
                    '/qiita_db/archive/observations/', headers=self.header,
                    data=data)
                exp = {}
                self.assertEqual(obs.code, 200)
                self.assertEqual(loads(obs.body), exp)


if __name__ == '__main__':
    main()
