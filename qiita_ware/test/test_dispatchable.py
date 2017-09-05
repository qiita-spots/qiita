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
from os.path import exists, join, dirname, abspath

from qiita_core.util import qiita_test_checker
from qiita_ware.dispatchable import (
    create_sample_template, delete_artifact)
from qiita_db.study import Study
from qiita_db.artifact import Artifact
from qiita_db.exceptions import QiitaDBUnknownIDError


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

    def test_delete_artifact(self):
        obs = delete_artifact(1)
        exp = {'status': 'danger',
               'message': 'Cannot delete artifact 1: it has children: 2, 3'}
        self.assertEqual(obs, exp)

        obs = delete_artifact(3)
        exp = {'status': 'success',
               'message': ''}
        self.assertEqual(obs, exp)

        with self.assertRaises(QiitaDBUnknownIDError):
            Artifact(3)

    def test_create_sample_template(self):
        obs = create_sample_template(self.fp, Study(1), False)
        exp = {'status': 'danger',
               'message': "The 'SampleTemplate' object with attributes "
                          "(id: 1) already exists."}
        self.assertEqual(obs, exp)

    def test_create_sample_template_nonutf8(self):
        fp = join(dirname(abspath(__file__)), 'test_data',
                  'sample_info_utf8_error.txt')
        obs = create_sample_template(fp, Study(1), False)
        exp = {'status': 'danger',
               'message': 'There are invalid (non UTF-8) characters in your '
                          'information file. The offending fields and their '
                          'location (row, column) are listed below, invalid '
                          'characters are represented using &#128062;: '
                          '"&#128062;collection_timestamp" = (0, 13)'}
        self.assertEqual(obs, exp)

if __name__ == '__main__':
    main()
