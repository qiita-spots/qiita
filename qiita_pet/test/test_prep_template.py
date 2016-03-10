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

from qiita_pet.test.tornado_test_base import TestHandlerBase
from qiita_db.util import get_count, get_mountpoint
from qiita_db.metadata_template.prep_template import PrepTemplate


class TestPrepTemplateHandler(TestHandlerBase):
    database = True

    def setUp(self):
        super(TestPrepTemplateHandler, self).setUp()
        uploads_dp = get_mountpoint('uploads')[0][1]
        self.new_prep = join(uploads_dp, '1', 'new_template.txt')
        with open(self.new_prep, 'w') as f:
            f.write("sample_name\tnew_col\nSKD6.640190\tnew_value\n")

    def tearDown(self):
        super(TestPrepTemplateHandler, self).tearDown()
        if exists(self.new_prep):
            remove(self.new_prep)

    def test_post(self):
        new_prep_id = get_count('qiita.prep_template') + 1
        arguments = {'study_id': '1',
                     'data-type': '16S',
                     'prep-file': 'new_template.txt'}
        response = self.post('/prep_template/', arguments)
        self.assertEqual(response.code, 200)
        # Check that the new prep template has been created
        self.assertTrue(PrepTemplate.exists(new_prep_id))

if __name__ == '__main__':
    main()
