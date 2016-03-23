# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from unittest import TestCase, main

from qiita_pet.handlers.api_proxy.processing import (
    process_artifact_handler_get_req, list_commands_handler_get_req,
    list_options_handler_get_req)


class TestProcessingAPIReadOnly(TestCase):
    def test_process_artifact_handler_get_req(self):
        obs = process_artifact_handler_get_req(1)
        exp = {'status': 'success',
               'message': '',
               'name': 'Raw data 1',
               'type': 'FASTQ'}
        self.assertEqual(obs, exp)

        obs = process_artifact_handler_get_req(2)
        exp = {'status': 'success',
               'message': '',
               'name': 'Demultiplexed 1',
               'type': 'Demultiplexed'}
        self.assertEqual(obs, exp)

    def test_list_commands_handler_get_req(self):
        obs = list_commands_handler_get_req('FASTQ')
        exp = {'status': 'success',
               'message': '',
               'commands': [{'id': 1, 'command': 'Split libraries FASTQ',
                             'output': [['demultiplexed', 'Demultiplexed']]}]}
        self.assertEqual(obs, exp)

        obs = list_commands_handler_get_req('Demultiplexed')
        exp = {'status': 'success',
               'message': '',
               'commands': [{'id': 3, 'command': 'Pick closed-reference OTUs',
                             'output': [['OTU table', 'BIOM']]}]}
        self.assertEqual(obs, exp)

    def test_list_options_handler_get_req(self):
        obs = list_options_handler_get_req(3)
        exp = {'status': 'success',
               'message': '',
               'options': [10, 'Defaults', {'reference': 1,
                                            'similarity': 0.97,
                                            'sortmerna_coverage': 0.97,
                                            'sortmerna_e_value': 1,
                                            'sortmerna_max_pos': 10000,
                                            'threads': 1}]}
        self.assertItemsEqual(obs, exp)


if __name__ == '__main__':
    main()
