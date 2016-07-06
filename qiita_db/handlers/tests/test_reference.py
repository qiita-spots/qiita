# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import main, TestCase
from json import loads
from functools import partial
from os.path import join

from tornado.web import HTTPError

from qiita_db.handlers.tests.oauthbase import OauthTestingBase
import qiita_db as qdb
from qiita_db.handlers.reference import _get_reference


class UtilTests(TestCase):
    def test_get_reference(self):
        with self.assertRaises(HTTPError):
            _get_reference(100)

        obs = _get_reference(1)
        self.assertEqual(obs, qdb.reference.Reference(1))


class ReferenceHandler(OauthTestingBase):
    def test_get_reference_no_header(self):
        obs = self.get('/qiita_db/references/1/')
        self.assertEqual(obs.code, 400)

    def test_get_reference_does_not_exist(self):
        obs = self.get('/qiita_db/references/100/',
                       headers=self.header)
        self.assertEqual(obs.code, 404)

    def test_get(self):
        obs = self.get('/qiita_db/references/1/',
                       headers=self.header)
        self.assertEqual(obs.code, 200)
        db_test_raw_dir = qdb.util.get_mountpoint('reference')[0][1]
        path_builder = partial(join, db_test_raw_dir)
        fps = {
            'reference_seqs': path_builder("GreenGenes_13_8_97_otus.fasta"),
            'reference_tax': path_builder(
                "GreenGenes_13_8_97_otu_taxonomy.txt"),
            'reference_tree': path_builder("GreenGenes_13_8_97_otus.tree")}
        exp = {'name': 'Greengenes', 'version': '13_8', 'files': fps}
        self.assertEqual(loads(obs.body), exp)

if __name__ == '__main__':
    main()
