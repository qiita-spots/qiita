# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import main
from mock import Mock
from os.path import exists, isdir, join, basename
from os import remove, makedirs, close
from shutil import rmtree
from tempfile import mkdtemp, mkstemp

from biom.util import biom_open
from biom import example_table as et

from qiita_pet.test.tornado_test_base import TestHandlerBase
from qiita_pet.handlers.base_handlers import BaseHandler
from qiita_db.user import User
from qiita_db.study import Study
from qiita_db.artifact import Artifact
from qiita_db.software import Parameters, Command


class TestDownloadHandler(TestHandlerBase):

    def setUp(self):
        super(TestDownloadHandler, self).setUp()
        self._clean_up_files = []

    def tearDown(self):
        super(TestDownloadHandler, self).tearDown()
        for fp in self._clean_up_files:
            if exists(fp):
                if isdir(fp):
                    rmtree(fp)
                else:
                    remove(fp)

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
        self.assertEqual(response.code, 403)

        # directory
        a = Artifact(1)
        fd, fp = mkstemp(suffix='.html')
        close(fd)
        with open(fp, 'w') as f:
            f.write('\n')
        self._clean_up_files.append(fp)
        dirpath = mkdtemp()
        fd, fp2 = mkstemp(suffix='.txt', dir=dirpath)
        close(fd)
        with open(fp2, 'w') as f:
            f.write('\n')
        self._clean_up_files.append(dirpath)
        a.set_html_summary(fp, support_dir=dirpath)
        for fp_id, _, fp_type in a.filepaths:
            if fp_type == 'html_summary_dir':
                break
        response = self.get('/download/%d' % fp_id)
        self.assertEqual(response.code, 200)

        fp_name = basename(fp2)
        dirname = basename(dirpath)
        self.assertEqual(
            response.body, "- 1 /protected/FASTQ/1/%s/%s FASTQ/1/%s/%s\n"
                           % (dirname, fp_name, dirname, fp_name))


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
        tgz = join(tmp_dir, 'sortmerna_picked_otus.tgz')

        with biom_open(biom_fp, 'w') as f:
            et.to_hdf5(f, "test")
        makedirs(smr_dir)
        with open(log_dir, 'w') as f:
            f.write('\n')
        with open(tgz, 'w') as f:
            f.write('\n')

        files_biom = [(biom_fp, 'biom'), (smr_dir, 'directory'), (tgz, 'tgz')]

        params = Parameters.from_default_params(
            Command(3).default_parameter_sets.next(), {'input_data': 1})
        a = Artifact.create(files_biom, "BIOM", parents=[Artifact(2)],
                            processing_parameters=params)
        for _, fp, _ in a.filepaths:
            self._clean_up_files.append(fp)

        response = self.get('/download_study_bioms/1')
        self.assertEqual(response.code, 200)
        exp = (
            '- 1256812 /protected/processed_data/1_study_1001_closed_'
            'reference_otu_table.biom processed_data/1_study_1001_closed_'
            'reference_otu_table.biom\n'
            '- 36615 /protected/templates/1_prep_1_qiime_[0-9]*-'
            '[0-9]*.txt mapping_files/4_mapping_file.txt\n'
            '- 1256812 /protected/processed_data/'
            '1_study_1001_closed_reference_otu_table.biom processed_data/'
            '1_study_1001_closed_reference_otu_table.biom\n'
            '- 36615 /protected/templates/1_prep_1_qiime_[0-9]*-'
            '[0-9]*.txt mapping_files/5_mapping_file.txt\n'
            '- 1256812 /protected/processed_data/'
            '1_study_1001_closed_reference_otu_table_Silva.biom processed_data'
            '/1_study_1001_closed_reference_otu_table_Silva.biom\n'
            '- 36615 /protected/templates/1_prep_1_qiime_[0-9]*-'
            '[0-9]*.txt mapping_files/6_mapping_file.txt\n'
            '- 36615 /protected/templates/1_prep_2_qiime_[0-9]*-'
            '[0-9]*.txt mapping_files/7_mapping_file.txt\n'
            '- [0-9]* /protected/BIOM/{0}/otu_table.biom '
            'BIOM/{0}/otu_table.biom\n'
            '- 1 /protected/BIOM/{0}/sortmerna_picked_otus/seqs_otus.log '
            'BIOM/{0}/sortmerna_picked_otus/seqs_otus.log\n'
            '- 36615 /protected/templates/1_prep_1_qiime_[0-9]*-[0-9]*.'
            'txt mapping_files/{0}_mapping_file.txt\n'.format(a.id))
        self.assertRegexpMatches(response.body, exp)

        response = self.get('/download_study_bioms/200')
        self.assertEqual(response.code, 405)

        # changing user so we can test the failures
        BaseHandler.get_current_user = Mock(
            return_value=User("demo@microbio.me"))
        response = self.get('/download_study_bioms/1')
        self.assertEqual(response.code, 405)

        a.visibility = 'public'
        response = self.get('/download_study_bioms/1')
        self.assertEqual(response.code, 200)
        exp = (
            '- [0-9]* /protected/BIOM/{0}/otu_table.biom '
            'BIOM/{0}/otu_table.biom\n'
            '- 1 /protected/BIOM/{0}/sortmerna_picked_otus/seqs_otus.log '
            'BIOM/{0}/sortmerna_picked_otus/seqs_otus.log\n'
            '- 36615 /protected/templates/1_prep_1_qiime_[0-9]*-[0-9]*.'
            'txt mapping_files/{0}_mapping_file.txt\n'.format(a.id))
        self.assertRegexpMatches(response.body, exp)


class TestDownloadRelease(TestHandlerBase):

    def setUp(self):
        super(TestDownloadRelease, self).setUp()

    def tearDown(self):
        super(TestDownloadRelease, self).tearDown()

    def test_download(self):
        # check success
        response = self.get('/release/download/1')
        self.assertEqual(response.code, 200)
        self.assertIn(
            "This installation of Qiita was not equipped with nginx, so it is "
            "incapable of serving files. The file you attempted to download "
            "is located at", response.body)


class TestDownloadRawData(TestHandlerBase):

    def setUp(self):
        super(TestDownloadRawData, self).setUp()
        self._clean_up_files = []

    def tearDown(self):
        super(TestDownloadRawData, self).tearDown()
        for fp in self._clean_up_files:
            if exists(fp):
                if isdir(fp):
                    rmtree(fp)
                else:
                    remove(fp)

    def test_download_raw_data(self):
        # it's possible that one of the tests is deleting the raw data
        # so we will make sure that the files exists so this test passes
        all_files = [fp for a in Study(1).artifacts()
                     for _, fp, _ in a.filepaths]
        for fp in all_files:
            if not exists(fp):
                with open(fp, 'w') as f:
                    f.write('')
        response = self.get('/download_raw_data/1')
        self.assertEqual(response.code, 200)

        exp = (
            '- 58 /protected/raw_data/1_s_G1_L001_sequences.fastq.gz '
            'raw_data/1_s_G1_L001_sequences.fastq.gz\n'
            '- 58 /protected/raw_data/1_s_G1_L001_sequences_barcodes.fastq.gz '
            'raw_data/1_s_G1_L001_sequences_barcodes.fastq.gz\n'
            '- 36615 /protected/templates/1_prep_1_qiime_[0-9]*-[0-9]*.txt '
            'mapping_files/1_mapping_file.txt\n'
            '- 36615 /protected/templates/1_prep_2_qiime_[0-9]*-[0-9]*.txt '
            'mapping_files/7_mapping_file.txt\n')
        self.assertRegexpMatches(response.body, exp)

        response = self.get('/download_study_bioms/200')
        self.assertEqual(response.code, 405)

        # changing user so we can test the failures
        BaseHandler.get_current_user = Mock(
            return_value=User("demo@microbio.me"))
        response = self.get('/download_study_bioms/1')
        self.assertEqual(response.code, 405)


class TestDownloadEBISampleAccessions(TestHandlerBase):

    def setUp(self):
        super(TestDownloadEBISampleAccessions, self).setUp()

    def tearDown(self):
        super(TestDownloadEBISampleAccessions, self).tearDown()

    def test_download(self):
        # check success
        response = self.get('/download_ebi_accessions/samples/1')
        exp = ("sample_name\tsample_accession\n1.SKB2.640194\tERS000008\n"
               "1.SKM4.640180\tERS000004\n1.SKB3.640195\tERS000024\n"
               "1.SKB6.640176\tERS000025\n1.SKD6.640190\tERS000007\n"
               "1.SKM6.640187\tERS000022\n1.SKD9.640182\tERS000019\n"
               "1.SKM8.640201\tERS000014\n1.SKM2.640199\tERS000015\n"
               "1.SKD2.640178\tERS000009\n1.SKB7.640196\tERS000002\n"
               "1.SKD4.640185\tERS000023\n1.SKB8.640193\tERS000000\n"
               "1.SKM3.640197\tERS000018\n1.SKD5.640186\tERS000017\n"
               "1.SKB1.640202\tERS000011\n1.SKM1.640183\tERS000025\n"
               "1.SKD1.640179\tERS000012\n1.SKD3.640198\tERS000013\n"
               "1.SKB5.640181\tERS000006\n1.SKB4.640189\tERS000020\n"
               "1.SKB9.640200\tERS000016\n1.SKM9.640192\tERS000003\n"
               "1.SKD8.640184\tERS000001\n1.SKM5.640177\tERS000005\n"
               "1.SKM7.640188\tERS000010\n1.SKD7.640191\tERS000021")
        self.assertEqual(response.code, 200)
        self.assertRegexpMatches(response.body, exp)

        # changing user so we can test the failures
        BaseHandler.get_current_user = Mock(
            return_value=User("demo@microbio.me"))
        response = self.get('/download_ebi_accessions/samples/1')
        self.assertEqual(response.code, 405)


class TestDownloadEBIPrepAccessions(TestHandlerBase):

    def setUp(self):
        super(TestDownloadEBIPrepAccessions, self).setUp()

    def tearDown(self):
        super(TestDownloadEBIPrepAccessions, self).tearDown()

    def test_download(self):
        # check success
        response = self.get('/download_ebi_accessions/experiments/1')
        exp = ("sample_name\texperiment_accession\n1.SKB2.640194\tERX0000008\n"
               "1.SKM4.640180\tERX0000004\n1.SKB3.640195\tERX0000024\n"
               "1.SKB6.640176\tERX0000025\n1.SKD6.640190\tERX0000007\n"
               "1.SKM6.640187\tERX0000022\n1.SKD9.640182\tERX0000019\n"
               "1.SKM8.640201\tERX0000014\n1.SKM2.640199\tERX0000015\n"
               "1.SKD2.640178\tERX0000009\n1.SKB7.640196\tERX0000002\n"
               "1.SKD4.640185\tERX0000023\n1.SKB8.640193\tERX0000000\n"
               "1.SKM3.640197\tERX0000018\n1.SKD5.640186\tERX0000017\n"
               "1.SKB1.640202\tERX0000011\n1.SKM1.640183\tERX0000026\n"
               "1.SKD1.640179\tERX0000012\n1.SKD3.640198\tERX0000013\n"
               "1.SKB5.640181\tERX0000006\n1.SKB4.640189\tERX0000020\n"
               "1.SKB9.640200\tERX0000016\n1.SKM9.640192\tERX0000003\n"
               "1.SKD8.640184\tERX0000001\n1.SKM5.640177\tERX0000005\n"
               "1.SKM7.640188\tERX0000010\n1.SKD7.640191\tERX0000021")
        self.assertEqual(response.code, 200)
        self.assertRegexpMatches(response.body, exp)

        # changing user so we can test the failures
        BaseHandler.get_current_user = Mock(
            return_value=User("demo@microbio.me"))
        response = self.get('/download_ebi_accessions/experiments/1')
        self.assertEqual(response.code, 405)


if __name__ == '__main__':
    main()
