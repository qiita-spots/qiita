# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import main

# from qiita_pet.exceptions import QiitaPetAuthorizationError
from qiita_pet.test.tornado_test_base import TestHandlerBase


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
        # response = self.get('/download/1000')


class TestDownloadStudyBIOMSHandler(TestHandlerBase):

    def setUp(self):
        super(TestDownloadStudyBIOMSHandler, self).setUp()

    def tearDown(self):
        super(TestDownloadStudyBIOMSHandler, self).tearDown()

    def test_download_study(self):
        # check success
        response = self.get('/download_study_bioms/1')
        self.assertEqual(response.code, 200)
        self.assertEqual(response.body, (
            "This installation of Qiita was not equipped with nginx, so it "
            "is incapable of serving files. The files you attempted to "
            "download are located at:\nbiom: processed_data/1_study_1001_"
            "closed_reference_otu_table.biom\nQIIME map file: templates/"
            "1_prep_1_qiime_19700101-000000.txt\nbiom: processed_data/"
            "1_study_1001_closed_reference_otu_table.biom\nQIIME map file: "
            "templates/1_prep_1_qiime_19700101-000000.txt\nbiom: "
            "processed_data/1_study_1001_closed_reference_otu_table_Silva.biom"
            "\nQIIME map file: templates/1_prep_1_qiime_19700101-000000.txt"))

        # failure
        # response = self.get('/download_study_bioms/2')


if __name__ == '__main__':
    main()
