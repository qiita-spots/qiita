# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from mock import Mock
try:
    from urllib import urlencode
except ImportError:  # py3
    from urllib.parse import urlencode

from tornado.testing import AsyncHTTPTestCase, bind_unused_port
from tornado.escape import json_encode
from tornado.websocket import websocket_connect
from qiita_pet.webserver import Application
from qiita_pet.handlers.base_handlers import BaseHandler
from qiita_db.environment_manager import clean_test_environment
from qiita_db.user import User
from qiita_core.qiita_settings import r_client


class TestHandlerBase(AsyncHTTPTestCase):
    database = False
    app = Application()

    def get_app(self):
        BaseHandler.get_current_user = Mock(return_value=User("test@foo.bar"))
        self.app.settings['debug'] = False
        return self.app

    @classmethod
    def tearDownClass(cls):
        clean_test_environment()
        r_client.flushdb()

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

    def post(self, url, data, headers=None, doseq=True, asjson=False):
        if data is not None:
            if asjson:
                data = json_encode(data)
            elif isinstance(data, dict):
                data = urlencode(data, doseq=doseq)
        return self._fetch(url, 'POST', data, headers)

    def patch(self, url, data, headers=None, doseq=True, asjson=False):
        if asjson:
            data = json_encode(data)
        else:
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
        return self.wait(timeout=15)


class TestHandlerWebSocketBase(TestHandlerBase):
    def setUp(self):
        super(TestHandlerWebSocketBase, self).setUp()
        socket, self.port = bind_unused_port()
        self.http_server.add_socket(socket)

    def _mk_connection(self):
        return websocket_connect(
            'ws://localhost:{}/analysis/selected/socket/'.format(self.port)
        )
