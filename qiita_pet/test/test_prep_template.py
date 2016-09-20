# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import main
from os.path import join, exists
from os import remove
from json import loads

from qiita_pet.test.tornado_test_base import TestHandlerBase
from qiita_db.util import get_count, get_mountpoint
from qiita_db.metadata_template.prep_template import PrepTemplate


class TestPrepTemplateHandler(TestHandlerBase):

    def setUp(self):
        super(TestPrepTemplateHandler, self).setUp()
        uploads_dp = get_mountpoint('uploads')[0][1]
        self.new_prep = join(uploads_dp, '1', 'new_template.txt')
        with open(self.new_prep, 'w') as f:
            f.write("sample_name\tnew_col\nSKD6.640190\tnew_value\n")

        self.broken_prep = join(uploads_dp, '1', 'broke_template.txt')
        with open(self.broken_prep, 'w') as f:
            f.write("sample_name\tbroke \col\nSKD6.640190\tnew_value\n")

    def tearDown(self):
        super(TestPrepTemplateHandler, self).tearDown()
        if exists(self.new_prep):
            remove(self.new_prep)
        if exists(self.broken_prep):
            remove(self.broken_prep)

    def test_post(self):
        new_prep_id = get_count('qiita.prep_template') + 1
        arguments = {'study_id': '1',
                     'data-type': '16S',
                     'prep-file': 'new_template.txt'}
        response = self.post('/prep_template/', arguments)
        self.assertEqual(response.code, 200)
        # Check that the new prep template has been created
        self.assertTrue(PrepTemplate.exists(new_prep_id))

    def test_post_broken_header(self):
        arguments = {'study_id': '1',
                     'data-type': '16S',
                     'prep-file': 'broke_template.txt'}
        response = self.post('/prep_template/', arguments)
        self.assertEqual(response.code, 200)
        self.assertIn('broke \\\\col', response.body)

    def test_patch(self):
        arguments = {'op': 'replace',
                     'path': '/1/investigation_type/',
                     'value': 'Cancer Genomics'}
        response = self.patch('/prep_template/', data=arguments)
        self.assertEqual(response.code, 200)
        exp = {'status': 'success', 'message': ''}
        self.assertEqual(loads(response.body), exp)

    def test_delete(self):
        # Create a new prep template so we can delete it
        response = self.delete('/prep_template/', data={'prep-template-id': 1})
        self.assertEqual(response.code, 200)
        exp = {
            "status": "error",
            "message": "Couldn't remove prep template: Cannot remove prep "
                       "template 1 because it has an artifact associated "
                       "with it"}
        self.assertEqual(loads(response.body), exp)

if __name__ == '__main__':
    main()
