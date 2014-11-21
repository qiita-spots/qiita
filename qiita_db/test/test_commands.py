# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from os import remove, close, mkdir
from os.path import exists, join, basename
from tempfile import mkstemp, mkdtemp
from shutil import rmtree
from unittest import TestCase, main
from future.utils.six import StringIO
from future import standard_library
from functools import partial
with standard_library.hooks():
    import configparser

from qiita_db.commands import (load_study_from_cmd, load_raw_data_cmd,
                               load_sample_template_from_cmd,
                               load_prep_template_from_cmd,
                               load_processed_data_cmd,
                               load_preprocessed_data_from_cmd)
from qiita_db.environment_manager import patch
from qiita_db.study import Study, StudyPerson
from qiita_db.user import User
from qiita_db.data import RawData
from qiita_db.util import get_count, check_count, get_db_files_base_dir
from qiita_core.util import qiita_test_checker


@qiita_test_checker()
class TestMakeStudyFromCmd(TestCase):
    def setUp(self):
        StudyPerson.create('SomeDude', 'somedude@foo.bar', 'some',
                           '111 fake street', '111-121-1313')
        User.create('test@test.com', 'password')
        self.config1 = CONFIG_1
        self.config2 = CONFIG_2

    def test_make_study_from_cmd(self):
        fh = StringIO(self.config1)
        load_study_from_cmd('test@test.com', 'newstudy', fh)
        sql = ("select study_id from qiita.study where email = %s and "
               "study_title = %s")
        study_id = self.conn_handler.execute_fetchone(sql, ('test@test.com',
                                                            'newstudy'))
        self.assertTrue(study_id is not None)

        fh2 = StringIO(self.config2)
        with self.assertRaises(configparser.NoOptionError):
            load_study_from_cmd('test@test.com', 'newstudy2', fh2)


@qiita_test_checker()
class TestImportPreprocessedData(TestCase):
    def setUp(self):
        self.tmpdir = mkdtemp()
        fd, self.file1 = mkstemp(dir=self.tmpdir)
        close(fd)
        fd, self.file2 = mkstemp(dir=self.tmpdir)
        close(fd)
        with open(self.file1, "w") as f:
            f.write("\n")
        with open(self.file2, "w") as f:
            f.write("\n")

        self.files_to_remove = [self.file1, self.file2]
        self.dirs_to_remove = [self.tmpdir]

        self.db_test_ppd_dir = join(get_db_files_base_dir(),
                                    'preprocessed_data')

    def tearDown(self):
        for fp in self.files_to_remove:
            if exists(fp):
                remove(fp)
        for dp in self.dirs_to_remove:
            if exists(dp):
                rmtree(dp)

    def test_import_preprocessed_data(self):
        initial_ppd_count = get_count('qiita.preprocessed_data')
        initial_fp_count = get_count('qiita.filepath')
        ppd = load_preprocessed_data_from_cmd(
            1, 'preprocessed_sequence_illumina_params',
            self.tmpdir, 'preprocessed_fasta', 1, False, 1, None)
        self.files_to_remove.append(
            join(self.db_test_ppd_dir,
                 '%d_%s' % (ppd.id, basename(self.file1))))
        self.files_to_remove.append(
            join(self.db_test_ppd_dir,
                 '%d_%s' % (ppd.id, basename(self.file2))))
        self.assertEqual(ppd.id, 3)
        self.assertTrue(check_count('qiita.preprocessed_data',
                                    initial_ppd_count + 1))
        self.assertTrue(check_count('qiita.filepath', initial_fp_count+2))

    def test_import_preprocessed_data_data_type(self):
        initial_ppd_count = get_count('qiita.preprocessed_data')
        initial_fp_count = get_count('qiita.filepath')
        ppd = load_preprocessed_data_from_cmd(
            1, 'preprocessed_sequence_illumina_params',
            self.tmpdir, 'preprocessed_fasta', 1, False, None, '16S')
        self.files_to_remove.append(
            join(self.db_test_ppd_dir,
                 '%d_%s' % (ppd.id, basename(self.file1))))
        self.files_to_remove.append(
            join(self.db_test_ppd_dir,
                 '%d_%s' % (ppd.id, basename(self.file2))))
        self.assertEqual(ppd.id, 3)
        self.assertTrue(check_count('qiita.preprocessed_data',
                                    initial_ppd_count + 1))
        self.assertTrue(check_count('qiita.filepath', initial_fp_count+2))


@qiita_test_checker()
class TestLoadSampleTemplateFromCmd(TestCase):
    def setUp(self):
        # Create a sample template file
        self.st_contents = SAMPLE_TEMPLATE

        # create a new study to attach the sample template
        info = {
            "timeseries_type_id": 1,
            "metadata_complete": True,
            "mixs_compliant": True,
            "number_samples_collected": 4,
            "number_samples_promised": 4,
            "portal_type_id": 3,
            "study_alias": "TestStudy",
            "study_description": "Description of a test study",
            "study_abstract": "No abstract right now...",
            "emp_person_id": StudyPerson(2),
            "principal_investigator_id": StudyPerson(3),
            "lab_person_id": StudyPerson(1)
        }
        self.study = Study.create(User('test@foo.bar'),
                                  "Test study", [1], info)

    def test_load_sample_template_from_cmd(self):
        """Correctly adds a sample template to the DB"""
        fh = StringIO(self.st_contents)
        st = load_sample_template_from_cmd(fh, self.study.id)
        self.assertEqual(st.id, self.study.id)


@qiita_test_checker()
class TestLoadPrepTemplateFromCmd(TestCase):
    def setUp(self):
        # Create a sample template file
        fd, seqs_fp = mkstemp(suffix='_seqs.fastq')
        close(fd)
        fd, barcodes_fp = mkstemp(suffix='_barcodes.fastq')
        close(fd)

        with open(seqs_fp, "w") as f:
            f.write("\n")
        with open(barcodes_fp, "w") as f:
            f.write("\n")

        self.pt_contents = PREP_TEMPLATE

        self.raw_data = RawData.create(
            2, [Study(1)], filepaths=[(seqs_fp, 1), (barcodes_fp, 2)])

        join_f = partial(join, join(get_db_files_base_dir(), 'raw_data'))
        self.files_to_remove = [
            join_f("%s_%s" % (self.raw_data.id, basename(seqs_fp))),
            join_f("%s_%s" % (self.raw_data.id, basename(barcodes_fp)))]

    def tearDown(self):
        for fp in self.files_to_remove:
            if exists(fp):
                remove(fp)

    def test_load_prep_template_from_cmd(self):
        """Correctly adds a prep template to the DB"""
        fh = StringIO(self.pt_contents)
        st = load_prep_template_from_cmd(fh, self.raw_data.id, 1, '18S')
        self.assertEqual(st.id, 2)


@qiita_test_checker()
class TestLoadRawDataFromCmd(TestCase):
    def setUp(self):
        fd, self.forward_fp = mkstemp(suffix='_forward.fastq.gz')
        close(fd)
        fd, self.reverse_fp = mkstemp(suffix='_reverse.fastq.gz')
        close(fd)
        fd, self.barcodes_fp = mkstemp(suffix='_barcodes.fastq.gz')
        close(fd)

        with open(self.forward_fp, "w") as f:
            f.write("\n")
        with open(self.reverse_fp, "w") as f:
            f.write("\n")
        with open(self.barcodes_fp, "w") as f:
            f.write("\n")

        self.files_to_remove = []
        self.files_to_remove.append(self.forward_fp)
        self.files_to_remove.append(self.reverse_fp)
        self.files_to_remove.append(self.barcodes_fp)

        self.db_test_raw_dir = join(get_db_files_base_dir(), 'raw_data')

    def tearDown(self):
        for fp in self.files_to_remove:
            if exists(fp):
                remove(fp)

    def test_load_data_from_cmd(self):
        filepaths = [self.forward_fp, self.reverse_fp, self.barcodes_fp]
        filepath_types = ['raw_forward_seqs', 'raw_reverse_seqs',
                          'raw_barcodes']

        filetype = 'FASTQ'
        study_ids = [1]

        initial_raw_count = get_count('qiita.raw_data')
        initial_fp_count = get_count('qiita.filepath')
        initial_raw_fp_count = get_count('qiita.raw_filepath')

        new = load_raw_data_cmd(filepaths, filepath_types, filetype,
                                study_ids)
        raw_data_id = new.id
        self.files_to_remove.append(
            join(self.db_test_raw_dir,
                 '%d_%s' % (raw_data_id, basename(self.forward_fp))))
        self.files_to_remove.append(
            join(self.db_test_raw_dir,
                 '%d_%s' % (raw_data_id, basename(self.reverse_fp))))
        self.files_to_remove.append(
            join(self.db_test_raw_dir,
                 '%d_%s' % (raw_data_id, basename(self.barcodes_fp))))

        self.assertTrue(check_count('qiita.raw_data', initial_raw_count + 1))
        self.assertTrue(check_count('qiita.filepath',
                                    initial_fp_count + 3))
        self.assertTrue(check_count('qiita.raw_filepath',
                                    initial_raw_fp_count + 3))
        self.assertTrue(check_count('qiita.study_raw_data',
                                    initial_raw_count + 1))

        # Ensure that the ValueError is raised when a filepath_type is not
        # provided for each and every filepath
        with self.assertRaises(ValueError):
            load_raw_data_cmd(filepaths, filepath_types[:-1], filetype,
                              study_ids)


@qiita_test_checker()
class TestLoadProcessedDataFromCmd(TestCase):
    def setUp(self):
        fd, self.otu_table_fp = mkstemp(suffix='_otu_table.biom')
        close(fd)
        fd, self.otu_table_2_fp = mkstemp(suffix='_otu_table2.biom')
        close(fd)

        with open(self.otu_table_fp, "w") as f:
            f.write("\n")
        with open(self.otu_table_2_fp, "w") as f:
            f.write("\n")

        self.files_to_remove = []
        self.files_to_remove.append(self.otu_table_fp)
        self.files_to_remove.append(self.otu_table_2_fp)

        self.db_test_processed_data_dir = join(get_db_files_base_dir(),
                                               'processed_data')

    def tearDown(self):
        for fp in self.files_to_remove:
            if exists(fp):
                remove(fp)

    def test_load_processed_data_from_cmd(self):
        filepaths = [self.otu_table_fp, self.otu_table_2_fp]
        filepath_types = ['biom', 'biom']

        initial_processed_data_count = get_count('qiita.processed_data')
        initial_processed_fp_count = get_count('qiita.processed_filepath')
        initial_fp_count = get_count('qiita.filepath')

        new = load_processed_data_cmd(filepaths, filepath_types,
                                      'processed_params_uclust', 1, 1, None)
        processed_data_id = new.id
        self.files_to_remove.append(
            join(self.db_test_processed_data_dir,
                 '%d_%s' % (processed_data_id, basename(self.otu_table_fp))))
        self.files_to_remove.append(
            join(self.db_test_processed_data_dir,
                 '%d_%s' % (processed_data_id,
                            basename(self.otu_table_2_fp))))

        self.assertTrue(check_count('qiita.processed_data',
                                    initial_processed_data_count + 1))
        self.assertTrue(check_count('qiita.processed_filepath',
                                    initial_processed_fp_count + 2))
        self.assertTrue(check_count('qiita.filepath',
                                    initial_fp_count + 2))

        # Ensure that the ValueError is raised when a filepath_type is not
        # provided for each and every filepath
        with self.assertRaises(ValueError):
            load_processed_data_cmd(filepaths, filepath_types[:-1],
                                    'processed_params_uclust', 1, 1, None)


@qiita_test_checker()
class TestPatch(TestCase):
    def setUp(self):
        self.patches_dir = mkdtemp()
        self.py_patches_dir = join(self.patches_dir, 'python_patches')
        mkdir(self.py_patches_dir)
        patch2_fp = join(self.patches_dir, '2.sql')
        patch10_fp = join(self.patches_dir, '10.sql')

        with open(patch2_fp, 'w') as f:
            f.write("CREATE TABLE qiita.patchtest2 (testing integer);\n")
            f.write("INSERT INTO qiita.patchtest2 VALUES (1);\n")
            f.write("INSERT INTO qiita.patchtest2 VALUES (9);\n")

        with open(patch10_fp, 'w') as f:
            f.write("CREATE TABLE qiita.patchtest10 (testing integer);\n")

    def tearDown(self):
        rmtree(self.patches_dir)

    def _check_patchtest2(self, exists=True):
        if exists:
            assertion_fn = self.assertTrue
        else:
            assertion_fn = self.assertFalse

        obs = self.conn_handler.execute_fetchone(
            """SELECT EXISTS(SELECT * FROM information_schema.tables
               WHERE table_name = 'patchtest2')""")[0]
        assertion_fn(obs)

        if exists:
            exp = [[1], [9]]
            obs = self.conn_handler.execute_fetchall(
                """SELECT * FROM qiita.patchtest2 ORDER BY testing""")
            self.assertEqual(obs, exp)

    def _check_patchtest10(self):
        obs = self.conn_handler.execute_fetchone(
            """SELECT EXISTS(SELECT * FROM information_schema.tables
               WHERE table_name = 'patchtest10')""")[0]
        self.assertTrue(obs)

        exp = []
        obs = self.conn_handler.execute_fetchall(
            """SELECT * FROM qiita.patchtest10""")
        self.assertEqual(obs, exp)

    def _assert_current_patch(self, patch_to_check):
        current_patch = self.conn_handler.execute_fetchone(
            """SELECT current_patch FROM settings""")[0]
        self.assertEqual(current_patch, patch_to_check)

    def test_unpatched(self):
        """Test patching from unpatched state"""
        # Reset the settings table to the unpatched state
        self.conn_handler.execute(
            """UPDATE settings SET current_patch = 'unpatched'""")

        self._assert_current_patch('unpatched')
        patch(self.patches_dir)
        self._check_patchtest2()
        self._check_patchtest10()
        self._assert_current_patch('10.sql')

    def test_skip_patch(self):
        """Test patching from a patched state"""
        self.conn_handler.execute(
            """UPDATE settings SET current_patch = '2.sql'""")
        self._assert_current_patch('2.sql')

        # If it tried to apply patch 2.sql again, this will error
        patch(self.patches_dir)

        self._assert_current_patch('10.sql')
        self._check_patchtest10()

        # Since we "tricked" the system, patchtest2 should not exist
        self._check_patchtest2(exists=False)

    def test_nonexistent_patch(self):
        """Test case where current patch does not exist"""
        self.conn_handler.execute(
            """UPDATE settings SET current_patch = 'nope.sql'""")
        self._assert_current_patch('nope.sql')

        with self.assertRaises(RuntimeError):
            patch(self.patches_dir)

    def test_python_patch(self):
        # Write a test python patch
        patch10_py_fp = join(self.py_patches_dir, '10.py')
        with open(patch10_py_fp, 'w') as f:
            f.write(PY_PATCH)

        # Reset the settings table to the unpatched state
        self.conn_handler.execute(
            """UPDATE settings SET current_patch = 'unpatched'""")

        self._assert_current_patch('unpatched')

        patch(self.patches_dir)

        obs = self.conn_handler.execute_fetchall(
            """SELECT testing FROM qiita.patchtest10""")
        exp = [[1], [100]]
        self.assertEqual(obs, exp)

        self._assert_current_patch('10.sql')


CONFIG_1 = """[required]
timeseries_type_id = 1
metadata_complete = True
mixs_compliant = True
portal_type_id = 3
principal_investigator = SomeDude, somedude@foo.bar, some
reprocess = False
study_alias = 'test study'
study_description = 'test study description'
study_abstract = 'study abstract'
efo_ids = 1,2,3,4
[optional]
number_samples_collected = 50
number_samples_promised = 25
lab_person = SomeDude, somedude@foo.bar, some
funding = 'funding source'
vamps_id = vamps_id
"""

CONFIG_2 = """[required]
timeseries_type_id = 1
metadata_complete = True
portal_type_id = 3
principal_investigator = SomeDude, somedude@foo.bar, some
reprocess = False
study_alias = 'test study'
study_description = 'test study description'
study_abstract = 'study abstract'
efo_ids = 1,2,3,4
[optional]
number_samples_collected = 50
number_samples_promised = 25
lab_person = SomeDude, somedude@foo.bar, some
funding = 'funding source'
vamps_id = vamps_id
"""

SAMPLE_TEMPLATE = (
    "sample_name\trequired_sample_info_status\tcollection_timestamp\t"
    "sample_type\thas_physical_specimen\tphysical_location\thas_extracted_data"
    "\thost_subject_id\tTreatment\tDOB\tlatitude\tlongitude\tDescription\n"
    "PC.354\treceived\t2014-06-18 16:44\ttype_1\tTrue\tLocation_1\tTrue\t"
    "HS_ID_PC.354\tControl\t20061218\t1.88401499993\t56.0003871552\t"
    "Control_mouse_I.D._354\n"
    "PC.593\treceived\t2014-06-18 16:44\ttype_1\tTrue\tLocation_1\tTrue\t"
    "HS_ID_PC.593\tControl\t20071210\t35.4079458313\t83.2595338611\t"
    "Control_mouse_I.D._593\n"
    "PC.607\treceived\t2014-06-18 16:44\ttype_1\tTrue\tLocation_1\tTrue\t"
    "HS_ID_PC.607\tFast\t20071112\t18.3175615444\t91.3713989729\t"
    "Fasting_mouse_I.D._607\n"
    "PC.636\treceived\t2014-06-18 16:44\ttype_1\tTrue\tLocation_1\tTrue\t"
    "HS_ID_PC.636\tFast\t20080116\t31.0856060708\t4.16781143893\t"
    "Fasting_mouse_I.D._636")

PREP_TEMPLATE = (
    'sample_name\tbarcodesequence\tcenter_name\tcenter_project_name\t'
    'description\tebi_submission_accession\temp_status\tlinkerprimersequence\t'
    'run_prefix\tstr_column\tplatform\tlibrary_construction_protocol\t'
    'experiment_design_description\n'
    'SKB7.640196\tCCTCTGAGAGCT\tANL\tTest Project\tskb7\tNone\tEMP\t'
    'GTGCCAGCMGCCGCGGTAA\tts_G1_L001_sequences\tValue for sample 3\tA\tB\tC\n'
    'SKB8.640193\tGTCCGCAAGTTA\tANL\tTest Project\tskb8\tNone\tEMP\t'
    'GTGCCAGCMGCCGCGGTAA\tts_G1_L001_sequences\tValue for sample 1\tA\tB\tC\n'
    'SKD8.640184\tCGTAGAGCTCTC\tANL\tTest Project\tskd8\tNone\tEMP\t'
    'GTGCCAGCMGCCGCGGTAA\tts_G1_L001_sequences\tValue for sample 2\tA\tB\tC\n')

PY_PATCH = """
from qiita_db.study import Study
study = Study(1)
conn = SQLConnectionHandler()
conn.executemany(
    "INSERT INTO qiita.patchtest10 (testing) VALUES (%s)",
    [[study.id], [study.id*100]])
"""

if __name__ == "__main__":
    main()
