from mock import Mock
try:
    from urllib import urlencode
except ImportError:  # py3
    from urllib.parse import urlencode

from tornado.testing import AsyncHTTPTestCase
from qiita_pet.webserver import Application
from qiita_pet.handlers.base_handlers import BaseHandler
from qiita_db.environment_manager import clean_test_environment
from qiita_db.user import User


class TestHandlerBase(AsyncHTTPTestCase):
    database = False
    app = Application()

    def get_app(self):
        BaseHandler.get_current_user = Mock(return_value=User("test@foo.bar"))
        self.app.settings['debug'] = False
        return self.app

    def tearDown(self):
        if self.database:
            clean_test_environment()
        super(TestHandlerBase, self).tearDown()

    # helpers from http://www.peterbe.com/plog/tricks-asynchttpclient-tornado
    def get(self, url, data=None, headers=None, doseq=True):
        if data is not None:
            if isinstance(data, dict):
                data = urlencode(data, doseq=doseq)
            if '?' in url:
                url += '&%s' % data
            else:
                url += '?%s' % data
        return self._fetch(url, 'GET', headers=headers)

    def post(self, url, data, headers=None, doseq=True):
        if data is not None:
            if isinstance(data, dict):
                data = urlencode(data, doseq=doseq)
        return self._fetch(url, 'POST', data, headers)

    def patch(self, url, data, headers=None, doseq=True):
        if isinstance(data, dict):
            data = urlencode(data, doseq=doseq)
        if '?' in url:
            url += '&%s' % data
        else:
            url += '?%s' % data
        return self._fetch(url, 'PATCH', data=data, headers=headers)

    def delete(self, url, data=None, headers=None, doseq=True):
        if data is not None:
            if isinstance(data, dict):
                data = urlencode(data, doseq=doseq)
            if '?' in url:
                url += '&%s' % data
            else:
                url += '?%s' % data
        return self._fetch(url, 'DELETE', headers=headers)

    def _fetch(self, url, method, data=None, headers=None):
        self.http_client.fetch(self.get_url(url), self.stop, method=method,
                               body=data, headers=headers)
        return self.wait(timeout=10)
