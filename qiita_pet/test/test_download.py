# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import main
from mock import Mock

from qiita_pet.test.tornado_test_base import TestHandlerBase
from qiita_pet.handlers.base_handlers import BaseHandler
from qiita_db.user import User


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

    def tearDown(self):
        super(TestDownloadStudyBIOMSHandler, self).tearDown()

    def test_download_study(self):
        response = self.get('/download_study_bioms/1')
        self.assertEqual(response.code, 200)
        exp = (
            '- 1256812 /protected/processed_data/1_study_1001_closed_'
            'reference_otu_table.biom processed_data/1_study_1001_closed_'
            'reference_otu_table.biom\n'
            '- 36615 /protected/templates/1_prep_1_qiime_[0-9]*-[0-9]*.txt '
            'mapping_files/4_mapping_file.txt\n'
            '- 1256812 /protected/processed_data/1_study_1001_closed_reference'
            '_otu_table.biom processed_data/1_study_1001_closed_'
            'reference_otu_table.biom\n'
            '- 36615 /protected/templates/1_prep_1_qiime_[0-9]*-[0-9]*.txt '
            'mapping_files/5_mapping_file.txt\n'
            '- 1256812 /protected/processed_data/1_study_1001_closed_reference'
            '_otu_table_Silva.biom processed_data/1_study_1001_closed_'
            'reference_otu_table_Silva.biom\n'
            '- 36615 /protected/templates/1_prep_1_qiime_[0-9]*-[0-9]*.txt '
            'mapping_files/6_mapping_file.txt\n'
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


if __name__ == '__main__':
    main()
