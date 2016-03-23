# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from unittest import TestCase, main

from qiita_pet.handlers.api_proxy.processing import (
    list_commands_handler_get_req)


class TestProcessingAPIReadOnly(TestCase):
    def test_list_commands_handler_get_req(self):
        obs = list_commands_handler_get_req(['FASTQ'])
        exp = {'status': 'success',
               'message': '',
               'commands': [{'id': 1, 'command': 'Split libraries FASTQ',
                             'output': [['demultiplexed', 'Demultiplexed']]}]}
        self.assertEqual(obs, exp)


if __name__ == '__main__':
    main()
