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
from qiita_db.handlers.artifact import _get_artifact


@qiita_test_checker()
class UtilTests(TestCase):
    def test_get_artifact(self):
        obs = _get_artifact(-1)
        exp = (None, False, 'Artifact does not exist')
        self.assertEqual(obs, exp)


class ArtifactFilepathsHandlerTests(TestHandlerBase):
    def test_get_artifact_does_not_exist(self):
        obs = self.get('/qiita_db/artifacts/100/filepaths/')
        self.assertEqual(obs.code, 200)
        exp = {'success': False, 'error': 'Artifact does not exist',
               'filepaths': None}
        self.assertEqual(loads(obs.body), exp)

    def test_get_artifact(self):
        obs = self.get('/qiita_db/artifacts/1/filepaths/')
        self.assertEqual(obs.code, 200)
        db_test_raw_dir = qdb.util.get_mountpoint('raw_data')[0][1]
        path_builder = partial(join, db_test_raw_dir)
        exp_fps = [
            [path_builder('1_s_G1_L001_sequences.fastq.gz'),
             "raw_forward_seqs"],
            [path_builder('1_s_G1_L001_sequences_barcodes.fastq.gz'),
             "raw_barcodes"]]
        exp = {'success': True, 'error': '',
               'filepaths': exp_fps}
        self.assertEqual(loads(obs.body), exp)


class ArtifactMappingHandlerTests(TestHandlerBase):
    def test_get_artifact_does_not_exist(self):
        obs = self.get('/qiita_db/artifacts/100/mapping/')
        self.assertEqual(obs.code, 200)
        exp = {'success': False, 'error': 'Artifact does not exist',
               'mapping': None}
        self.assertEqual(loads(obs.body), exp)

    def test_get(self):
        obs = self.get('/qiita_db/artifacts/1/mapping/')
        self.assertEqual(obs.code, 200)
        db_dir = qdb.util.get_mountpoint('templates')[0][1]
        exp_fp = join(db_dir, "1_prep_1_qiime_19700101-000000.txt")
        exp = {'success': True, 'error': '',
               'mapping': exp_fp}
        self.assertEqual(loads(obs.body), exp)


class ArtifactTypeHandlerTests(TestHandlerBase):
    def test_get_artifact_does_not_exist(self):
        obs = self.get('/qiita_db/artifacts/100/type/')
        self.assertEqual(obs.code, 200)
        exp = {'success': False, 'error': 'Artifact does not exist',
               'type': None}
        self.assertEqual(loads(obs.body), exp)

    def test_get(self):
        obs = self.get('/qiita_db/artifacts/1/type/')
        self.assertEqual(obs.code, 200)
        exp = {'success': True, 'error': '',
               'type': "FASTQ"}
        self.assertEqual(loads(obs.body), exp)


if __name__ == '__main__':
    main()
