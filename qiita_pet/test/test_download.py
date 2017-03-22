# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import main
from mock import Mock
from os.path import exists, isdir, join
from os import remove, makedirs
from shutil import rmtree
from tempfile import mkdtemp

from biom.util import biom_open
from biom import example_table as et

from qiita_pet.test.tornado_test_base import TestHandlerBase
from qiita_pet.handlers.base_handlers import BaseHandler
from qiita_db.user import User
from qiita_db.artifact import Artifact
from qiita_db.software import Parameters, Command


class TestDownloadHandler(TestHandlerBase):

    def setUp(self):
        super(TestDownloadHandler, self).setUp()

    def tearDown(self):
        super(TestDownloadHandler, self).tearDown()

    def test_download(self):
        # check success
        response = self.get('/download/1')
        self.assertEqual(response.code, 200)
        self.assertEqual(response.body, (
            "This installation of Qiita was not equipped with nginx, so it "
            "is incapable of serving files. The file you attempted to "
            "download is located at raw_data/1_s_G1_L001_sequences.fastq.gz"))

        # failure
        response = self.get('/download/1000')
        self.assertEqual(response.code, 404)


class TestDownloadStudyBIOMSHandler(TestHandlerBase):

    def setUp(self):
        super(TestDownloadStudyBIOMSHandler, self).setUp()
        self._clean_up_files = []

    def tearDown(self):
        super(TestDownloadStudyBIOMSHandler, self).tearDown()
        for fp in self._clean_up_files:
            if exists(fp):
                if isdir(fp):
                    rmtree(fp)
                else:
                    remove(fp)

    def test_download_study(self):
        tmp_dir = mkdtemp()
        self._clean_up_files.append(tmp_dir)

        biom_fp = join(tmp_dir, 'otu_table.biom')
        smr_dir = join(tmp_dir, 'sortmerna_picked_otus')
        log_dir = join(smr_dir, 'seqs_otus.log')

        with biom_open(biom_fp, 'w') as f:
            et.to_hdf5(f, "test")
        makedirs(smr_dir)
        with open(log_dir, 'w') as f:
            f.write('\n')

        self._clean_up_files.append(tmp_dir)

        files_biom = [(biom_fp, 'biom'), (smr_dir, 'directory')]

        params = Parameters.from_default_params(
            Command(3).default_parameter_sets.next(), {'input_data': 1})
        a = Artifact.create(files_biom, "BIOM", parents=[Artifact(2)],
                            processing_parameters=params)
        for _, fp, _ in a.filepaths:
            self._clean_up_files.append(fp)

        response = self.get('/download_study_bioms/1')
        self.assertEqual(response.code, 200)
        exp = (
            '[0-9]* 1256812 /protected/processed_data/1_study_1001_closed_'
            'reference_otu_table.biom processed_data/1_study_1001_closed_'
            'reference_otu_table.biom\n'
            '[0-9]* 36615 /protected/templates/1_prep_1_qiime_[0-9]*-'
            '[0-9]*.txt mapping_files/4_mapping_file.txt\n'
            '[0-9]* 1256812 /protected/processed_data/'
            '1_study_1001_closed_reference_otu_table.biom processed_data/'
            '1_study_1001_closed_reference_otu_table.biom\n'
            '[0-9]* 36615 /protected/templates/1_prep_1_qiime_[0-9]*-'
            '[0-9]*.txt mapping_files/5_mapping_file.txt\n'
            '[0-9]* 1256812 /protected/processed_data/'
            '1_study_1001_closed_reference_otu_table_Silva.biom processed_data'
            '/1_study_1001_closed_reference_otu_table_Silva.biom\n'
            '[0-9]* 36615 /protected/templates/1_prep_1_qiime_[0-9]*-'
            '[0-9]*.txt mapping_files/6_mapping_file.txt\n'
            '[0-9]* 36615 /protected/templates/1_prep_2_qiime_[0-9]*-'
            '[0-9]*.txt mapping_files/7_mapping_file.txt\n'
            '[0-9]* 39752 /protected/BIOM/{0}/otu_table.biom '
            'BIOM/{0}/otu_table.biom\n'
            '[0-9]* 1 /protected/BIOM/{0}/sortmerna_picked_otus/seqs_otus.log '
            'BIOM/{0}/sortmerna_picked_otus/seqs_otus.log\n'
            '[0-9]* 36615 /protected/templates/1_prep_1_qiime_[0-9]*-[0-9]*.'
            'txt mapping_files/{0}_mapping_file.txt\n'.format(a.id))
        self.assertRegexpMatches(response.body, exp)

        response = self.get('/download_study_bioms/200')
        self.assertEqual(response.code, 405)

        # changing user so we can test the failures
        BaseHandler.get_current_user = Mock(
            return_value=User("demo@microbio.me"))
        response = self.get('/download_study_bioms/1')
        self.assertEqual(response.code, 405)


if __name__ == '__main__':
    main()
