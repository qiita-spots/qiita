from mock import Mock
try:
    from urllib import urlencode
except ImportError:  # py3
    from urllib.parse import urlencode

from tornado.testing import AsyncHTTPTestCase
from qiita_core.qiita_settings import qiita_config
from qiita_pet.webserver import Application
from qiita_pet.handlers.base_handlers import BaseHandler
from qiita_db.sql_connection import SQLConnectionHandler
from qiita_db.environment_manager import drop_and_rebuild_tst_database
from qiita_db.user import User


class TestHandlerBase(AsyncHTTPTestCase):
    database = False
    conn_handler = SQLConnectionHandler()
    app = Application()

    def get_app(self):
        BaseHandler.get_current_user = Mock(return_value=User("test@foo.bar"))
        self.app.settings['debug'] = False
        return self.app

    def setUp(self):
        if self.database:
            # First, we check that we are not in a production environment
            # It is possible that we are connecting to a production database
            test_db = self.conn_handler.execute_fetchone(
                "SELECT test FROM settings")[0]
            # Or the loaded config file belongs to a production environment
            if not qiita_config.test_environment or not test_db:
                raise RuntimeError("Working in a production environment. Not "
                                   "executing the tests to keep the production"
                                   " database safe.")

            # Drop the schema and rebuild the test database
            drop_and_rebuild_tst_database(self.conn_handler)

        super(TestHandlerBase, self).setUp()

    # helpers from http://www.peterbe.com/plog/tricks-asynchttpclient-tornado
    def get(self, url, data=None, headers=None, doseq=True):
        if data is not None:
            if isinstance(data, dict):
                data = urlencode(data, doseq=doseq)
            if '?' in url:
                url += '&amp;%s' % data
            else:
                url += '?%s' % data
        return self._fetch(url, 'GET', headers=headers)

    def post(self, url, data, headers=None, doseq=True):
        if data is not None:
            if isinstance(data, dict):
                data = urlencode(data, doseq=doseq)
        return self._fetch(url, 'POST', data, headers)

    def _fetch(self, url, method, data=None, headers=None):
        self.http_client.fetch(self.get_url(url), self.stop, method=method,
                               body=data, headers=headers)
        return self.wait(timeout=10)
