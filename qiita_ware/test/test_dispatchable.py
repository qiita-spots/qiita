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
    update_prep_template, delete_artifact, copy_raw_data, create_raw_data)
from qiita_db.study import Study
from qiita_db.artifact import Artifact
from qiita_db.exceptions import QiitaDBUnknownIDError
from qiita_db.metadata_template.prep_template import PrepTemplate


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

    def test_create_raw_data(self):
        fps = {'raw_barcodes': 'uploaded_file.txt',
               'raw_forward_seqs': 'update.txt'}
        obs = create_raw_data("FASTQ", PrepTemplate(1), fps, name="New name")
        exp = {'status': 'danger',
               'message': "Error creating artifact: Prep template 1 already "
                          "has an artifact associated"}
        self.assertEqual(obs, exp)

    def test_copy_raw_data(self):
        obs = copy_raw_data(PrepTemplate(1), 1)
        exp = {'status': 'danger',
               'message': "Error creating artifact: Prep template 1 already "
                          "has an artifact associated"}
        self.assertEqual(obs, exp)

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

    def test_update_sample_template(self):
        obs = update_sample_template(1, self.fp)
        exp = {'status': 'warning',
               'message': ("Sample names were already prefixed with the study "
                           "id.\nThe following columns have been added to the "
                           "existing template: new_col\nThere are no "
                           "differences between the data stored in the DB and "
                           "the new data provided\nSome functionality will be "
                           "disabled due to missing columns:\n"
                           "\t1.SKB2.640194, wrong value "
                           '"11/11/11 13:00:00";\n'
                           "\t1.SKM4.640180, wrong value "
                           '"11/11/11 13:00:00";\n'
                           "\t1.SKB3.640195, wrong value "
                           '"11/11/11 13:00:00";\n'
                           "\t1.SKB6.640176, wrong value "
                           '"11/11/11 13:00:00";\n'
                           "\t1.SKD6.640190, wrong value "
                           '"11/11/11 13:00:00";\n'
                           "\t1.SKM6.640187, wrong value "
                           '"11/11/11 13:00:00";\n'
                           "\t1.SKD9.640182, wrong value "
                           '"11/11/11 13:00:00";\n'
                           "\t1.SKM8.640201, wrong value "
                           '"11/11/11 13:00:00";\n'
                           "\t1.SKM2.640199, wrong value "
                           '"11/11/11 13:00:00";\n'
                           "\t1.SKD2.640178, wrong value "
                           '"11/11/11 13:00:00";\n'
                           "\t1.SKB7.640196, wrong value "
                           '"11/11/11 13:00:00";\n'
                           "\t1.SKD4.640185, wrong value "
                           '"11/11/11 13:00:00";\n'
                           "\t1.SKB8.640193, wrong value "
                           '"11/11/11 13:00:00";\n'
                           "\t1.SKM3.640197, wrong value "
                           '"11/11/11 13:00:00";\n'
                           "\t1.SKD5.640186, wrong value "
                           '"11/11/11 13:00:00";\n'
                           "\t1.SKB1.640202, wrong value "
                           '"11/11/11 13:00:00";\n'
                           "\t1.SKM1.640183, wrong value "
                           '"11/11/11 13:00:00";\n'
                           "\t1.SKD1.640179, wrong value "
                           '"11/11/11 13:00:00";\n'
                           "\t1.SKD3.640198, wrong value "
                           '"11/11/11 13:00:00";\n'
                           "\t1.SKB5.640181, wrong value "
                           '"11/11/11 13:00:00";\n'
                           "\t1.SKB4.640189, wrong value "
                           '"11/11/11 13:00:00";\n'
                           "\t1.SKB9.640200, wrong value "
                           '"11/11/11 13:00:00";\n'
                           "\t1.SKM9.640192, wrong value "
                           '"11/11/11 13:00:00";\n'
                           "\t1.SKD8.640184, wrong value "
                           '"11/11/11 13:00:00";\n'
                           "\t1.SKM5.640177, wrong value "
                           '"11/11/11 13:00:00";\n'
                           "\t1.SKM7.640188, wrong value "
                           '"11/11/11 13:00:00";\n'
                           "\t1.SKD7.640191, wrong value "
                           '"11/11/11 13:00:00".\nSee the Templates tutorial '
                           'for a description of these fields.')}
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
