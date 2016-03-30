# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import TestCase, main
from tempfile import mkstemp
from os import close, remove
from os.path import exists

from qiita_core.util import qiita_test_checker
from qiita_ware.dispatchable import (
    create_sample_template, update_sample_template, delete_sample_template,
    update_prep_template)
from qiita_db.study import Study


@qiita_test_checker()
class TestDispatchable(TestCase):
    def setUp(self):
        fd, self.fp = mkstemp(suffix=".txt")
        close(fd)
        with open(self.fp, 'w') as f:
            f.write("sample_name\tnew_col\n"
                    "1.SKD6.640190\tnew_vale")

        self._clean_up_files = [self.fp]

    def tearDown(self):
        for fp in self._clean_up_files:
            if exists(fp):
                remove(fp)

    def test_create_sample_template(self):
        obs = create_sample_template(self.fp, Study(1), False)
        exp = {'status': 'danger',
               'message': "The 'SampleTemplate' object with attributes "
                          "(id: 1) already exists."}
        self.assertEqual(obs, exp)

    def test_update_sample_template(self):
        obs = update_sample_template(1, self.fp)
        exp = {'status': 'warning',
               'message': 'Sample names were already prefixed with the study '
                          'id.\nThe following columns have been added to the '
                          'existing template: new_col\nThere are no '
                          'differences between the data stored in the DB and '
                          'the new data provided'}
        self.assertEqual(obs['status'], exp['status'])
        self.assertItemsEqual(obs['message'].split('\n'),
                              exp['message'].split('\n'))

    def test_delete_sample_template(self):
        obs = delete_sample_template(1)
        exp = {'status': 'danger',
               'message': 'Sample template cannot be erased because there '
                          'are prep templates associated.'}
        self.assertEqual(obs, exp)

    def test_update_prep_template(self):
        obs = update_prep_template(1, self.fp)
        exp = {'status': 'warning',
               'message': 'Sample names were already prefixed with the study '
                          'id.\nThe following columns have been added to the '
                          'existing template: new_col\nThere are no '
                          'differences between the data stored in the DB and '
                          'the new data provided'}
        self.assertEqual(obs['status'], exp['status'])
        self.assertItemsEqual(obs['message'].split('\n'),
                              exp['message'].split('\n'))

if __name__ == '__main__':
    main()
