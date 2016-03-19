# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from unittest import main
from json import loads

from qiita_pet.test.tornado_test_base import TestHandlerBase


class TestNewPrepTemplateAjax(TestHandlerBase):
    def test_get(self):
        response = self.get('/study/new_prep_template/', {'study_id': '1'})
        self.assertEqual(response.code, 200)


class TestPrepTemplateGraphAJAX(TestHandlerBase):
    def test_get(self):
        response = self.get('/prep/graph/', {'prep_id': 1})
        self.assertEqual(response.code, 200)
        exp = {"status": "success",
               "node_labels": [[1, "Raw data 1 - FASTQ"],
                               [3, "Demultiplexed 2 - Demultiplexed"],
                               [2, "Demultiplexed 1 - Demultiplexed"],
                               [4, "BIOM - BIOM"],
                               [4, "BIOM - BIOM"]],
               "message": "",
               "edge_list": [[1, 3], [1, 2], [2, 4], [2, 5]]}
        self.assertItemsEqual(loads(response.body), exp)


class TestPrepTemplateAJAXReadOnly(TestHandlerBase):
    def test_get(self):
        response = self.get('/study/description/prep_template/',
                            {'prep_id': 1, 'study_id': 1})
        self.assertEqual(response.code, 200)
        self.assertNotEqual(response.body, '')


class TestPrepFilesHandler(TestHandlerBase):
    def test_get_files_not_allowed(self):
        response = self.post(
            '/study/prep_files/',
            {'type': 'BIOM', 'prep_file': 'uploaded_file.txt', 'study_id': 1})
        self.assertEqual(response.code, 405)

if __name__ == "__main__":
    main()
