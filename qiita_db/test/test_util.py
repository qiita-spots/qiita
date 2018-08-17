# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import TestCase, main
from tempfile import mkstemp, NamedTemporaryFile, TemporaryFile
from os import close, remove, makedirs, mkdir
from os.path import join, exists, basename
from shutil import rmtree
from datetime import datetime
from functools import partial
from string import punctuation
import h5py
from six import StringIO, BytesIO
import pandas as pd

from qiita_core.util import qiita_test_checker
import qiita_db as qdb


@qiita_test_checker()
class DBUtilTests(TestCase):
    def setUp(self):
        self.table = 'study'
        self.required = [
            'number_samples_promised', 'study_title', 'mixs_compliant',
            'metadata_complete', 'study_description', 'first_contact',
            'reprocess', 'timeseries_type_id', 'study_alias',
            'study_abstract', 'principal_investigator_id', 'email',
            'number_samples_collected']
        self.files_to_remove = []

    def tearDown(self):
        for fp in self.files_to_remove:
            if exists(fp):
                remove(fp)

    def test_params_dict_to_json(self):
        params_dict = {'opt1': '1', 'opt2': [2, '3'], 3: 9}
        exp = '{"3":9,"opt1":"1","opt2":[2,"3"]}'
        self.assertEqual(qdb.util.params_dict_to_json(params_dict), exp)

    def test_check_required_columns(self):
        # Doesn't do anything if correct info passed, only errors if wrong info
        qdb.util.check_required_columns(self.required, self.table)

    def test_check_required_columns_fail(self):
        self.required.remove('study_title')
        with self.assertRaises(qdb.exceptions.QiitaDBColumnError):
            qdb.util.check_required_columns(self.required, self.table)

    def test_check_table_cols(self):
        # Doesn't do anything if correct info passed, only errors if wrong info
        qdb.util.check_table_cols(self.required, self.table)

    def test_check_table_cols_fail(self):
        self.required.append('BADTHINGNOINHERE')
        with self.assertRaises(qdb.exceptions.QiitaDBColumnError):
            qdb.util.check_table_cols(self.required, self.table)

    def test_get_table_cols(self):
        obs = qdb.util.get_table_cols("qiita_user")
        exp = {"email", "user_level_id", "password", "name", "affiliation",
               "address", "phone", "user_verify_code", "pass_reset_code",
               "pass_reset_timestamp"}
        self.assertEqual(set(obs), exp)

    def test_exists_table(self):
        """Correctly checks if a table exists"""
        # True cases
        self.assertTrue(qdb.util.exists_table("filepath"))
        self.assertTrue(qdb.util.exists_table("qiita_user"))
        self.assertTrue(qdb.util.exists_table("analysis"))
        self.assertTrue(qdb.util.exists_table("prep_1"))
        self.assertTrue(qdb.util.exists_table("sample_1"))
        # False cases
        self.assertFalse(qdb.util.exists_table("sample_2"))
        self.assertFalse(qdb.util.exists_table("prep_3"))
        self.assertFalse(qdb.util.exists_table("foo_table"))
        self.assertFalse(qdb.util.exists_table("bar_table"))

    def test_convert_to_id(self):
        """Tests that ids are returned correctly"""
        self.assertEqual(
            qdb.util.convert_to_id("directory", "filepath_type"), 8)
        self.assertEqual(
            qdb.util.convert_to_id("private", "visibility", "visibility"), 3)
        self.assertEqual(
            qdb.util.convert_to_id("EMP", "portal_type", "portal"), 2)

    def test_convert_to_id_bad_value(self):
        """Tests that ids are returned correctly"""
        with self.assertRaises(qdb.exceptions.QiitaDBLookupError):
            qdb.util.convert_to_id("FAKE", "filepath_type")

    def test_get_artifact_types(self):
        obs = qdb.util.get_artifact_types()
        exp = {'SFF': 1, 'FASTA_Sanger': 2, 'FASTQ': 3, 'FASTA': 4,
               'per_sample_FASTQ': 5, 'Demultiplexed': 6, 'BIOM': 7,
               'beta_div_plots': 8L, 'rarefaction_curves': 9L,
               'taxa_summary': 10L}
        self.assertEqual(obs, exp)

        obs = qdb.util.get_artifact_types(key_by_id=True)
        exp = {v: k for k, v in exp.items()}
        self.assertEqual(obs, exp)

    def test_get_filepath_types(self):
        """Tests that get_filepath_types works with valid arguments"""
        obs = qdb.util.get_filepath_types()
        exp = {'raw_forward_seqs': 1, 'raw_reverse_seqs': 2,
               'raw_barcodes': 3, 'preprocessed_fasta': 4,
               'preprocessed_fastq': 5, 'preprocessed_demux': 6, 'biom': 7,
               'directory': 8, 'plain_text': 9, 'reference_seqs': 10,
               'reference_tax': 11, 'reference_tree': 12, 'log': 13,
               'sample_template': 14, 'prep_template': 15, 'qiime_map': 16,
               }
        exp = dict(self.conn_handler.execute_fetchall(
            "SELECT filepath_type,filepath_type_id FROM qiita.filepath_type"))
        self.assertEqual(obs, exp)

        obs = qdb.util.get_filepath_types(key='filepath_type_id')
        exp = {v: k for k, v in exp.items()}
        self.assertEqual(obs, exp)

    def test_get_filepath_types_fail(self):
        """Tests that get_Filetypes fails with invalid argument"""
        with self.assertRaises(qdb.exceptions.QiitaDBColumnError):
            qdb.util.get_filepath_types(key='invalid')

    def test_get_data_types(self):
        """Tests that get_data_types works with valid arguments"""
        obs = qdb.util.get_data_types()
        exp = {'16S': 1, '18S': 2, 'ITS': 3, 'Proteomic': 4, 'Metabolomic': 5,
               'Metagenomic': 6, 'Multiomic': 7, 'Metatranscriptomics': 8,
               'Viromics': 9, 'Genomics': 10, 'Transcriptomics': 11}
        self.assertEqual(obs, exp)

        obs = qdb.util.get_data_types(key='data_type_id')
        exp = {v: k for k, v in exp.items()}
        self.assertEqual(obs, exp)

    def test_create_rand_string(self):
        set_punct = set(punctuation)

        obs = qdb.util.create_rand_string(200)
        self.assertEqual(len(obs), 200)
        self.assertTrue(set_punct.intersection(set(obs)))

        obs = qdb.util.create_rand_string(400, punct=False)
        self.assertEqual(len(obs), 400)
        self.assertFalse(set_punct.intersection(set(obs)))

    def test_get_count(self):
        """Checks that get_count retrieves proper count"""
        self.assertEqual(qdb.util.get_count('qiita.study_person'), 3)

    def test_check_count(self):
        """Checks that check_count returns True and False appropriately"""
        self.assertTrue(qdb.util.check_count('qiita.study_person', 3))
        self.assertFalse(qdb.util.check_count('qiita.study_person', 2))

    def test_insert_filepaths(self):
        fd, fp = mkstemp()
        close(fd)
        with open(fp, "w") as f:
            f.write("\n")
        self.files_to_remove.append(fp)

        exp_new_id = 1 + self.conn_handler.execute_fetchone(
            "SELECT last_value FROM qiita.filepath_filepath_id_seq")[0]
        obs = qdb.util.insert_filepaths([(fp, 1)], 2, "raw_data")
        self.assertEqual(obs, [exp_new_id])

        # Check that the files have been copied correctly
        exp_fp = join(qdb.util.get_db_files_base_dir(), "raw_data",
                      "2_%s" % basename(fp))
        self.assertTrue(exists(exp_fp))
        self.assertFalse(exists(fp))
        self.files_to_remove.append(exp_fp)

        # Check that the filepaths have been added to the DB
        obs = self.conn_handler.execute_fetchall(
            "SELECT * FROM qiita.filepath WHERE filepath_id=%d" % exp_new_id)
        exp_fp = "2_%s" % basename(fp)
        exp = [[exp_new_id, exp_fp, 1, '852952723', 1, 5]]
        self.assertEqual(obs, exp)

        qdb.util.purge_filepaths()

    def test_insert_filepaths_copy(self):
        fd, fp = mkstemp()
        close(fd)
        with open(fp, "w") as f:
            f.write("\n")
        self.files_to_remove.append(fp)

        # The id's in the database are bigserials, i.e. they get
        # autoincremented for each element introduced.
        exp_new_id = 1 + self.conn_handler.execute_fetchone(
            "SELECT last_value FROM qiita.filepath_filepath_id_seq")[0]
        obs = qdb.util.insert_filepaths([(fp, 1)], 2, "raw_data", copy=True)
        self.assertEqual(obs, [exp_new_id])

        # Check that the files have been copied correctly
        exp_fp = join(qdb.util.get_db_files_base_dir(), "raw_data",
                      "2_%s" % basename(fp))
        self.assertTrue(exists(exp_fp))
        self.assertTrue(exists(fp))
        self.files_to_remove.append(exp_fp)

        # Check that the filepaths have been added to the DB
        obs = self.conn_handler.execute_fetchall(
            "SELECT * FROM qiita.filepath WHERE filepath_id=%d" % exp_new_id)
        exp_fp = "2_%s" % basename(fp)
        exp = [[exp_new_id, exp_fp, 1, '852952723', 1, 5]]
        self.assertEqual(obs, exp)

        qdb.util.purge_filepaths()

    def test_insert_filepaths_string(self):
        fd, fp = mkstemp()
        close(fd)
        with open(fp, "w") as f:
            f.write("\n")
        self.files_to_remove.append(fp)

        exp_new_id = 1 + self.conn_handler.execute_fetchone(
            "SELECT last_value FROM qiita.filepath_filepath_id_seq")[0]
        obs = qdb.util.insert_filepaths(
            [(fp, "raw_forward_seqs")], 2, "raw_data")
        self.assertEqual(obs, [exp_new_id])

        # Check that the files have been copied correctly
        exp_fp = join(qdb.util.get_db_files_base_dir(), "raw_data",
                      "2_%s" % basename(fp))
        self.assertTrue(exists(exp_fp))
        self.files_to_remove.append(exp_fp)

        # Check that the filepaths have been added to the DB
        obs = self.conn_handler.execute_fetchall(
            "SELECT * FROM qiita.filepath WHERE filepath_id=%d" % exp_new_id)
        exp_fp = "2_%s" % basename(fp)
        exp = [[exp_new_id, exp_fp, 1, '852952723', 1, 5]]
        self.assertEqual(obs, exp)

        qdb.util.purge_filepaths()

    def test_retrieve_filepaths(self):
        obs = qdb.util.retrieve_filepaths('artifact_filepath',
                                          'artifact_id', 1)
        path_builder = partial(
            join, qdb.util.get_db_files_base_dir(), "raw_data")
        exp = [(1, path_builder("1_s_G1_L001_sequences.fastq.gz"),
                "raw_forward_seqs"),
               (2, path_builder("1_s_G1_L001_sequences_barcodes.fastq.gz"),
                "raw_barcodes")]
        self.assertEqual(obs, exp)

    def test_retrieve_filepaths_sort(self):
        obs = qdb.util.retrieve_filepaths(
            'artifact_filepath', 'artifact_id', 1, sort='descending')
        path_builder = partial(
            join, qdb.util.get_db_files_base_dir(), "raw_data")
        exp = [(2, path_builder("1_s_G1_L001_sequences_barcodes.fastq.gz"),
                "raw_barcodes"),
               (1, path_builder("1_s_G1_L001_sequences.fastq.gz"),
                "raw_forward_seqs")]
        self.assertEqual(obs, exp)

    def test_retrieve_filepaths_type(self):
        obs = qdb.util.retrieve_filepaths(
            'artifact_filepath', 'artifact_id', 1, sort='descending',
            fp_type='raw_barcodes')
        path_builder = partial(
            join, qdb.util.get_db_files_base_dir(), "raw_data")
        exp = [(2, path_builder("1_s_G1_L001_sequences_barcodes.fastq.gz"),
                "raw_barcodes")]
        self.assertEqual(obs, exp)

        obs = qdb.util.retrieve_filepaths(
            'artifact_filepath', 'artifact_id', 1, fp_type='raw_barcodes')
        path_builder = partial(
            join, qdb.util.get_db_files_base_dir(), "raw_data")
        exp = [(2, path_builder("1_s_G1_L001_sequences_barcodes.fastq.gz"),
                "raw_barcodes")]
        self.assertEqual(obs, exp)

        obs = qdb.util.retrieve_filepaths(
            'artifact_filepath', 'artifact_id', 1, fp_type='biom')
        path_builder = partial(
            join, qdb.util.get_db_files_base_dir(), "raw_data")
        self.assertEqual(obs, [])

    def test_retrieve_filepaths_error(self):
        with self.assertRaises(qdb.exceptions.QiitaDBError):
            qdb.util.retrieve_filepaths('artifact_filepath', 'artifact_id', 1,
                                        sort='Unknown')

    def _common_purge_filepaths_test(self):
        # Get all the filepaths so we can test if they've been removed or not
        sql_fp = "SELECT filepath, data_directory_id FROM qiita.filepath"
        fps = [join(qdb.util.get_mountpoint_path_by_id(dd_id), fp)
               for fp, dd_id in self.conn_handler.execute_fetchall(sql_fp)]

        # Make sure that the files exist - specially for travis
        for fp in fps:
            if not exists(fp):
                with open(fp, 'w') as f:
                    f.write('\n')
                self.files_to_remove.append(fp)

        _, raw_data_mp = qdb.util.get_mountpoint('raw_data')[0]

        removed_fps = [
            join(raw_data_mp, '2_sequences_barcodes.fastq.gz'),
            join(raw_data_mp, '2_sequences.fastq.gz'),
            join(raw_data_mp, 'directory_test')]

        for fp in removed_fps[:-1]:
            with open(fp, 'w') as f:
                f.write('\n')
        makedirs(removed_fps[-1])

        sql = """INSERT INTO qiita.filepath
                    (filepath, filepath_type_id, checksum,
                     checksum_algorithm_id, data_directory_id)
                VALUES ('2_sequences_barcodes.fastq.gz', 3, '852952723', 1, 5),
                       ('2_sequences.fastq.gz', 1, '852952723', 1, 5),
                       ('directory_test', 8, '852952723', 1, 5)
                RETURNING filepath_id"""
        fp_ids = self.conn_handler.execute_fetchall(sql)

        fps = set(fps).difference(removed_fps)

        # Check that the files exist
        for fp in fps:
            self.assertTrue(exists(fp))
        for fp in removed_fps:
            self.assertTrue(exists(fp))

        exp_count = qdb.util.get_count("qiita.filepath") - 3

        qdb.util.purge_filepaths()

        obs_count = qdb.util.get_count("qiita.filepath")

        # Check that only 2 rows have been removed
        self.assertEqual(obs_count, exp_count)

        # Check that the 2 rows that have been removed are the correct ones
        sql = """SELECT EXISTS(
                    SELECT * FROM qiita.filepath WHERE filepath_id = %s)"""
        obs = self.conn_handler.execute_fetchone(sql, (fp_ids[0][0],))[0]
        self.assertFalse(obs)
        obs = self.conn_handler.execute_fetchone(sql, (fp_ids[1][0],))[0]
        self.assertFalse(obs)

        # Check that the files have been successfully removed
        for fp in removed_fps:
            self.assertFalse(exists(fp))

        # Check that all the other files still exist
        for fp in fps:
            self.assertTrue(exists(fp))

    def test_purge_filepaths(self):
        self._common_purge_filepaths_test()

    def test_purge_files_from_filesystem(self):
        info = {"timeseries_type_id": 1, "metadata_complete": True,
                "mixs_compliant": True, "number_samples_collected": 25,
                "number_samples_promised": 28, "study_alias": "TST",
                "study_description": "Some description of the study goes here",
                "study_abstract": "Some abstract goes here",
                "emp_person_id": qdb.study.StudyPerson(1),
                "principal_investigator_id": qdb.study.StudyPerson(1),
                "lab_person_id": qdb.study.StudyPerson(1)}

        new_study = qdb.study.Study.create(
            qdb.user.User('shared@foo.bar'),
            'test_purge_files_from_filesystem', info=info)

        metadata_dict = {
            'SKB8.640193': {'center_name': 'ANL',
                            'primer': 'GTGCCAGCMGCCGCGGTAA',
                            'barcode': 'GTCCGCAAGTTA',
                            'run_prefix': "s_G1_L001_sequences",
                            'platform': 'ILLUMINA',
                            'instrument_model': 'Illumina MiSeq',
                            'library_construction_protocol': 'AAAA',
                            'experiment_design_description': 'BBBB'}}
        metadata = pd.DataFrame.from_dict(metadata_dict, orient='index',
                                          dtype=str)
        st = qdb.metadata_template.sample_template.SampleTemplate.create(
            metadata, new_study)
        fps = [fp for _, fp in st.get_filepaths()]
        qdb.metadata_template.sample_template.SampleTemplate.delete(st.id)
        qdb.study.Study.delete(new_study.id)

        for fp in fps:
            self.assertTrue(exists(fp))

        qdb.util.purge_files_from_filesystem(True)

        for fp in fps:
            self.assertFalse(exists(fp))

    def test_empty_trash_upload_folder(self):
        # creating file to delete so we know it actually works
        study_id = '1'
        uploads_fp = join(qdb.util.get_mountpoint("uploads")[0][1], study_id)
        trash = join(uploads_fp, 'trash')
        if not exists(trash):
            mkdir(trash)
        fp = join(trash, 'my_file_to_delete.txt')
        open(fp, 'w').close()

        self.assertTrue(exists(fp))
        qdb.util.empty_trash_upload_folder()
        self.assertFalse(exists(fp))

    def test_purge_filepaths_null_cols(self):
        # For more details about the source of the issue that motivates this
        # test: http://www.depesz.com/2008/08/13/nulls-vs-not-in/
        # In the current set up, the only place where we can actually have a
        # null value in a filepath id is in the reference table. Add a new
        # reference without tree and taxonomy:
        fd, seqs_fp = mkstemp(suffix="_seqs.fna")
        close(fd)
        ref = qdb.reference.Reference.create("null_db", "13_2", seqs_fp)
        self.files_to_remove.append(ref.sequence_fp)

        self._common_purge_filepaths_test()

    def test_move_filepaths_to_upload_folder(self):
        # setting up test, done here as this is the only test that uses these
        # files
        fd, seqs_fp = mkstemp(suffix='_seqs.fastq')
        close(fd)
        fd, html_fp = mkstemp(suffix='.html')
        close(fd)
        st = qdb.study.Study(1)
        metadata_dict = {
            'SKB8.640193': {'center_name': 'ANL',
                            'primer': 'GTGCCAGCMGCCGCGGTAA',
                            'barcode': 'GTCCGCAAGTTA',
                            'run_prefix': "s_G1_L001_sequences",
                            'platform': 'ILLUMINA',
                            'instrument_model': 'Illumina MiSeq',
                            'library_construction_protocol': 'AAAA',
                            'experiment_design_description': 'BBBB'}}
        metadata = pd.DataFrame.from_dict(metadata_dict, orient='index',
                                          dtype=str)
        pt = qdb.metadata_template.prep_template.PrepTemplate.create(
            metadata, qdb.study.Study(1), "16S")

        artifact = qdb.artifact.Artifact.create(
            [(seqs_fp, 1), (html_fp, 'html_summary')], "FASTQ",
            prep_template=pt)
        filepaths = artifact.filepaths
        # deleting reference so we can directly call
        # move_filepaths_to_upload_folder
        for fid, _, _ in filepaths:
            sql = "DELETE FROM qiita.artifact_filepath WHERE filepath_id=%s"
            self.conn_handler.execute(sql, (fid,))

        # moving filepaths
        qdb.util.move_filepaths_to_upload_folder(st.id, filepaths)

        # check that they do not exist in the old path but do in the new one
        path_for_removal = join(qdb.util.get_mountpoint("uploads")[0][1],
                                str(st.id))
        for _, fp, fp_type in filepaths:
            self.assertFalse(exists(fp))
            new_fp = join(path_for_removal, basename(fp))
            if fp_type == 'html_summary':
                # The html summary gets removed, not moved
                self.assertFalse(exists(new_fp))
            else:
                self.assertTrue(exists(new_fp))

            self.files_to_remove.append(new_fp)

    def test_get_mountpoint(self):
        exp = [(5, join(qdb.util.get_db_files_base_dir(), 'raw_data'))]
        obs = qdb.util.get_mountpoint("raw_data")
        self.assertEqual(obs, exp)

        exp = [(1, join(qdb.util.get_db_files_base_dir(), 'analysis'))]
        obs = qdb.util.get_mountpoint("analysis")
        self.assertEqual(obs, exp)

        exp = [(2, join(qdb.util.get_db_files_base_dir(), 'job'))]
        obs = qdb.util.get_mountpoint("job")
        self.assertEqual(obs, exp)

        # inserting new ones so we can test that it retrieves these and
        # doesn't alter other ones
        self.conn_handler.execute(
            "UPDATE qiita.data_directory SET active=false WHERE "
            "data_directory_id=1")
        count = qdb.util.get_count('qiita.data_directory')
        sql = """INSERT INTO qiita.data_directory (data_type, mountpoint,
                                                   subdirectory, active)
                 VALUES ('analysis', 'analysis_tmp', true, true),
                        ('raw_data', 'raw_data_tmp', true, false)"""
        self.conn_handler.execute(sql)

        # this should have been updated
        exp = [(count + 1, join(qdb.util.get_db_files_base_dir(),
                'analysis_tmp'))]
        obs = qdb.util.get_mountpoint("analysis")
        self.assertEqual(obs, exp)

        # these 2 shouldn't
        exp = [(5, join(qdb.util.get_db_files_base_dir(), 'raw_data'))]
        obs = qdb.util.get_mountpoint("raw_data")
        self.assertEqual(obs, exp)

        exp = [(2, join(qdb.util.get_db_files_base_dir(), 'job'))]
        obs = qdb.util.get_mountpoint("job")
        self.assertEqual(obs, exp)

        # testing multi returns
        exp = [(5, join(qdb.util.get_db_files_base_dir(), 'raw_data')),
               (count + 2, join(qdb.util.get_db_files_base_dir(),
                'raw_data_tmp'))]
        obs = qdb.util.get_mountpoint("raw_data", retrieve_all=True)
        self.assertEqual(obs, exp)

        # testing retrieve subdirectory
        exp = [
            (5, join(qdb.util.get_db_files_base_dir(), 'raw_data'), False),
            (count + 2, join(qdb.util.get_db_files_base_dir(), 'raw_data_tmp'),
             True)]
        obs = qdb.util.get_mountpoint("raw_data", retrieve_all=True,
                                      retrieve_subdir=True)
        self.assertEqual(obs, exp)

    def test_get_mountpoint_path_by_id(self):
        exp = join(qdb.util.get_db_files_base_dir(), 'raw_data')
        obs = qdb.util.get_mountpoint_path_by_id(5)
        self.assertEqual(obs, exp)

        exp = join(qdb.util.get_db_files_base_dir(), 'analysis')
        obs = qdb.util.get_mountpoint_path_by_id(1)
        self.assertEqual(obs, exp)

        exp = join(qdb.util.get_db_files_base_dir(), 'job')
        obs = qdb.util.get_mountpoint_path_by_id(2)
        self.assertEqual(obs, exp)

        # inserting new ones so we can test that it retrieves these and
        # doesn't alter other ones
        self.conn_handler.execute(
            "UPDATE qiita.data_directory SET active=false WHERE "
            "data_directory_id=1")
        count = qdb.util.get_count('qiita.data_directory')
        sql = """INSERT INTO qiita.data_directory (data_type, mountpoint,
                                                   subdirectory, active)
                 VALUES ('analysis', 'analysis_tmp', true, true),
                        ('raw_data', 'raw_data_tmp', true, false)"""
        self.conn_handler.execute(sql)

        # this should have been updated
        exp = join(qdb.util.get_db_files_base_dir(), 'analysis_tmp')
        obs = qdb.util.get_mountpoint_path_by_id(count + 1)
        self.assertEqual(obs, exp)

        # these 2 shouldn't
        exp = join(qdb.util.get_db_files_base_dir(), 'raw_data')
        obs = qdb.util.get_mountpoint_path_by_id(5)
        self.assertEqual(obs, exp)

        exp = join(qdb.util.get_db_files_base_dir(), 'job')
        obs = qdb.util.get_mountpoint_path_by_id(2)
        self.assertEqual(obs, exp)

    def test_get_files_from_uploads_folders(self):
        # something has been uploaded and ignoring hidden files/folders
        # and folders
        exp = (7, 'uploaded_file.txt', '0 Bytes')
        obs = qdb.util.get_files_from_uploads_folders("1")
        self.assertIn(exp, obs)

        # nothing has been uploaded
        exp = []
        obs = qdb.util.get_files_from_uploads_folders("2")
        self.assertEqual(obs, exp)

    def test_move_upload_files_to_trash(self):
        test_filename = 'this_is_a_test_file.txt'

        # create file to move to trash
        fid, folder = qdb.util.get_mountpoint("uploads")[0]
        test_fp = join(folder, '1', test_filename)
        with open(test_fp, 'w') as f:
            f.write('test')

        self.files_to_remove.append(test_fp)

        exp = (fid, 'this_is_a_test_file.txt', '4 Bytes')
        obs = qdb.util.get_files_from_uploads_folders("1")
        self.assertIn(exp, obs)

        # move file
        qdb.util.move_upload_files_to_trash(1, [(fid, test_filename)])
        obs = qdb.util.get_files_from_uploads_folders("1")
        self.assertNotIn(obs, exp)

        # if the file doesn't exist, don't raise any errors
        qdb.util.move_upload_files_to_trash(1, [(fid, test_filename)])

        # testing errors
        # - study doesn't exist
        with self.assertRaises(qdb.exceptions.QiitaDBError):
            qdb.util.move_upload_files_to_trash(100, [(fid, test_filename)])
        # - fid doen't exist
        with self.assertRaises(qdb.exceptions.QiitaDBError):
            qdb.util.move_upload_files_to_trash(1, [(10, test_filename)])

        # removing trash folder
        rmtree(join(folder, '1', 'trash'))

    def test_get_environmental_packages(self):
        obs = qdb.util.get_environmental_packages()
        exp = [['air', 'ep_air'],
               ['built environment', 'ep_built_environment'],
               ['host-associated', 'ep_host_associated'],
               ['human-amniotic-fluid', 'ep_human_amniotic_fluid'],
               ['human-associated', 'ep_human_associated'],
               ['human-blood', 'ep_human_blood'],
               ['human-gut', 'ep_human_gut'],
               ['human-oral', 'ep_human_oral'],
               ['human-skin', 'ep_human_skin'],
               ['human-urine', 'ep_human_urine'],
               ['human-vaginal', 'ep_human_vaginal'],
               ['microbial mat/biofilm', 'ep_microbial_mat_biofilm'],
               ['miscellaneous natural or artificial environment',
                'ep_misc_artif'],
               ['plant-associated', 'ep_plant_associated'],
               ['sediment', 'ep_sediment'],
               ['soil', 'ep_soil'],
               ['wastewater/sludge', 'ep_wastewater_sludge'],
               ['water', 'ep_water']]
        self.assertEqual(sorted(obs), sorted(exp))

    def test_get_timeseries_types(self):
        obs = qdb.util.get_timeseries_types()
        exp = [[1, 'None', 'None'],
               [2, 'real', 'single intervention'],
               [3, 'real', 'multiple intervention'],
               [4, 'real', 'combo intervention'],
               [5, 'pseudo', 'single intervention'],
               [6, 'pseudo', 'multiple intervention'],
               [7, 'pseudo', 'combo intervention'],
               [8, 'mixed', 'single intervention'],
               [9, 'mixed', 'multiple intervention'],
               [10, 'mixed', 'combo intervention']]
        self.assertEqual(obs, exp)

    def test_get_filepath_information(self):
        obs = qdb.util.get_filepath_information(1)
        # This path is machine specific. Just checking that is not empty
        self.assertIsNotNone(obs.pop('fullpath'))
        exp = {'filepath_id': 1L, 'filepath': '1_s_G1_L001_sequences.fastq.gz',
               'filepath_type': 'raw_forward_seqs', 'checksum': '852952723',
               'data_type': 'raw_data', 'mountpoint': 'raw_data',
               'subdirectory': False, 'active': True}
        self.assertEqual(obs, exp)

    def test_filepath_id_to_rel_path(self):
        obs = qdb.util.filepath_id_to_rel_path(1)
        exp = 'raw_data/1_s_G1_L001_sequences.fastq.gz'
        self.assertEqual(obs, exp)

        obs = qdb.util.filepath_id_to_rel_path(3)
        exp = 'preprocessed_data/1_seqs.fna'
        self.assertEqual(obs, exp)

        fd, fp = mkstemp()
        close(fd)
        with open(fp, 'w') as f:
            f.write('\n')
        self.files_to_remove.append(fp)
        test = qdb.util.insert_filepaths(
            [(fp, "raw_forward_seqs")], 2, "FASTQ")[0]
        with qdb.sql_connection.TRN:
            sql = """INSERT INTO qiita.artifact_filepath
                            (artifact_id, filepath_id)
                        VALUES (%s, %s)"""
            qdb.sql_connection.TRN.add(sql, [2, test])
            qdb.sql_connection.TRN.execute()

        obs = qdb.util.filepath_id_to_rel_path(test)
        exp = 'FASTQ/2/%s' % basename(fp)
        self.assertEqual(obs, exp)

    def test_filepath_ids_to_rel_paths(self):
        fd, fp = mkstemp()
        close(fd)
        with open(fp, 'w') as f:
            f.write('\n')
        self.files_to_remove.append(fp)
        test = qdb.util.insert_filepaths(
            [(fp, "raw_forward_seqs")], 2, "FASTQ")[0]
        with qdb.sql_connection.TRN:
            sql = """INSERT INTO qiita.artifact_filepath
                            (artifact_id, filepath_id)
                        VALUES (%s, %s)"""
            qdb.sql_connection.TRN.add(sql, [2, test])
            qdb.sql_connection.TRN.execute()

        obs = qdb.util.filepath_ids_to_rel_paths([1, 3, test])
        exp = {1: 'raw_data/1_s_G1_L001_sequences.fastq.gz',
               3: 'preprocessed_data/1_seqs.fna',
               test: 'FASTQ/2/%s' % basename(fp)}

        self.assertEqual(obs, exp)

    def test_add_message(self):
        count = qdb.util.get_count('qiita.message') + 1
        user = qdb.user.User.create('new@test.bar', 'password')
        users = [user]
        qdb.util.add_message("TEST MESSAGE", users)

        obs = [[x[0], x[1]] for x in user.messages()]
        exp = [[count, 'TEST MESSAGE']]
        self.assertEqual(obs, exp)

    def test_add_system_message(self):
        count = qdb.util.get_count('qiita.message') + 1
        qdb.util.add_system_message("SYS MESSAGE",
                                    datetime(2015, 8, 5, 19, 41))

        obs = [[x[0], x[1]]
               for x in qdb.user.User('shared@foo.bar').messages()]
        exp = [[count, 'SYS MESSAGE'], [1, 'message 1']]
        self.assertEqual(obs, exp)
        obs = [[x[0], x[1]] for x in qdb.user.User('admin@foo.bar').messages()]
        exp = [[count, 'SYS MESSAGE']]
        self.assertEqual(obs, exp)

        sql = "SELECT expiration from qiita.message WHERE message_id = %s"
        obs = self.conn_handler.execute_fetchall(sql, [count])
        exp = [[datetime(2015, 8, 5, 19, 41)]]
        self.assertEqual(obs, exp)

    def test_clear_system_messages(self):
        message_id = qdb.util.get_count('qiita.message') + 1
        user = qdb.user.User.create('csm@test.bar', 'password')
        obs = [[x[0], x[1]] for x in user.messages()]
        exp = []
        self.assertEqual(obs, exp)

        qdb.util.add_system_message("SYS MESSAGE",
                                    datetime(2015, 8, 5, 19, 41))
        obs = [[x[0], x[1]] for x in user.messages()]
        exp = [[message_id, 'SYS MESSAGE']]
        self.assertItemsEqual(obs, exp)

        qdb.util.clear_system_messages()
        obs = [[x[0], x[1]] for x in user.messages()]
        exp = []
        self.assertEqual(obs, exp)

        # Run again with no system messages to make sure no errors
        qdb.util.clear_system_messages()

    def test_supported_filepath_types(self):
        obs = qdb.util.supported_filepath_types("FASTQ")
        exp = [["raw_forward_seqs", True], ["raw_reverse_seqs", False],
               ["raw_barcodes", True]]
        self.assertItemsEqual(obs, exp)

        obs = qdb.util.supported_filepath_types("BIOM")
        exp = [["biom", True], ["directory", False], ["log", False]]
        self.assertItemsEqual(obs, exp)

    def test_generate_analysis_list(self):
        self.assertEqual(qdb.util.generate_analysis_list([]), [])

        obs = qdb.util.generate_analysis_list([1, 2, 3, 5])
        exp = [{'mapping_files': [
                (16, qdb.util.get_filepath_information(16)['fullpath'])],
                'description': 'A test analysis', 'artifacts': [9], 'name':
                'SomeAnalysis', 'analysis_id': 1, 'visibility': 'private'},
               {'mapping_files': [], 'description': 'Another test analysis',
                'artifacts': [], 'name': 'SomeSecondAnalysis',
                'analysis_id': 2, 'visibility': 'private'}]
        # removing timestamp for testing
        for i in range(len(obs)):
            del obs[i]['timestamp']
        self.assertEqual(obs, exp)

        self.assertEqual(
            qdb.util.generate_analysis_list([1, 2, 3, 5], True), [])


@qiita_test_checker()
class UtilTests(TestCase):
    """Tests for the util functions that do not need to access the DB"""

    def setUp(self):
        fh, self.filepath = mkstemp()
        close(fh)
        with open(self.filepath, "w") as f:
            f.write("Some text so we can actually compute a checksum")

    def test_compute_checksum(self):
        """Correctly returns the file checksum"""
        obs = qdb.util.compute_checksum(self.filepath)
        exp = 1719580229
        self.assertEqual(obs, exp)

    def test_scrub_data_nothing(self):
        """Returns the same string without changes"""
        self.assertEqual(qdb.util.scrub_data("nothing_changes"),
                         "nothing_changes")

    def test_scrub_data_semicolon(self):
        """Correctly removes the semicolon from the string"""
        self.assertEqual(qdb.util.scrub_data("remove_;_char"), "remove__char")

    def test_scrub_data_single_quote(self):
        """Correctly removes single quotes from the string"""
        self.assertEqual(qdb.util.scrub_data("'quotes'"), "quotes")

    def test_get_visibilities(self):
        obs = qdb.util.get_visibilities()
        exp = ['awaiting_approval', 'sandbox', 'private', 'public']
        self.assertEqual(obs, exp)

    def test_infer_status(self):
        obs = qdb.util.infer_status([])
        self.assertEqual(obs, 'sandbox')

        obs = qdb.util.infer_status([['private']])
        self.assertEqual(obs, 'private')

        obs = qdb.util.infer_status([['private'], ['public']])
        self.assertEqual(obs, 'public')

        obs = qdb.util.infer_status([['sandbox'], ['awaiting_approval']])
        self.assertEqual(obs, 'awaiting_approval')

        obs = qdb.util.infer_status([['sandbox'], ['sandbox']])
        self.assertEqual(obs, 'sandbox')

    def test_get_pubmed_ids_from_dois(self):
        exp = {'10.100/123456': '123456'}
        obs = qdb.util.get_pubmed_ids_from_dois(['', '10.100/123456'])
        self.assertEqual(obs, exp)

    def test_generate_study_list(self):
        USER = qdb.user.User
        STUDY = qdb.study.Study
        PREP = qdb.metadata_template.prep_template.PrepTemplate
        UTIL = qdb.util

        # creating a new study to make sure that empty studies are also
        # returned
        info = {"timeseries_type_id": 1, "metadata_complete": True,
                "mixs_compliant": True, "number_samples_collected": 25,
                "number_samples_promised": 28, "study_alias": "TST",
                "study_description": "Some description of the study goes here",
                "study_abstract": "Some abstract goes here",
                "emp_person_id": qdb.study.StudyPerson(1),
                "principal_investigator_id": qdb.study.StudyPerson(1),
                "lab_person_id": qdb.study.StudyPerson(1)}
        new_study = STUDY.create(
            USER('shared@foo.bar'), 'test_study_1', info=info)

        sinfo = {
            'study_id': 1,
            'owner': 'Dude',
            'study_alias': 'Cannabis Soils',
            'status': 'private',
            'study_abstract':
                'This is a preliminary study to examine the microbiota '
                'associated with the Cannabis plant. Soils samples '
                'from the bulk soil, soil associated with the roots, '
                'and the rhizosphere were extracted and the DNA '
                'sequenced. Roots from three independent plants of '
                'different strains were examined. These roots were '
                'obtained November 11, 2011 from plants that had been '
                'harvested in the summer. Future studies will attempt '
                'to analyze the soils and rhizospheres from the same '
                'location at different time points in the plant '
                'lifecycle.',
            'metadata_complete': True,
            'ebi_study_accession': 'EBI123456-BB',
            'ebi_submission_status': 'submitted',
            'study_title':
                'Identification of the Microbiomes for Cannabis Soils',
            'number_samples_collected': 27,
            'shared': [('shared@foo.bar', 'Shared')],
            'publication_doi': ['10.100/123456', '10.100/7891011'],
            'publication_pid': ['123456', '7891011'],
            'pi': ('PI_dude@foo.bar', 'PIDude'),
            'artifact_biom_ids': [4, 5, 6, 7],
            'study_tags': None,
        }
        snew_info = {
            'status': 'sandbox', 'study_title': 'test_study_1',
            'metadata_complete': True, 'publication_pid': [],
            'artifact_biom_ids': None,
            'ebi_submission_status': 'not submitted',
            'study_id': new_study.id, 'ebi_study_accession': None,
            'owner': 'Shared', 'shared': [],
            'study_abstract': 'Some abstract goes here',
            'pi': ('lab_dude@foo.bar', 'LabDude'), 'publication_doi': [],
            'study_alias': 'TST', 'study_tags': None,
            'number_samples_collected': 0}
        exp1 = [sinfo]
        exp2 = [snew_info]
        exp_both = [sinfo, snew_info]

        # let's make sure that everything is private for study 1
        for a in STUDY(1).artifacts():
            a.visibility = 'private'

        # owner of study
        obs = UTIL.generate_study_list(USER('test@foo.bar'), 'user')
        self.assertEqual(obs, exp1)
        # shared with
        obs = UTIL.generate_study_list(USER('shared@foo.bar'), 'user')
        self.assertEqual(obs, exp_both)
        # admin
        obs = UTIL.generate_study_list(USER('admin@foo.bar'), 'user')
        self.assertEqual(obs, exp_both)
        # no access/hidden
        obs = UTIL.generate_study_list(USER('demo@microbio.me'), 'user')
        self.assertEqual(obs, [])
        # public - none for everyone
        obs = UTIL.generate_study_list(USER('test@foo.bar'), 'public')
        self.assertEqual(obs, [])
        obs = UTIL.generate_study_list(USER('shared@foo.bar'), 'public')
        self.assertEqual(obs, [])
        obs = UTIL.generate_study_list(USER('admin@foo.bar'), 'public')
        self.assertEqual(obs, [])
        obs = UTIL.generate_study_list(USER('demo@microbio.me'), 'public')
        self.assertEqual(obs, [])

        def _avoid_duplicated_tests(all_artifacts=False):
            # nothing should shange for owner, shared
            obs = UTIL.generate_study_list(USER('test@foo.bar'), 'user')
            self.assertEqual(obs, exp1)
            obs = UTIL.generate_study_list(USER('shared@foo.bar'), 'user')
            self.assertEqual(obs, exp_both)
            # for admin it should be shown in public and user cause there are
            # 2 preps and only one is public
            obs = UTIL.generate_study_list(USER('admin@foo.bar'), 'user')
            if not all_artifacts:
                self.assertEqual(obs, exp_both)
            else:
                self.assertEqual(obs, exp2)
            obs = UTIL.generate_study_list(USER('demo@microbio.me'), 'user')
            self.assertEqual(obs, [])
            # for the public query, everything should be same for owner, share
            # and admin but demo should now see it as public but with limited
            # artifacts
            obs = UTIL.generate_study_list(USER('test@foo.bar'), 'public')
            self.assertEqual(obs, [])
            obs = UTIL.generate_study_list(USER('shared@foo.bar'), 'public')
            self.assertEqual(obs, [])
            obs = UTIL.generate_study_list(USER('admin@foo.bar'), 'public')
            if not all_artifacts:
                exp1[0]['artifact_biom_ids'] = [7]
            self.assertEqual(obs, exp1)
            obs = UTIL.generate_study_list(USER('demo@microbio.me'), 'public')
            self.assertEqual(obs, exp1)

            # returning artifacts
            exp1[0]['artifact_biom_ids'] = [4, 5, 6, 7]

        # make artifacts of prep 2 public
        PREP(2).artifact.visibility = 'public'
        exp1[0]['status'] = 'public'
        exp_both[0]['status'] = 'public'
        _avoid_duplicated_tests()

        # make artifacts of prep 1 awaiting_approval
        PREP(1).artifact.visibility = 'awaiting_approval'
        _avoid_duplicated_tests()

        # making all studies public
        PREP(1).artifact.visibility = 'public'
        _avoid_duplicated_tests(True)

        # deleting the new study study and returning artifact status
        qdb.study.Study.delete(new_study.id)
        PREP(1).artifact.visibility = 'private'
        PREP(2).artifact.visibility = 'private'

    def test_generate_study_list_errors(self):
        with self.assertRaises(ValueError):
            qdb.util.generate_study_list(qdb.user.User('test@foo.bar'), 'bad')

    def test_generate_study_list_without_artifacts(self):
        # creating a new study to make sure that empty studies are also
        # returned
        info = {"timeseries_type_id": 1, "metadata_complete": True,
                "mixs_compliant": True, "number_samples_collected": 25,
                "number_samples_promised": 28, "study_alias": "TST",
                "study_description": "Some description of the study goes here",
                "study_abstract": "Some abstract goes here",
                "emp_person_id": qdb.study.StudyPerson(1),
                "principal_investigator_id": qdb.study.StudyPerson(1),
                "lab_person_id": qdb.study.StudyPerson(1)}
        new_study = qdb.study.Study.create(
            qdb.user.User('shared@foo.bar'), 'test_study_1', info=info)

        exp_info = [
            {'status': 'private', 'study_title': (
                'Identification of the Microbiomes for Cannabis Soils'),
             'metadata_complete': True, 'publication_pid': [
                '123456', '7891011'], 'ebi_submission_status': 'submitted',
             'study_id': 1, 'ebi_study_accession': 'EBI123456-BB',
             'study_abstract': (
                'This is a preliminary study to examine the microbiota '
                'associated with the Cannabis plant. Soils samples from '
                'the bulk soil, soil associated with the roots, and the '
                'rhizosphere were extracted and the DNA sequenced. Roots '
                'from three independent plants of different strains were '
                'examined. These roots were obtained November 11, 2011 from '
                'plants that had been harvested in the summer. Future studies '
                'will attempt to analyze the soils and rhizospheres from the '
                'same location at different time points in the plant '
                'lifecycle.'), 'pi': ('PI_dude@foo.bar', 'PIDude'),
             'publication_doi': ['10.100/123456', '10.100/7891011'],
             'study_alias': 'Cannabis Soils', 'number_samples_collected': 27},
            {'status': 'sandbox', 'study_title': 'test_study_1',
             'metadata_complete': True, 'publication_pid': [],
             'ebi_submission_status': 'not submitted',
             'study_id': new_study.id, 'ebi_study_accession': None,
             'study_abstract': 'Some abstract goes here',
             'pi': ('lab_dude@foo.bar', 'LabDude'), 'publication_doi': [],
             'study_alias': 'TST', 'number_samples_collected': 0}]
        obs_info = qdb.util.generate_study_list_without_artifacts([1, 2, 3, 4])
        self.assertEqual(obs_info, exp_info)

        obs_info = qdb.util.generate_study_list_without_artifacts(
            [1, 2, 3, 4], 'EMP')
        self.assertEqual(obs_info, [])

        # deleting the old study
        qdb.study.Study.delete(new_study.id)

    def test_get_artifacts_information(self):
        # we are gonna test that it ignores 1 and 2 cause they are not biom,
        # 4 has all information and 7 and 8 don't
        obs = qdb.util.get_artifacts_information([1, 2, 4, 7, 8])
        # not testing timestamp
        for i in range(len(obs)):
            del obs[i]['timestamp']

        exp = [
            {'files': ['1_study_1001_closed_reference_otu_table.biom'],
             'artifact_id': 4, 'data_type': '18S', 'target_gene': '16S rRNA',
             'name': 'BIOM', 'target_subfragment': ['V4'],
             'parameters': {
                'reference': '1', 'similarity': '0.97',
                'sortmerna_e_value': '1', 'sortmerna_max_pos': '10000',
                'threads': '1', 'sortmerna_coverage': '0.97'},
             'algorithm': 'Pick closed-reference OTUs | Split libraries FASTQ',
             'algorithm_az': 'd480799a0a7a2fbe0e9022bc9c602018',
             'platform': 'Illumina', 'prep_samples': 27},
            {'files': [], 'artifact_id': 7, 'data_type': '16S',
             'target_gene': '16S rRNA', 'name': 'BIOM',
             'target_subfragment': ['V4'], 'parameters': {}, 'algorithm': '',
             'algorithm_az': '', 'platform': 'Illumina', 'prep_samples': 27},
            {'files': ['biom_table.biom'], 'artifact_id': 8,
             'data_type': '18S', 'target_gene': 'not provided',
             'name': 'noname', 'target_subfragment': [], 'parameters': {},
             'algorithm': '', 'algorithm_az': '', 'platform': 'not provided',
             'prep_samples': 0}]
        self.assertItemsEqual(obs, exp)

        # now let's test that the order given by the commands actually give the
        # correct results
        with qdb.sql_connection.TRN:
            # setting up database changes for just checking commands
            qdb.sql_connection.TRN.add(
                """UPDATE qiita.command_parameter SET check_biom_merge = True
                   WHERE parameter_name = 'reference'""")
            qdb.sql_connection.TRN.execute()

            # testing that it works as expected
            obs = qdb.util.get_artifacts_information([1, 2, 4, 7, 8])
            # not testing timestamp
            for i in range(len(obs)):
                del obs[i]['timestamp']
            exp[0]['algorithm'] = ('Pick closed-reference OTUs (reference: 1) '
                                   '| Split libraries FASTQ')
            exp[0]['algorithm_az'] = '33fed1b35728417d7ba4139b8f817d44'
            self.assertItemsEqual(obs, exp)

            # setting up database changes for also command output
            qdb.sql_connection.TRN.add(
                "UPDATE qiita.command_output SET check_biom_merge = True")
            qdb.sql_connection.TRN.execute()
            obs = qdb.util.get_artifacts_information([1, 2, 4, 7, 8])
            # not testing timestamp
            for i in range(len(obs)):
                del obs[i]['timestamp']
            exp[0]['algorithm'] = ('Pick closed-reference OTUs (reference: 1, '
                                   'BIOM: 1_study_1001_closed_reference_'
                                   'otu_table.biom) | Split libraries FASTQ')
            exp[0]['algorithm_az'] = 'de5b794a2cacd428f36fea86df196bfd'
            self.assertItemsEqual(obs, exp)

            # let's test that we ignore the parent_info
            qdb.sql_connection.TRN.add("""UPDATE qiita.software_command
                                          SET ignore_parent_command = True""")
            qdb.sql_connection.TRN.execute()
            obs = qdb.util.get_artifacts_information([1, 2, 4, 7, 8])
            # not testing timestamp
            for i in range(len(obs)):
                del obs[i]['timestamp']
            exp[0]['algorithm'] = ('Pick closed-reference OTUs (reference: 1, '
                                   'BIOM: 1_study_1001_closed_reference_'
                                   'otu_table.biom)')
            exp[0]['algorithm_az'] = '7f59a45b2f0d30cd1ed1929391c26e07'
            self.assertItemsEqual(obs, exp)

            # let's test that we ignore the parent_info
            qdb.sql_connection.TRN.add("""UPDATE qiita.software_command
                                          SET ignore_parent_command = True""")
            qdb.sql_connection.TRN.execute()
            obs = qdb.util.get_artifacts_information([1, 2, 4, 7, 8])
            # not testing timestamp
            for i in range(len(obs)):
                del obs[i]['timestamp']
            exp[0]['algorithm'] = ('Pick closed-reference OTUs (reference: 1, '
                                   'BIOM: 1_study_1001_closed_reference_'
                                   'otu_table.biom)')
            exp[0]['algorithm_az'] = (
                'PickclosedreferenceOTUsreferenceBIOMstudyclosedreference'
                'otutablebiom')
            self.assertItemsEqual(obs, exp)

            # returning database as it was
            qdb.sql_connection.TRN.add(
                "UPDATE qiita.command_output SET check_biom_merge = False")
            qdb.sql_connection.TRN.add("""UPDATE qiita.software_command
                                          SET ignore_parent_command = False""")
            qdb.sql_connection.TRN.add(
                """UPDATE qiita.command_parameter SET check_biom_merge = False
                   WHERE parameter_name = 'reference'""")
            qdb.sql_connection.TRN.execute()


class TestFilePathOpening(TestCase):
    """Tests adapted from scikit-bio's skbio.io.util tests"""
    def test_is_string_or_bytes(self):
        self.assertTrue(qdb.util._is_string_or_bytes('foo'))
        self.assertTrue(qdb.util._is_string_or_bytes(u'foo'))
        self.assertTrue(qdb.util._is_string_or_bytes(b'foo'))
        self.assertFalse(qdb.util._is_string_or_bytes(StringIO('bar')))
        self.assertFalse(qdb.util._is_string_or_bytes([1]))

    def test_file_closed(self):
        """File gets closed in decorator"""
        f = NamedTemporaryFile('r')
        filepath = f.name
        with qdb.util.open_file(filepath) as fh:
            pass
        self.assertTrue(fh.closed)

    def test_file_closed_harder(self):
        """File gets closed in decorator, even if exceptions happen."""
        f = NamedTemporaryFile('r')
        filepath = f.name
        try:
            with qdb.util.open_file(filepath) as fh:
                raise TypeError
        except TypeError:
            self.assertTrue(fh.closed)
        else:
            # If we're here, no exceptions have been raised inside the
            # try clause, so the context manager swallowed them. No
            # good.
            raise Exception("`open_file` didn't propagate exceptions")

    def test_filehandle(self):
        """Filehandles slip through untouched"""
        with TemporaryFile('r') as fh:
            with qdb.util.open_file(fh) as ffh:
                self.assertTrue(fh is ffh)
            # And it doesn't close the file-handle
            self.assertFalse(fh.closed)

    def test_StringIO(self):
        """StringIO (useful e.g. for testing) slips through."""
        f = StringIO("File contents")
        with qdb.util.open_file(f) as fh:
            self.assertTrue(fh is f)

    def test_BytesIO(self):
        """BytesIO (useful e.g. for testing) slips through."""
        f = BytesIO(b"File contents")
        with qdb.util.open_file(f) as fh:
            self.assertTrue(fh is f)

    def test_hdf5IO(self):
        f = h5py.File('test', driver='core', backing_store=False)
        with qdb.util.open_file(f) as fh:
            self.assertTrue(fh is f)

    def test_hdf5IO_open(self):
        name = None
        with NamedTemporaryFile(delete=False) as fh:
            name = fh.name
            fh.close()

            h5file = h5py.File(name, 'w')
            h5file.close()

            with qdb.util.open_file(name) as fh_inner:
                self.assertTrue(isinstance(fh_inner, h5py.File))

        remove(name)


if __name__ == '__main__':
    main()
