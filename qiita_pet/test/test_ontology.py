# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from unittest import main

from qiita_pet.test.tornado_test_base import TestHandlerBase


class TestOntologyHandler(TestHandlerBase):
    def test_patch(self):
        # TODO: issue #1682
        # arguments = {'op': 'add', 'path': 'ENA', 'value': 'new-term'}
        # response = self.patch('/ontology/', data=arguments)
        # self.assertEqual(response.code, 200)
        # exp = {'status': 'success', 'message': ''}
        # self.assertEqual(loads(response.body), exp)
        pass

if __name__ == '__main__':
    main()
