# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from qiita_core.qiita_settings import r_client

from qiita_pet.test.tornado_test_base import TestHandlerBase


class RESTHandlerTestCase(TestHandlerBase):
    def setUp(self):
        self.client_token = 'SOMEAUTHTESTINGTOKENHERE2122'
        r_client.hset(self.client_token, 'timestamp', '12/12/12 12:12:00')
        r_client.hset(self.client_token, 'client_id', 'test123123123')
        r_client.hset(self.client_token, 'grant_type', 'client')
        r_client.expire(self.client_token, 5)

        self.headers = {'Authorization': 'Bearer ' + self.client_token}
        super(RESTHandlerTestCase, self).setUp()
