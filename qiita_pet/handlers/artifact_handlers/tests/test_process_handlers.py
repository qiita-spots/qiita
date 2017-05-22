# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import TestCase, main

from qiita_core.util import qiita_test_checker
from qiita_pet.test.tornado_test_base import TestHandlerBase
from qiita_pet.handlers.artifact_handlers.process_handlers import (
    process_artifact_handler_get_req)


@qiita_test_checker()
class TestProcessHandlersUtils(TestCase):
    def test_process_artifact_handler_get_req(self):
        obs = process_artifact_handler_get_req(1)
        exp = {'status': 'success',
               'message': '',
               'name': 'Raw data 1',
               'type': 'FASTQ',
               'artifact_id': 1,
               'allow_change_optionals': False}
        self.assertEqual(obs, exp)

        obs = process_artifact_handler_get_req(8)
        exp = {'status': 'success',
               'message': '',
               'name': 'noname',
               'type': 'BIOM',
               'artifact_id': 8,
               'allow_change_optionals': True}
        self.assertEqual(obs, exp)


class TestProcessHandlers(TestHandlerBase):
    def test_get_process_artifact_handler(self):
        response = self.get("/artifact/1/process/")
        self.assertEqual(response.code, 200)
        self.assertNotEqual(response.body, "")
        self.assertIn('load_artifact_type(params.nodes, false);',
                      response.body)

        response = self.get("/artifact/8/process/")
        self.assertEqual(response.code, 200)
        self.assertNotEqual(response.body, "")
        self.assertIn('load_artifact_type(params.nodes, true);', response.body)

if __name__ == '__main__':
    main()
