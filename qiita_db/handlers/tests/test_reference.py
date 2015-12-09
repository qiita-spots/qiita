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

from qiita_core.util import qiita_test_checker
from qiita_pet.test.tornado_test_base import TestHandlerBase
import qiita_db as qdb
from qiita_db.handlers.reference import _get_reference


@qiita_test_checker()
class UtilTests(TestCase):
    def test_get_reference(self):
        obs = _get_reference(-1)
        exp = (None, False, 'Reference does not exist')
        self.assertEqual(obs, exp)

        obs = _get_reference(1)
        exp = (qdb.reference.Reference(1), True, '')
        self.assertEqual(obs, exp)


@qiita_test_checker()
class ReferenceFilepathsHandler(TestHandlerBase):
    def test_get_reference_does_not_exist(self):
        obs = self.get('/qiita_db/references/100/filepaths/')
        self.assertEqual(obs.code, 200)
        exp = {'success': False, 'error': 'Reference does not exist',
               'filepaths': None}
        self.assertEqual(loads(obs.body), exp)

    def test_get(self):
        obs = self.get('/qiita_db/references/1/filepaths/')
        self.assertEqual(obs.code, 200)
        db_test_raw_dir = qdb.util.get_mountpoint('reference')[0][1]
        path_builder = partial(join, db_test_raw_dir)
        exp_fps = [
            [path_builder("GreenGenes_13_8_97_otus.fasta"), "reference_seqs"],
            [path_builder("GreenGenes_13_8_97_otu_taxonomy.txt"),
             "reference_tax"],
            [path_builder("GreenGenes_13_8_97_otus.tree"), "reference_tree"]]
        exp = {'success': True, 'error': '',
               'filepaths': exp_fps}
        self.assertEqual(loads(obs.body), exp)

if __name__ == '__main__':
    main()
