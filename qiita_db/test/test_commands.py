# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from os import remove, close, mkdir
from os.path import exists, join
from tempfile import mkstemp, mkdtemp
from shutil import rmtree
from unittest import TestCase, main
from six import StringIO
from future import standard_library
from functools import partial
from operator import itemgetter

import pandas as pd

from qiita_core.util import qiita_test_checker

import qiita_db as qdb

with standard_library.hooks():
    import configparser


@qiita_test_checker()
class TestMakeStudyFromCmd(TestCase):
    def setUp(self):
        qdb.study.StudyPerson.create(
            'SomeDude', 'somedude@foo.bar', 'some',
            '111 fake street', '111-121-1313')
        qdb.user.User.create('test@test.com', 'password')
        self.config1 = CONFIG_1
        self.config2 = CONFIG_2

    def test_make_study_from_cmd(self):
        fh = StringIO(self.config1)
        qdb.commands.load_study_from_cmd('test@test.com', 'newstudy', fh)
        sql = ("select study_id from qiita.study where email = %s and "
               "study_title = %s")
        study_id = self.conn_handler.execute_fetchone(sql, ('test@test.com',
                                                            'newstudy'))
        self.assertTrue(study_id is not None)

        fh2 = StringIO(self.config2)
        with self.assertRaises(configparser.NoOptionError):
            qdb.commands.load_study_from_cmd('test@test.com', 'newstudy2', fh2)


@qiita_test_checker()
class TestLoadArtifactFromCmd(TestCase):
    def setUp(self):
        self.artifact_count = qdb.util.get_count('qiita.artifact')
        self.fp_count = qdb.util.get_count('qiita.filepath')
        self.files_to_remove = []

    def tearDown(self):
        for fp in self.files_to_remove:
            if exists(fp):
                remove(fp)

    def test_load_artifact_from_cmd_error(self):
        with self.assertRaises(ValueError):
            qdb.commands.load_artifact_from_cmd(
                ["fp1", "fp2"], ["preprocessed_fasta"], "Demultiplexed",
                parents=[1], processing_command_id=1,
                processing_parameters_id=1)

    def test_load_artifact_from_cmd_root(self):
        fd, forward_fp = mkstemp(suffix='_forward.fastq.gz')
        close(fd)
        self.files_to_remove.append(forward_fp)
        fd, reverse_fp = mkstemp(suffix='_reverse.fastq.gz')
        close(fd)
        self.files_to_remove.append(reverse_fp)
        fd, barcodes_fp = mkstemp(suffix='_barcodes.fastq.gz')
        close(fd)
        self.files_to_remove.append(barcodes_fp)
        fps = [forward_fp, reverse_fp, barcodes_fp]
        for fp in fps:
            with open(fp, 'w') as f:
                f.write('\n')
        ftypes = ['raw_forward_seqs', 'raw_reverse_seqs', 'raw_barcodes']
        metadata = pd.DataFrame.from_dict(
            {'SKB8.640193': {'center_name': 'ANL',
                             'primer': 'GTGCCAGCMGCCGCGGTAA',
                             'barcode': 'GTCCGCAAGTTA',
                             'run_prefix': "s_G1_L001_sequences",
                             'platform': 'ILLUMINA',
                             'instrument_model': 'Illumina MiSeq',
                             'library_construction_protocol': 'AAAA',
                             'experiment_design_description': 'BBBB'}},
            orient='index')
        pt = qdb.metadata_template.prep_template.PrepTemplate.create(
            metadata, qdb.study.Study(1), "16S")
        obs = qdb.commands.load_artifact_from_cmd(
            fps, ftypes, 'FASTQ', prep_template=pt.id)
        self.files_to_remove.extend([fp for _, fp, _ in obs.filepaths])
        self.assertEqual(obs.id, self.artifact_count + 1)
        self.assertTrue(
            qdb.util.check_count('qiita.filepath', self.fp_count + 5))

    def test_load_artifact_from_cmd_processed(self):
        fd, file1 = mkstemp()
        close(fd)
        self.files_to_remove.append(file1)
        fd, file2 = mkstemp()
        close(fd)
        self.files_to_remove.append(file2)
        fps = [file1, file2]
        ftypes = ['preprocessed_fasta', 'preprocessed_fastq']
        for fp in fps:
            with open(fp, 'w') as f:
                f.write("\n")
        obs = qdb.commands.load_artifact_from_cmd(
            fps, ftypes, 'Demultiplexed', parents=[1], processing_command_id=1,
            processing_parameters_id=1, can_be_submitted_to_ebi=True,
            can_be_submitted_to_vamps=True)
        self.files_to_remove.extend([fp for _, fp, _ in obs.filepaths])
        self.assertEqual(obs.id, self.artifact_count + 1)
        self.assertTrue(
            qdb.util.check_count('qiita.filepath', self.fp_count + 2))

    def test_load_artifact_from_cmd_biom(self):
        fd, otu_table_fp = mkstemp(suffix='_otu_table.biom')
        close(fd)
        self.files_to_remove.append(otu_table_fp)
        fps = [otu_table_fp]
        ftypes = ['biom']
        for fp in fps:
            with open(fp, 'w') as f:
                f.write("\n")
        obs = qdb.commands.load_artifact_from_cmd(
            fps, ftypes, 'BIOM', parents=[3], processing_command_id=3,
            processing_parameters_id=1)
        self.files_to_remove.extend([fp for _, fp, _ in obs.filepaths])
        self.assertEqual(obs.id, self.artifact_count + 1)
        self.assertTrue(
            qdb.util.check_count('qiita.filepath', self.fp_count + 1))


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
            "study_alias": "TestStudy",
            "study_description": "Description of a test study",
            "study_abstract": "No abstract right now...",
            "emp_person_id": qdb.study.StudyPerson(2),
            "principal_investigator_id": qdb.study.StudyPerson(3),
            "lab_person_id": qdb.study.StudyPerson(1)
        }
        self.study = qdb.study.Study.create(
            qdb.user.User('test@foo.bar'), "Test study", [1], info)

    def test_load_sample_template_from_cmd(self):
        """Correctly adds a sample template to the DB"""
        fh = StringIO(self.st_contents)
        st = qdb.commands.load_sample_template_from_cmd(fh, self.study.id)
        self.assertEqual(st.id, self.study.id)


@qiita_test_checker()
class TestLoadPrepTemplateFromCmd(TestCase):
    def setUp(self):
        self.pt_contents = PREP_TEMPLATE

    def test_load_prep_template_from_cmd(self):
        """Correctly adds a prep template to the DB"""
        fh = StringIO(self.pt_contents)
        st = qdb.commands.load_prep_template_from_cmd(fh, 1, '18S')
        self.assertEqual(st.id, 2)


@qiita_test_checker()
class TestLoadParametersFromCmd(TestCase):
    def setUp(self):
        fd, self.fp = mkstemp(suffix='_params.txt')
        close(fd)

        fd, self.fp_wrong = mkstemp(suffix='_params.txt')
        close(fd)

        with open(self.fp, 'w') as f:
            f.write(PARAMETERS)

        with open(self.fp_wrong, 'w') as f:
            f.write(PARAMETERS_ERROR)

        self.files_to_remove = [self.fp, self.fp_wrong]

    def tearDown(self):
        for fp in self.files_to_remove:
            if exists(fp):
                remove(fp)

    def test_load_parameters_from_cmd_error(self):
        with self.assertRaises(qdb.exceptions.QiitaDBUnknownIDError):
            qdb.commands.load_parameters_from_cmd(
                "test", self.fp, 20)

    def test_load_parameters_from_cmd_error_format(self):
        with self.assertRaises(ValueError):
            qdb.commands.load_parameters_from_cmd(
                "test", self.fp_wrong, 1)

    def test_load_parameters_from_cmd(self):
        new = qdb.commands.load_parameters_from_cmd(
            "test", self.fp, 1)
        obs = new.values
        exp = {"barcode_type": "hamming_8", "max_bad_run_length": "3",
               "max_barcode_errors": "1.5",
               "min_per_read_length_fraction": "0.75",
               "phred_quality_threshold": "3", "sequence_max_n": "0",
               "rev_comp": "False", "rev_comp_barcode": "False",
               "rev_comp_mapping_barcodes": "False",
               "sequence_max_n": "0"}
        self.assertEqual(obs, exp)


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
        qdb.environment_manager.patch(self.patches_dir)
        self._check_patchtest2()
        self._check_patchtest10()
        self._assert_current_patch('10.sql')

    def test_skip_patch(self):
        """Test patching from a patched state"""
        self.conn_handler.execute(
            """UPDATE settings SET current_patch = '2.sql'""")
        self._assert_current_patch('2.sql')

        # If it tried to apply patch 2.sql again, this will error
        qdb.environment_manager.patch(self.patches_dir)

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
            qdb.environment_manager.patch(self.patches_dir)

    def test_python_patch(self):
        # Write a test python patch
        patch10_py_fp = join(self.py_patches_dir, '10.py')
        with open(patch10_py_fp, 'w') as f:
            f.write(PY_PATCH)

        # Reset the settings table to the unpatched state
        self.conn_handler.execute(
            """UPDATE settings SET current_patch = 'unpatched'""")

        self._assert_current_patch('unpatched')

        qdb.environment_manager.patch(self.patches_dir)

        obs = self.conn_handler.execute_fetchall(
            """SELECT testing FROM qiita.patchtest10""")
        exp = [[1], [100]]
        self.assertEqual(obs, exp)

        self._assert_current_patch('10.sql')


@qiita_test_checker()
class TestUpdateArtifactFromCmd(TestCase):
    def setUp(self):
        fd, seqs_fp = mkstemp(suffix='_seqs.fastq')
        close(fd)
        fd, barcodes_fp = mkstemp(suffix='_barcodes.fastq')
        close(fd)
        self.filepaths = [seqs_fp, barcodes_fp]
        self.checksums = []
        for fp in sorted(self.filepaths):
            with open(fp, 'w') as f:
                f.write("%s\n" % fp)
            self.checksums.append(qdb.util.compute_checksum(fp))
        self.filepaths_types = ["raw_forward_seqs", "raw_barcodes"]
        self._clean_up_files = [seqs_fp, barcodes_fp]
        self.uploaded_files = qdb.util.get_files_from_uploads_folders("1")

        # The files for the Artifact 1 doesn't exist, create them
        for _, fp, _ in qdb.artifact.Artifact(1).filepaths:
            with open(fp, 'w') as f:
                f.write('\n')
            self._clean_up_files.append(fp)

    def tearDown(self):
        new_uploaded_files = qdb.util.get_files_from_uploads_folders("1")
        new_files = set(new_uploaded_files).difference(self.uploaded_files)
        path_builder = partial(
            join, qdb.util.get_mountpoint("uploads")[0][1], '1')
        self._clean_up_files.extend([path_builder(fp) for _, fp in new_files])
        for f in self._clean_up_files:
            if exists(f):
                remove(f)

    def test_update_artifact_from_cmd_error(self):
        with self.assertRaises(ValueError):
            qdb.commands.update_artifact_from_cmd(
                self.filepaths[1:], self.filepaths_types, 1)

        with self.assertRaises(ValueError):
            qdb.commands.update_artifact_from_cmd(
                self.filepaths, self.filepaths_types[1:], 1)

    def test_update_artifact_from_cmd(self):
        artifact = qdb.commands.update_artifact_from_cmd(
            self.filepaths, self.filepaths_types, 1)
        for _, fp, _ in artifact.filepaths:
            self._clean_up_files.append(fp)

        for obs, exp in zip(sorted(artifact.filepaths, key=itemgetter(1)),
                            self.checksums):
            self.assertEqual(qdb.util.compute_checksum(obs[1]), exp)


CONFIG_1 = """[required]
timeseries_type_id = 1
metadata_complete = True
mixs_compliant = True
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
    "sample_type\tphysical_specimen_remaining\tphysical_specimen_location\t"
    "dna_extracted\thost_subject_id\tTreatment\tDOB\tlatitude\tlongitude"
    "\ttaxon_id\tscientific_name\tDescription\n"
    "PC.354\treceived\t2014-06-18 16:44\ttype_1\tTrue\tLocation_1\tTrue\t"
    "HS_ID_PC.354\tControl\t20061218\t1.88401499993\t56.0003871552\t"
    "9606\thomo sapiens\tControl_mouse_I.D._354\n"
    "PC.593\treceived\t2014-06-18 16:44\ttype_1\tTrue\tLocation_1\tTrue\t"
    "HS_ID_PC.593\tControl\t20071210\t35.4079458313\t83.2595338611\t"
    "9606\thomo sapiens\tControl_mouse_I.D._593\n"
    "PC.607\treceived\t2014-06-18 16:44\ttype_1\tTrue\tLocation_1\tTrue\t"
    "HS_ID_PC.607\tFast\t20071112\t18.3175615444\t91.3713989729\t"
    "9606\thomo sapiens\tFasting_mouse_I.D._607\n"
    "PC.636\treceived\t2014-06-18 16:44\ttype_1\tTrue\tLocation_1\tTrue\t"
    "HS_ID_PC.636\tFast\t20080116\t31.0856060708\t4.16781143893\t"
    "9606\thomo sapiens\tFasting_mouse_I.D._636")

PREP_TEMPLATE = (
    'sample_name\tbarcode\tcenter_name\tcenter_project_name\t'
    'description\tebi_submission_accession\temp_status\tprimer\t'
    'run_prefix\tstr_column\tplatform\tlibrary_construction_protocol\t'
    'experiment_design_description\tinstrument_model\n'
    'SKB7.640196\tCCTCTGAGAGCT\tANL\tTest Project\tskb7\tNone\tEMP\t'
    'GTGCCAGCMGCCGCGGTAA\tts_G1_L001_sequences\tValue for sample 3\tA\tB\tC\t'
    'Illumina MiSeq\n'
    'SKB8.640193\tGTCCGCAAGTTA\tANL\tTest Project\tskb8\tNone\tEMP\t'
    'GTGCCAGCMGCCGCGGTAA\tts_G1_L001_sequences\tValue for sample 1\tA\tB\tC\t'
    'Illumina MiSeq\n'
    'SKD8.640184\tCGTAGAGCTCTC\tANL\tTest Project\tskd8\tNone\tEMP\t'
    'GTGCCAGCMGCCGCGGTAA\tts_G1_L001_sequences\tValue for sample 2\tA\tB\tC\t'
    'Illumina MiSeq\n')

PY_PATCH = """
from qiita_db.study import Study
from qiita_db.sql_connection import TRN
study = Study(1)

with TRN:
    sql = "INSERT INTO qiita.patchtest10 (testing) VALUES (%s)"
    TRN.add(sql, [[study.id], [study.id*100]], many=True)
    TRN.execute()
"""

PARAMETERS = """max_bad_run_length\t3
min_per_read_length_fraction\t0.75
sequence_max_n\t0
rev_comp_barcode\tFalse
rev_comp_mapping_barcodes\tFalse
rev_comp\tFalse
phred_quality_threshold\t3
barcode_type\thamming_8
max_barcode_errors\t1.5
"""

PARAMETERS_ERROR = """max_bad_run_length\t3\tmin_per_read_length_fraction\t0.75
sequence_max_n\t0
rev_comp_barcode\tFalse
rev_comp_mapping_barcodes\tFalse
rev_comp\tFalse
phred_quality_threshold\t3
barcode_type\thamming_8
max_barcode_errors\t1.5
"""

if __name__ == "__main__":
    main()
