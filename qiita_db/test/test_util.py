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
from os.path import join, exists, basename
from shutil import rmtree

import pandas as pd

from qiita_core.util import qiita_test_checker
from qiita_core.exceptions import IncompetentQiitaDeveloperError
from qiita_db.exceptions import QiitaDBColumnError, QiitaDBError
from qiita_db.data import RawData
from qiita_db.study import Study
from qiita_db.reference import Reference
from qiita_db.metadata_template import PrepTemplate
from qiita_db.util import (exists_table, exists_dynamic_table, scrub_data,
                           compute_checksum, check_table_cols,
                           check_required_columns, convert_to_id,
                           get_table_cols, get_table_cols_w_type,
                           get_filetypes, get_filepath_types, get_count,
                           check_count, get_processed_params_tables,
                           params_dict_to_json, insert_filepaths,
                           get_db_files_base_dir, get_data_types,
                           purge_filepaths, get_filepath_id,
                           get_lat_longs, get_mountpoint,
                           get_mountpoint_path_by_id,
                           get_files_from_uploads_folders,
                           get_environmental_packages, get_timeseries_types,
                           filepath_id_to_rel_path, filepath_ids_to_rel_paths,
                           move_filepaths_to_upload_folder,
                           move_upload_files_to_trash,
                           check_access_to_analysis_result, infer_status,
                           get_preprocessed_params_tables)


@qiita_test_checker()
class DBUtilTests(TestCase):
    def setUp(self):
        self.table = 'study'
        self.required = [
            'number_samples_promised', 'study_title', 'mixs_compliant',
            'metadata_complete', 'study_description', 'first_contact',
            'reprocess', 'portal_type_id', 'timeseries_type_id', 'study_alias',
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
        self.assertEqual(params_dict_to_json(params_dict), exp)

    def test_check_required_columns(self):
        # Doesn't do anything if correct info passed, only errors if wrong info
        check_required_columns(self.required, self.table)

    def test_check_required_columns_fail(self):
        self.required.remove('study_title')
        with self.assertRaises(QiitaDBColumnError):
            check_required_columns(self.required, self.table)

    def test_get_lat_longs(self):
        exp = [
            [74.0894932572, 65.3283470202],
            [57.571893782, 32.5563076447],
            [13.089194595, 92.5274472082],
            [12.7065957714, 84.9722975792],
            [31.7167821863, 95.5088566087],
            [44.9725384282, 66.1920014699],
            [10.6655599093, 70.784770579],
            [29.1499460692, 82.1270418227],
            [35.2374368957, 68.5041623253],
            [53.5050692395, 31.6056761814],
            [60.1102854322, 74.7123248382],
            [4.59216095574, 63.5115213108],
            [68.0991287718, 34.8360987059],
            [84.0030227585, 66.8954849864],
            [3.21190859967, 26.8138925876],
            [82.8302905615, 86.3615778099],
            [12.6245524972, 96.0693176066],
            [85.4121476399, 15.6526750776],
            [63.6505562766, 31.2003474585],
            [23.1218032799, 42.838497795],
            [43.9614715197, 82.8516734159],
            [68.51099627, 2.35063674718],
            [0.291867635913, 68.5945325743],
            [40.8623799474, 6.66444220187],
            [95.2060749748, 27.3592668624],
            [78.3634273709, 74.423907894],
            [38.2627021402, 3.48274264219]]

        obs = get_lat_longs()
        self.assertItemsEqual(obs, exp)

    def test_check_table_cols(self):
        # Doesn't do anything if correct info passed, only errors if wrong info
        check_table_cols(self.required, self.table)

    def test_check_table_cols_fail(self):
        self.required.append('BADTHINGNOINHERE')
        with self.assertRaises(QiitaDBColumnError):
            check_table_cols(self.required, self.table)

    def test_get_table_cols(self):
        obs = get_table_cols("qiita_user")
        exp = {"email", "user_level_id", "password", "name", "affiliation",
               "address", "phone", "user_verify_code", "pass_reset_code",
               "pass_reset_timestamp"}
        self.assertEqual(set(obs), exp)

    def test_get_table_cols_w_type(self):
        obs = get_table_cols_w_type("preprocessed_sequence_illumina_params")
        exp = [['param_set_name', 'character varying'],
               ['preprocessed_params_id', 'bigint'],
               ['max_bad_run_length', 'integer'],
               ['min_per_read_length_fraction', 'real'],
               ['sequence_max_n', 'integer'],
               ['rev_comp_barcode', 'boolean'],
               ['rev_comp_mapping_barcodes', 'boolean'],
               ['rev_comp', 'boolean'],
               ['phred_quality_threshold', 'integer'],
               ['barcode_type', 'character varying'],
               ['max_barcode_errors', 'real']]
        self.assertItemsEqual(obs, exp)

    def test_exists_table(self):
        """Correctly checks if a table exists"""
        # True cases
        self.assertTrue(exists_table("filepath"))
        self.assertTrue(exists_table("qiita_user"))
        self.assertTrue(exists_table("analysis"))
        self.assertTrue(exists_table("prep_1"))
        self.assertTrue(exists_table("sample_1"))
        # False cases
        self.assertFalse(exists_table("sample_2"))
        self.assertFalse(exists_table("prep_2"))
        self.assertFalse(exists_table("foo_table"))
        self.assertFalse(exists_table("bar_table"))

    def test_exists_dynamic_table(self):
        """Correctly checks if a dynamic table exists"""
        # True cases
        self.assertTrue(exists_dynamic_table(
            "preprocessed_sequence_illumina_params", "preprocessed_",
            "_params"))
        self.assertTrue(exists_dynamic_table("prep_1", "prep_", ""))
        self.assertTrue(exists_dynamic_table("filepath", "", ""))
        # False cases
        self.assertFalse(exists_dynamic_table(
            "preprocessed_foo_params", "preprocessed_", "_params"))
        self.assertFalse(exists_dynamic_table(
            "preprocessed__params", "preprocessed_", "_params"))
        self.assertFalse(exists_dynamic_table(
            "foo_params", "preprocessed_", "_params"))
        self.assertFalse(exists_dynamic_table(
            "preprocessed_foo", "preprocessed_", "_params"))
        self.assertFalse(exists_dynamic_table(
            "foo", "preprocessed_", "_params"))

    def test_convert_to_id(self):
        """Tests that ids are returned correctly"""
        self.assertEqual(convert_to_id("directory", "filepath_type"), 8)
        self.assertEqual(convert_to_id("running", "analysis_status",
                                       "status"), 3)
        self.assertEqual(convert_to_id("EMP", "portal_type", "portal"), 2)

    def test_convert_to_id_bad_value(self):
        """Tests that ids are returned correctly"""
        with self.assertRaises(IncompetentQiitaDeveloperError):
            convert_to_id("FAKE", "filepath_type")

    def test_get_filetypes(self):
        """Tests that get_filetypes works with valid arguments"""

        obs = get_filetypes()
        exp = {'SFF': 1, 'FASTA_Sanger': 2, 'FASTQ': 3, 'FASTA': 4,
               'per_sample_FASTQ': 5}
        self.assertEqual(obs, exp)

        obs = get_filetypes(key='filetype_id')
        exp = {v: k for k, v in exp.items()}
        self.assertEqual(obs, exp)

    def test_get_filetypes_fail(self):
        """Tests that get_Filetypes fails with invalid argument"""
        with self.assertRaises(QiitaDBColumnError):
            get_filetypes(key='invalid')

    def test_get_filepath_types(self):
        """Tests that get_filepath_types works with valid arguments"""
        obs = get_filepath_types()
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

        obs = get_filepath_types(key='filepath_type_id')
        exp = {v: k for k, v in exp.items()}
        self.assertEqual(obs, exp)

    def test_get_filepath_types_fail(self):
        """Tests that get_Filetypes fails with invalid argument"""
        with self.assertRaises(QiitaDBColumnError):
            get_filepath_types(key='invalid')

    def test_get_data_types(self):
        """Tests that get_data_types works with valid arguments"""
        obs = get_data_types()
        exp = {'16S': 1, '18S': 2, 'ITS': 3, 'Proteomic': 4, 'Metabolomic': 5,
               'Metagenomic': 6}
        self.assertEqual(obs, exp)

        obs = get_data_types(key='data_type_id')
        exp = {v: k for k, v in exp.items()}
        self.assertEqual(obs, exp)

    def test_get_count(self):
        """Checks that get_count retrieves proper count"""
        self.assertEqual(get_count('qiita.study_person'), 3)

    def test_check_count(self):
        """Checks that check_count returns True and False appropriately"""
        self.assertTrue(check_count('qiita.study_person', 3))
        self.assertFalse(check_count('qiita.study_person', 2))

    def test_get_preprocessed_params_tables(self):
        obs = get_preprocessed_params_tables()
        exp = ['preprocessed_sequence_454_params',
               'preprocessed_sequence_illumina_params',
               'preprocessed_spectra_params']
        self.assertEqual(obs, exp)

    def test_get_processed_params_tables(self):
        obs = get_processed_params_tables()
        self.assertEqual(obs, ['processed_params_sortmerna',
                               'processed_params_uclust'])

    def test_insert_filepaths(self):
        fd, fp = mkstemp()
        close(fd)
        with open(fp, "w") as f:
            f.write("\n")
        self.files_to_remove.append(fp)

        exp_new_id = 1 + self.conn_handler.execute_fetchone(
            "SELECT count(1) FROM qiita.filepath")[0]
        obs = insert_filepaths([(fp, 1)], 1, "raw_data", "filepath")
        self.assertEqual(obs, [exp_new_id])

        # Check that the files have been copied correctly
        exp_fp = join(get_db_files_base_dir(), "raw_data",
                      "1_%s" % basename(fp))
        self.assertTrue(exists(exp_fp))
        self.files_to_remove.append(exp_fp)

        # Check that the filepaths have been added to the DB
        obs = self.conn_handler.execute_fetchall(
            "SELECT * FROM qiita.filepath WHERE filepath_id=%d" % exp_new_id)
        exp_fp = "1_%s" % basename(fp)
        exp = [[exp_new_id, exp_fp, 1, '852952723', 1, 5]]
        self.assertEqual(obs, exp)

    def test_insert_filepaths_string(self):
        fd, fp = mkstemp()
        close(fd)
        with open(fp, "w") as f:
            f.write("\n")
        self.files_to_remove.append(fp)

        exp_new_id = 1 + self.conn_handler.execute_fetchone(
            "SELECT count(1) FROM qiita.filepath")[0]
        obs = insert_filepaths([(fp, "raw_forward_seqs")], 1, "raw_data",
                               "filepath")
        self.assertEqual(obs, [exp_new_id])

        # Check that the files have been copied correctly
        exp_fp = join(get_db_files_base_dir(), "raw_data",
                      "1_%s" % basename(fp))
        self.assertTrue(exists(exp_fp))
        self.files_to_remove.append(exp_fp)

        # Check that the filepaths have been added to the DB
        obs = self.conn_handler.execute_fetchall(
            "SELECT * FROM qiita.filepath WHERE filepath_id=%d" % exp_new_id)
        exp_fp = "1_%s" % basename(fp)
        exp = [[exp_new_id, exp_fp, 1, '852952723', 1, 5]]
        self.assertEqual(obs, exp)

    def _common_purge_filpeaths_test(self):
        # Get all the filepaths so we can test if they've been removed or not
        sql_fp = "SELECT filepath, data_directory_id FROM qiita.filepath"
        fps = [join(get_mountpoint_path_by_id(dd_id), fp) for fp, dd_id in
               self.conn_handler.execute_fetchall(sql_fp)]

        # Make sure that the files exist - specially for travis
        for fp in fps:
            if not exists(fp):
                with open(fp, 'w') as f:
                    f.write('\n')
                self.files_to_remove.append(fp)

        _, raw_data_mp = get_mountpoint('raw_data')[0]

        removed_fps = [
            join(raw_data_mp, '2_sequences_barcodes.fastq.gz'),
            join(raw_data_mp, '2_sequences.fastq.gz')]

        for fp in removed_fps:
            with open(fp, 'w') as f:
                f.write('\n')

        sql = """INSERT INTO qiita.filepath
                    (filepath, filepath_type_id, checksum,
                     checksum_algorithm_id, data_directory_id)
                VALUES ('2_sequences_barcodes.fastq.gz', 3, '852952723', 1, 5),
                       ('2_sequences.fastq.gz', 1, '852952723', 1, 5)
                RETURNING filepath_id"""
        fp_ids = self.conn_handler.execute_fetchall(sql)

        fps = set(fps).difference(removed_fps)

        # Check that the files exist
        for fp in fps:
            self.assertTrue(exists(fp))
        for fp in removed_fps:
            self.assertTrue(exists(fp))

        exp_count = get_count("qiita.filepath") - 2

        purge_filepaths()

        obs_count = get_count("qiita.filepath")

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
        self._common_purge_filpeaths_test()

    def test_purge_filepaths_null_cols(self):
        # For more details about the source of the issue that motivates this
        # test: http://www.depesz.com/2008/08/13/nulls-vs-not-in/
        # In the current set up, the only place where we can actually have a
        # null value in a filepath id is in the reference table. Add a new
        # reference without tree and taxonomy:
        fd, seqs_fp = mkstemp(suffix="_seqs.fna")
        close(fd)
        ref = Reference.create("null_db", "13_2", seqs_fp)
        self.files_to_remove.append(ref.sequence_fp)

        self._common_purge_filpeaths_test()

    def test_move_filepaths_to_upload_folder(self):
        # setting up test, done here as this is the only test that uses these
        # files
        fd, seqs_fp = mkstemp(suffix='_seqs.fastq')
        close(fd)
        st = Study(1)
        metadata_dict = {
            'SKB8.640193': {'center_name': 'ANL',
                            'primer': 'GTGCCAGCMGCCGCGGTAA',
                            'barcode': 'GTCCGCAAGTTA',
                            'run_prefix': "s_G1_L001_sequences",
                            'platform': 'ILLUMINA',
                            'library_construction_protocol': 'AAAA',
                            'experiment_design_description': 'BBBB'}}
        metadata = pd.DataFrame.from_dict(metadata_dict, orient='index')
        pt = PrepTemplate.create(metadata, Study(1), "16S")

        rd = RawData.create(2, [pt], [(seqs_fp, 1)])
        filepaths = rd.get_filepaths()
        # deleting reference so we can directly call
        # move_filepaths_to_upload_folder
        for fid, _, _ in filepaths:
            self.conn_handler.execute(
                "DELETE FROM qiita.raw_filepath WHERE filepath_id=%s", (fid,))

        # moving filepaths
        move_filepaths_to_upload_folder(st.id, filepaths)

        # check that they do not exist in the old path but do in the new one
        path_for_removal = join(get_mountpoint("uploads")[0][1], str(st.id))
        for _, fp, _ in filepaths:
            self.assertFalse(exists(fp))
            new_fp = join(path_for_removal, basename(fp).split('_', 1)[1])
            self.assertTrue(exists(new_fp))

            self.files_to_remove.append(new_fp)

    def test_get_filepath_id(self):
        _, base = get_mountpoint("raw_data")[0]
        fp = join(base, '1_s_G1_L001_sequences.fastq.gz')
        obs = get_filepath_id("raw_data", fp)
        self.assertEqual(obs, 1)

    def test_get_filepath_id_error(self):
        with self.assertRaises(QiitaDBError):
            get_filepath_id("raw_data", "Not_a_path")

    def test_get_mountpoint(self):
        exp = [(5, join(get_db_files_base_dir(), 'raw_data', ''))]
        obs = get_mountpoint("raw_data")
        self.assertEqual(obs, exp)

        exp = [(1, join(get_db_files_base_dir(), 'analysis', ''))]
        obs = get_mountpoint("analysis")
        self.assertEqual(obs, exp)

        exp = [(2, join(get_db_files_base_dir(), 'job', ''))]
        obs = get_mountpoint("job")
        self.assertEqual(obs, exp)

        # inserting new ones so we can test that it retrieves these and
        # doesn't alter other ones
        self.conn_handler.execute(
            "UPDATE qiita.data_directory SET active=false WHERE "
            "data_directory_id=1")
        self.conn_handler.execute(
            "INSERT INTO qiita.data_directory (data_type, mountpoint, "
            "subdirectory, active) VALUES ('analysis', 'analysis', 'tmp', "
            "true), ('raw_data', 'raw_data', 'tmp', false)")

        # this should have been updated
        exp = [(10, join(get_db_files_base_dir(), 'analysis', 'tmp'))]
        obs = get_mountpoint("analysis")
        self.assertEqual(obs, exp)

        # these 2 shouldn't
        exp = [(5, join(get_db_files_base_dir(), 'raw_data', ''))]
        obs = get_mountpoint("raw_data")
        self.assertEqual(obs, exp)

        exp = [(2, join(get_db_files_base_dir(), 'job', ''))]
        obs = get_mountpoint("job")
        self.assertEqual(obs, exp)

        # testing multi returns
        exp = [(5, join(get_db_files_base_dir(), 'raw_data', '')),
               (11, join(get_db_files_base_dir(), 'raw_data', 'tmp'))]
        obs = get_mountpoint("raw_data", retrieve_all=True)
        self.assertEqual(obs, exp)

    def test_get_mountpoint_path_by_id(self):
        exp = join(get_db_files_base_dir(), 'raw_data', '')
        obs = get_mountpoint_path_by_id(5)
        self.assertEqual(obs, exp)

        exp = join(get_db_files_base_dir(), 'analysis', '')
        obs = get_mountpoint_path_by_id(1)
        self.assertEqual(obs, exp)

        exp = join(get_db_files_base_dir(), 'job', '')
        obs = get_mountpoint_path_by_id(2)
        self.assertEqual(obs, exp)

        # inserting new ones so we can test that it retrieves these and
        # doesn't alter other ones
        self.conn_handler.execute(
            "UPDATE qiita.data_directory SET active=false WHERE "
            "data_directory_id=1")
        self.conn_handler.execute(
            "INSERT INTO qiita.data_directory (data_type, mountpoint, "
            "subdirectory, active) VALUES ('analysis', 'analysis', 'tmp', "
            "true), ('raw_data', 'raw_data', 'tmp', false)")

        # this should have been updated
        exp = join(get_db_files_base_dir(), 'analysis', 'tmp')
        obs = get_mountpoint_path_by_id(10)
        self.assertEqual(obs, exp)

        # these 2 shouldn't
        exp = join(get_db_files_base_dir(), 'raw_data', '')
        obs = get_mountpoint_path_by_id(5)
        self.assertEqual(obs, exp)

        exp = join(get_db_files_base_dir(), 'job', '')
        obs = get_mountpoint_path_by_id(2)
        self.assertEqual(obs, exp)

    def test_get_files_from_uploads_folders(self):
        # something has been uploaded and ignoring hidden files/folders
        # and folders
        exp = [(7, 'uploaded_file.txt')]
        obs = get_files_from_uploads_folders("1")
        self.assertEqual(obs, exp)

        # nothing has been uploaded
        exp = []
        obs = get_files_from_uploads_folders("2")
        self.assertEqual(obs, exp)

    def test_move_upload_files_to_trash(self):
        test_filename = 'this_is_a_test_file.txt'

        # create file to move to trash
        fid, folder = get_mountpoint("uploads")[0]
        test_fp = join(folder, '1', test_filename)
        with open(test_fp, 'w') as f:
            f.write('test')

        self.files_to_remove.append(test_fp)

        exp = [(fid, 'this_is_a_test_file.txt'), (fid, 'uploaded_file.txt')]
        obs = get_files_from_uploads_folders("1")
        self.assertItemsEqual(obs, exp)

        # move file
        move_upload_files_to_trash(1, [(fid, test_filename)])
        exp = [(fid, 'uploaded_file.txt')]
        obs = get_files_from_uploads_folders("1")
        self.assertItemsEqual(obs, exp)

        # testing errors
        with self.assertRaises(QiitaDBError):
            move_upload_files_to_trash(2, [(fid, test_filename)])
        with self.assertRaises(QiitaDBError):
            move_upload_files_to_trash(1, [(10, test_filename)])
        with self.assertRaises(QiitaDBError):
            move_upload_files_to_trash(1, [(fid, test_filename)])

        # removing trash folder
        rmtree(join(folder, '1', 'trash'))

    def test_get_environmental_packages(self):
        obs = get_environmental_packages()
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
        obs = get_timeseries_types()
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

    def test_filepath_id_to_rel_path(self):
        obs = filepath_id_to_rel_path(1)
        exp = 'raw_data/1_s_G1_L001_sequences.fastq.gz'
        self.assertEqual(obs, exp)

        obs = filepath_id_to_rel_path(3)
        exp = 'preprocessed_data/1_seqs.fna'
        self.assertEqual(obs, exp)

    def test_filepath_ids_to_rel_paths(self):
        obs = filepath_ids_to_rel_paths([1, 3])
        exp = {1: 'raw_data/1_s_G1_L001_sequences.fastq.gz',
               3: 'preprocessed_data/1_seqs.fna'}

        self.assertEqual(obs, exp)

    def test_check_access_to_analysis_result(self):
        obs = check_access_to_analysis_result('test@foo.bar',
                                              '1_job_result.txt')
        exp = [10]

        self.assertEqual(obs, exp)


class UtilTests(TestCase):
    """Tests for the util functions that do not need to access the DB"""

    def setUp(self):
        fh, self.filepath = mkstemp()
        close(fh)
        with open(self.filepath, "w") as f:
            f.write("Some text so we can actually compute a checksum")

    def test_compute_checksum(self):
        """Correctly returns the file checksum"""
        obs = compute_checksum(self.filepath)
        exp = 1719580229
        self.assertEqual(obs, exp)

    def test_scrub_data_nothing(self):
        """Returns the same string without changes"""
        self.assertEqual(scrub_data("nothing_changes"), "nothing_changes")

    def test_scrub_data_semicolon(self):
        """Correctly removes the semicolon from the string"""
        self.assertEqual(scrub_data("remove_;_char"), "remove__char")

    def test_scrub_data_single_quote(self):
        """Correctly removes single quotes from the string"""
        self.assertEqual(scrub_data("'quotes'"), "quotes")

    def test_infer_status(self):
        obs = infer_status([])
        self.assertEqual(obs, 'sandbox')

        obs = infer_status([['private']])
        self.assertEqual(obs, 'private')

        obs = infer_status([['private'], ['public']])
        self.assertEqual(obs, 'public')

        obs = infer_status([['sandbox'], ['awaiting_approval']])
        self.assertEqual(obs, 'awaiting_approval')

        obs = infer_status([['sandbox'], ['sandbox']])
        self.assertEqual(obs, 'sandbox')

if __name__ == '__main__':
    main()
