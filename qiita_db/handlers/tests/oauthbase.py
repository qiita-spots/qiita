# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

import requests
import os
import sys
from qiita_core.qiita_settings import r_client, qiita_config

from qiita_pet.test.tornado_test_base import TestHandlerBase


class OauthTestingBase(TestHandlerBase):
    def setUp(self):
        self.token = 'TESTINGOAUTHSTUFF'
        self.header = {'Authorization': 'Bearer ' + self.token}
        r_client.hset(self.token, 'timestamp', '12/12/12 12:12:00')
        r_client.hset(self.token, 'grant_type', 'client')
        r_client.expire(self.token, 20)
        super(OauthTestingBase, self).setUp()
        self._session = requests.Session()
        # should point to client certificat file:
        # /qiita/qiita_core/support_files/ci_rootca.crt
        self._verify = os.environ['QIITA_ROOTCA_CERT']
        self._fetch_token()

        self._files_to_remove = []

    def tearDown(self):
        for fp in self._files_to_remove:
            if os.path.exists(fp):
                os.remove(fp)

    def _fetch_token(self):
        data = {
            'client_id': '4MOBzUBHBtUmwhaC258H7PS0rBBLyGQrVxGPgc9g305bvVhf6h',
            'client_secret':
            ('rFb7jwAb3UmSUN57Bjlsi4DTl2owLwRpwCc0SggRN'
             'EVb2Ebae2p5Umnq20rNMhmqN'),
            'grant_type': 'client'}
        resp = self._session.post(
            "%s/qiita_db/authenticate/" % qiita_config.base_url,
            verify=self._verify, data=data, timeout=80)
        if resp.status_code != 200:
            raise ValueError("_fetchToken() POST request failed")
        self._token = resp.json()['access_token']
        print('obtained access_token = %s' % self._token, file=sys.stderr)

    def post_authed(self, url, **kwargs):
        if 'headers' not in kwargs:
            kwargs['headers'] = {}
        if 'Authorization' not in kwargs['headers']:
            kwargs['headers']['Authorization'] = 'Bearer %s' % self._token

        r = self._session.post(
            qiita_config.base_url + url, verify=self._verify, **kwargs)
        r.close()

        return r

    def get_authed(self, url):
        r = self._session.get(qiita_config.base_url + url, verify=self._verify,
                              headers={'Authorization': 'Bearer %s' %
                                       self._token})
        r.close()
        return r
