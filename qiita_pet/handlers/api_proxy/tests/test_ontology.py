# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from unittest import TestCase, main

from qiita_core.util import qiita_test_checker
from qiita_pet.handlers.api_proxy.ontology import ontology_patch_handler


@qiita_test_checker()
class TestOntology(TestCase):
    def test_ontology_patch_handler(self):
        obs = ontology_patch_handler('add', '/ENA/', 'TERM')
        exp = {'status': 'success', 'message': ''}
        self.assertEqual(obs, exp)

    def test_ontology_patch_handler_errors(self):
        # Operation not supported
        obs = ontology_patch_handler('replace', '/ENA/', 'TERM')
        exp = {'status': 'error',
               'message': 'Operation "replace" not supported. '
                          'Current supported operations: add'}
        self.assertEqual(obs, exp)
        # Incorrect path parameter
        obs = ontology_patch_handler('add', '/ENA/Metagenomics', 'TERM')
        exp = {'status': 'error', 'message': 'Incorrect path parameter'}
        self.assertEqual(obs, exp)
        # Ontology does not exist
        obs = ontology_patch_handler('add', '/ONTOLOGY/', 'TERM')
        exp = {'status': 'error',
               'message': 'Ontology "ONTOLOGY" does not exist'}
        self.assertEqual(obs, exp)


if __name__ == '__main__':
    main()
