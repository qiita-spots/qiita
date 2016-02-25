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
from qiita_db.ontology import Ontology


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


class TestPrepTemplateAJAX(TestHandlerBase):
    database = True

    def test_get(self):
        response = self.get('/study/description/prep_template/',
                            {'prep_id': 1, 'study_id': 1})
        self.assertEqual(response.code, 200)
        self.assertIn('This analysis was done as in Caporaso', response.body)

    def test_post_update(self):
        response = self.post('/study/description/prep_template/',
                             {'prep_id': 1, 'action': 'update',
                              'filepath': 'uploaded_file.txt'})
        exp = {'status': 'error',
               'message': 'Empty file passed!',
               'file': 'uploaded_file.txt'}
        self.assertEqual(response.code, 200)
        self.assertEqual(loads(response.body), exp)

    def test_post_ontology(self):
        response = self.post('/study/description/prep_template/',
                             {'prep_id': 1, 'action': 'ontology',
                              'ena': 'Other', 'ena_user': 'New Type',
                              'ena_new': 'NEW THING'})
        exp = {'status': 'success', 'message': '', 'file': None}
        self.assertEqual(response.code, 200)
        self.assertEqual(loads(response.body), exp)
        # Make sure New Type added
        ontology = Ontology(999999999)
        self.assertIn('NEW THING', ontology.user_defined_terms)

    def test_post_delete(self):
        response = self.post('/study/description/prep_template/',
                             {'prep_id': 1,
                              'action': 'delete'})
        self.assertEqual(response.code, 200)

        # checking that the action was sent
        self.assertIn("Couldn't remove prep template:", response.body)


class TestPrepFilesHandler(TestHandlerBase):
    # TODO: missing tests
    pass

if __name__ == "__main__":
    main()
