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

from qiita_core.util import qiita_test_checker
from qiita_core.exceptions import IncompetentQiitaDeveloperError
from qiita_db.exceptions import QiitaDBColumnError, QiitaDBError
from qiita_db.util import (exists_table, exists_dynamic_table, scrub_data,
                           compute_checksum, check_table_cols,
                           check_required_columns, convert_to_id,
                           get_table_cols, get_table_cols_w_type,
                           get_filetypes, get_filepath_types, get_count,
                           check_count, get_processed_params_tables,
                           params_dict_to_json, insert_filepaths,
                           get_db_files_base_dir, get_data_types,
                           get_required_sample_info_status,
                           get_emp_status, purge_filepaths, get_filepath_id,
                           get_lat_longs, get_mountpoint,
                           get_files_from_uploads_folders,
                           get_environmental_packages, get_timeseries_types,
                           filepath_id_to_rel_path, find_repeated)


@qiita_test_checker()
class DBUtilTests(TestCase):
    def setUp(self):
        self.table = 'study'
        self.required = [
            'number_samples_promised', 'study_title', 'mixs_compliant',
            'metadata_complete', 'study_description', 'first_contact',
            'reprocess', 'study_status_id', 'portal_type_id',
            'timeseries_type_id', 'study_alias', 'study_abstract',
            'principal_investigator_id', 'email', 'number_samples_collected']
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
        check_required_columns(self.conn_handler, self.required, self.table)

    def test_check_required_columns_fail(self):
        self.required.remove('study_title')
        with self.assertRaises(QiitaDBColumnError):
            check_required_columns(self.conn_handler, self.required,
                                   self.table)

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
        self.assertEqual(obs, exp)

    def test_check_table_cols(self):
        # Doesn't do anything if correct info passed, only errors if wrong info
        check_table_cols(self.conn_handler, self.required, self.table)

    def test_check_table_cols_fail(self):
        self.required.append('BADTHINGNOINHERE')
        with self.assertRaises(QiitaDBColumnError):
            check_table_cols(self.conn_handler, self.required,
                             self.table)

    def test_get_table_cols(self):
        obs = get_table_cols("qiita_user", self.conn_handler)
        exp = {"email", "user_level_id", "password", "name", "affiliation",
               "address", "phone", "user_verify_code", "pass_reset_code",
               "pass_reset_timestamp"}
        self.assertEqual(set(obs), exp)

    def test_get_table_cols_w_type(self):
        obs = get_table_cols_w_type("preprocessed_sequence_illumina_params",
                                    self.conn_handler)
        exp = [['preprocessed_params_id', 'bigint'],
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
        self.assertTrue(exists_table("filepath", self.conn_handler))
        self.assertTrue(exists_table("qiita_user", self.conn_handler))
        self.assertTrue(exists_table("analysis", self.conn_handler))
        self.assertTrue(exists_table("prep_1", self.conn_handler))
        self.assertTrue(exists_table("sample_1", self.conn_handler))
        # False cases
        self.assertFalse(exists_table("sample_2", self.conn_handler))
        self.assertFalse(exists_table("prep_2", self.conn_handler))
        self.assertFalse(exists_table("foo_table", self.conn_handler))
        self.assertFalse(exists_table("bar_table", self.conn_handler))

    def test_exists_dynamic_table(self):
        """Correctly checks if a dynamic table exists"""
        # True cases
        self.assertTrue(exists_dynamic_table(
            "preprocessed_sequence_illumina_params", "preprocessed_",
            "_params", self.conn_handler))
        self.assertTrue(exists_dynamic_table("prep_1", "prep_", "",
                                             self.conn_handler))
        self.assertTrue(exists_dynamic_table("filepath", "", "",
                                             self.conn_handler))
        # False cases
        self.assertFalse(exists_dynamic_table(
            "preprocessed_foo_params", "preprocessed_", "_params",
            self.conn_handler))
        self.assertFalse(exists_dynamic_table(
            "preprocessed__params", "preprocessed_", "_params",
            self.conn_handler))
        self.assertFalse(exists_dynamic_table(
            "foo_params", "preprocessed_", "_params",
            self.conn_handler))
        self.assertFalse(exists_dynamic_table(
            "preprocessed_foo", "preprocessed_", "_params",
            self.conn_handler))
        self.assertFalse(exists_dynamic_table(
            "foo", "preprocessed_", "_params",
            self.conn_handler))

    def test_convert_to_id(self):
        """Tests that ids are returned correctly"""
        self.assertEqual(convert_to_id("directory", "filepath_type"), 8)

    def test_convert_to_id_bad_value(self):
        """Tests that ids are returned correctly"""
        with self.assertRaises(IncompetentQiitaDeveloperError):
            convert_to_id("FAKE", "filepath_type")

    def test_get_filetypes(self):
        """Tests that get_filetypes works with valid arguments"""

        obs = get_filetypes()
        exp = {'SFF': 1, 'FASTA-Sanger': 2, 'FASTQ': 3}
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
               'sample_template': 14, 'prep_template': 15, 'qiime_map': 16}
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

    def test_get_required_sample_info_status(self):
        """Tests that get_required_sample_info_status works"""
        obs = get_required_sample_info_status()
        exp = {'received': 1, 'in_preparation': 2, 'running': 3,
               'completed': 4}
        self.assertEqual(obs, exp)

        obs = get_required_sample_info_status(
            key='required_sample_info_status_id')
        exp = {v: k for k, v in exp.items()}
        self.assertEqual(obs, exp)

    def test_get_emp_status(self):
        """Tests that get_emp_status works"""
        obs = get_emp_status()
        exp = {'EMP': 1, 'EMP_Processed': 2, 'NOT_EMP': 3}
        self.assertEqual(obs, exp)

        obs = get_emp_status(key='emp_status_id')
        exp = {v: k for k, v in exp.items()}
        self.assertEqual(obs, exp)

    def test_get_count(self):
        """Checks that get_count retrieves proper count"""
        self.assertEqual(get_count('qiita.study_person'), 3)

    def test_check_count(self):
        """Checks that check_count returns True and False appropriately"""
        self.assertTrue(check_count('qiita.study_person', 3))
        self.assertFalse(check_count('qiita.study_person', 2))

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

        obs = insert_filepaths([(fp, 1)], 1, "raw_data", "filepath",
                               self.conn_handler)
        exp = [17]
        self.assertEqual(obs, exp)

        # Check that the files have been copied correctly
        exp_fp = join(get_db_files_base_dir(), "raw_data",
                      "1_%s" % basename(fp))
        self.assertTrue(exists(exp_fp))
        self.files_to_remove.append(exp_fp)

        # Check that the filepaths have been added to the DB
        obs = self.conn_handler.execute_fetchall(
            "SELECT * FROM qiita.filepath WHERE filepath_id=17")
        exp_fp = "1_%s" % basename(fp)
        exp = [[17, exp_fp, 1, '852952723', 1, 5]]
        self.assertEqual(obs, exp)

    def test_insert_filepaths_string(self):
        fd, fp = mkstemp()
        close(fd)
        with open(fp, "w") as f:
            f.write("\n")
        self.files_to_remove.append(fp)

        obs = insert_filepaths([(fp, "raw_forward_seqs")], 1, "raw_data",
                               "filepath", self.conn_handler)
        exp = [17]
        self.assertEqual(obs, exp)

        # Check that the files have been copied correctly
        exp_fp = join(get_db_files_base_dir(), "raw_data",
                      "1_%s" % basename(fp))
        self.assertTrue(exists(exp_fp))
        self.files_to_remove.append(exp_fp)

        # Check that the filepaths have been added to the DB
        obs = self.conn_handler.execute_fetchall(
            "SELECT * FROM qiita.filepath WHERE filepath_id=17")
        exp_fp = "1_%s" % basename(fp)
        exp = [[17, exp_fp, 1, '852952723', 1, 5]]
        self.assertEqual(obs, exp)

    def test_insert_filepaths_queue(self):
        fd, fp = mkstemp()
        close(fd)
        with open(fp, "w") as f:
            f.write("\n")
        self.files_to_remove.append(fp)

        # create and populate queue
        self.conn_handler.create_queue("toy_queue")
        self.conn_handler.add_to_queue(
            "toy_queue", "INSERT INTO qiita.qiita_user (email, name, password,"
            "phone) VALUES (%s, %s, %s, %s)",
            ['insert@foo.bar', 'Toy', 'pass', '111-111-1111'])

        insert_filepaths([(fp, "raw_forward_seqs")], 1, "raw_data",
                         "filepath", self.conn_handler, queue='toy_queue')

        self.conn_handler.add_to_queue(
            "toy_queue", "INSERT INTO qiita.raw_filepath (raw_data_id, "
            "filepath_id) VALUES (1, %s)", ['{0}'])
        self.conn_handler.execute_queue("toy_queue")

        # check that the user was added to the DB
        obs = self.conn_handler.execute_fetchall(
            "SELECT * from qiita.qiita_user WHERE email = %s",
            ['insert@foo.bar'])
        exp = [['insert@foo.bar', 5, 'pass', 'Toy', None, None, '111-111-1111',
                None, None, None]]
        self.assertEqual(obs, exp)

        # Check that the filepaths have been added to the DB
        obs = self.conn_handler.execute_fetchall(
            "SELECT * FROM qiita.filepath WHERE filepath_id=17")
        exp_fp = "1_%s" % basename(fp)
        exp = [[17, exp_fp, 1, '852952723', 1, 5]]
        self.assertEqual(obs, exp)

        # check that raw_filpath data was added to the DB
        obs = self.conn_handler.execute_fetchall(
            "SELECT * FROM qiita.raw_filepath WHERE filepath_id=17")
        exp_fp = "1_%s" % basename(fp)
        exp = [[1, 17]]
        self.assertEqual(obs, exp)

    def test_purge_filepaths(self):
        # Add a new filepath to the database
        fd, fp = mkstemp()
        close(fd)
        fp_id = self.conn_handler.execute_fetchone(
            "INSERT INTO qiita.filepath "
            "(filepath, filepath_type_id, checksum, checksum_algorithm_id) "
            "VALUES (%s, %s, %s, %s) RETURNING filepath_id", (fp, 1, "", 1))[0]
        self.assertEqual(fp_id, 17)

        # Connect the just added filepath to a raw data
        self.conn_handler.execute(
            "INSERT INTO qiita.raw_filepath (raw_data_id, filepath_id) VALUES"
            "(%s, %s)", (1, 17))

        # Get the filepaths so we can test if they've been removed or not
        sql_fp = "SELECT filepath FROM qiita.filepath WHERE filepath_id=%s"
        fp1 = self.conn_handler.execute_fetchone(sql_fp, (1,))[0]
        fp1 = join(get_db_files_base_dir(), fp1)

        # Make sure that the file exists - specially for travis
        with open(fp1, 'w') as f:
            f.write('\n')

        fp17 = self.conn_handler.execute_fetchone(sql_fp, (17,))[0]
        fp17 = join(get_db_files_base_dir(), fp17)

        # Nothing should be removed
        purge_filepaths(self.conn_handler)

        sql_ids = ("SELECT filepath_id FROM qiita.filepath ORDER BY "
                   "filepath_id")
        obs = self.conn_handler.execute_fetchall(sql_ids)
        exp = [[1], [2], [3], [4], [5], [6], [7], [8], [9],
               [10], [11], [12], [13], [14], [15], [17]]
        self.assertEqual(obs, exp)

        # Check that the files still exist
        self.assertTrue(exists(fp1))
        self.assertTrue(exists(fp17))

        # Unlink the filepath from the raw data
        self.conn_handler.execute(
            "DELETE FROM qiita.raw_filepath WHERE filepath_id=%s", (17,))

        # Only filepath 16 should be removed
        purge_filepaths(self.conn_handler)

        obs = self.conn_handler.execute_fetchall(sql_ids)
        exp = [[1], [2], [3], [4], [5], [6], [7], [8], [9],
               [10], [11], [12], [13], [14], [15]]
        self.assertEqual(obs, exp)

        # Check that only the file for the removed filepath has been removed
        self.assertTrue(exists(fp1))
        self.assertFalse(exists(fp17))

    def test_get_filepath_id(self):
        _, base = get_mountpoint("raw_data")[0]
        fp = join(base, '1_s_G1_L001_sequences.fastq.gz')
        obs = get_filepath_id("raw_data", fp, self.conn_handler)
        self.assertEqual(obs, 1)

    def test_get_filepath_id_error(self):
        with self.assertRaises(QiitaDBError):
            get_filepath_id("raw_data", "Not_a_path", self.conn_handler)

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
        obs = get_mountpoint("raw_data", retrive_all=True)
        self.assertEqual(obs, exp)

    def test_get_files_from_uploads_folders(self):
        # something has been uploaded
        exp = ['uploaded_file.txt']
        obs = get_files_from_uploads_folders("1")
        self.assertEqual(obs, exp)

        # nothing has been uploaded
        exp = []
        obs = get_files_from_uploads_folders("2")
        self.assertEqual(obs, exp)

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

        obs = filepath_id_to_rel_path(5)
        exp = 'preprocessed_data/1_seqs.fna'
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

    def test_find_repeated(self):
        self.assertEqual(find_repeated([]), set([]))

        not_sorted_vals = ['e', 'b', 'd', 'b', 'a', 'a', '1', '2']
        self.assertEqual(find_repeated(not_sorted_vals), set(['b', 'a']))

        sorted_vals = ['a', 'a', 'b', 'b', 'c', 'd', '1', '2']
        self.assertEqual(find_repeated(sorted_vals), set(['a', 'b']))

    def test_find_repeated_different_types(self):
        vals = [1, 2, 3, 4, 1, 1, 1, 1, 3, 3, 'a', 'b', 'a', 'x']
        self.assertEqual(find_repeated(vals), set([1, 3, 'a']))

if __name__ == '__main__':
    main()
