# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import TestCase, main

from qiita_core.util import qiita_test_checker
from qiita_pet.handlers.artifact_handlers.process_handlers import (
    process_artifact_handler_get_req)


@qiita_test_checker()
class TestProcessHandlersUtils(TestCase):
    def test_process_artifact_handler_get_req(self):
        obs = process_artifact_handler_get_req(1)
        exp = {}
        self.assertEqual(obs, exp)


if __name__ == '__main__':
    main()
