# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import main

from qiita_pet.test.tornado_test_base import TestHandlerWebSocketBase
from json import dumps, loads

from tornado.testing import gen_test
from tornado.gen import coroutine, Return


# adapted from: https://gist.github.com/crodjer/1e9989ab30fdc32db926
class TestSelectedSocketHandler(TestHandlerWebSocketBase):

    @coroutine
    def _mk_client(self):
        c = yield self._mk_connection()

        # Discard the hello
        # This could be any initial handshake, which needs to be generalized
        # for most of the tests.
        yield c.read_message()

        raise Return(c)

    @gen_test
    def test_socket(self):
        # A client with the hello taken care of.
        c = yield self._mk_client()

        msg = {'remove_sample': {'proc_data': 2, 'samples': ['A', 'B']}}
        c.write_message(dumps(msg))
        response = yield c.read_message()
        self.assertEqual(loads(response), msg)

        msg = {'remove_pd': {'proc_data': 2}}
        c.write_message(dumps(msg))
        response = yield c.read_message()
        self.assertEqual(loads(response), msg)

        msg = {'clear': {'pids': [2]}}
        c.write_message(dumps(msg))
        response = yield c.read_message()
        self.assertEqual(loads(response), msg)

        msg = {'clear': {'pids': [2, 3, 4]}}
        c.write_message(dumps(msg))
        response = yield c.read_message()
        self.assertEqual(loads(response), msg)


if __name__ == "__main__":
    main()
