from moi import r_client
from qiita_pet.test.tornado_test_base import TestHandlerBase


class OauthTestingBase(TestHandlerBase):
    def setUp(self):
        self.token = 'TESTINGOAUTHSTUFF'
        self.header = {'Authorization': 'Bearer ' + self.token}
        r_client.hset(self.token, 'timestamp', '12/12/12 12:12:00')
        r_client.hset(self.token, 'grant_type', 'client')
        r_client.expire(self.token, 2)
        super(OauthTestingBase, self).setUp()
