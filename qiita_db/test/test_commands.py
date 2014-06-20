# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from os import remove, close
from os.path import exists, join, basename
from tempfile import mkstemp, mkdtemp
from shutil import rmtree
from unittest import TestCase, main
from future.utils.six import StringIO
try:
    # Python 2
    from ConfigParser import NoOptionError
except ImportError:
    # Python 3
    from configparser import NoOptionError

from qiita_core.util import qiita_test_checker
from qiita_db.study import Study, StudyPerson
from qiita_db.user import User
from qiita_db.util import get_count, check_count, get_db_files_base_dir
from qiita_db.commands import (make_study_from_cmd, import_preprocessed_data,
                               load_raw_data_cmd, sample_template_adder)


@qiita_test_checker()
class TestMakeStudyFromCmd(TestCase):
    def setUp(self):
        StudyPerson.create('SomeDude', 'somedude@foo.bar',
                           '111 fake street', '111-121-1313')
        User.create('test@test.com', 'password')
        self.config1 = CONFIG_1
        self.config2 = CONFIG_2

    def test_make_study_from_cmd(self):
        fh = StringIO(self.config1)
        make_study_from_cmd('test@test.com', 'newstudy', fh)
        sql = ("select study_id from qiita.study where email = %s and "
               "study_title = %s")
        study_id = self.conn_handler.execute_fetchone(sql, ('test@test.com',
                                                            'newstudy'))
        self.assertTrue(study_id is not None)

        fh2 = StringIO(self.config2)
        with self.assertRaises(NoOptionError):
            make_study_from_cmd('test@test.com', 'newstudy2', fh2)


@qiita_test_checker()
class TestImportPreprocessedData(TestCase):
    def setUp(self):
        self.tmpdir = mkdtemp()
        fd, file1 = mkstemp(dir=self.tmpdir)
        close(fd)
        fd, file2 = mkstemp(dir=self.tmpdir)
        close(fd)
        with open(file1, "w") as f:
            f.write("\n")
        with open(file2, "w") as f:
            f.write("\n")

        self.files_to_remove = [file1, file2]
        self.dirs_to_remove = [self.tmpdir]

        self.db_test_raw_dir = join(get_db_files_base_dir(), 'raw_data')

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
        ppd = import_preprocessed_data(1, self.tmpdir, 1,
                                       'preprocessed_sequence_illumina_params',
                                       1, False)
        self.assertEqual(ppd.id, 3)
        self.assertTrue(check_count('qiita.preprocessed_data',
                                    initial_ppd_count + 1))
        self.assertTrue(check_count('qiita.filepath', initial_fp_count+2))


@qiita_test_checker()
class SampleTemplateAdderTests(TestCase):
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

    def test_sample_template_adder(self):
        """Correctly adds a sample template to the DB"""
        fh = StringIO(self.st_contents)
        st = sample_template_adder(fh, self.study.id)
        self.assertEqual(st.id, self.study.id)


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
        filepath_types = ['raw_sequences', 'raw_sequences', 'raw_barcodes']

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


CONFIG_1 = """[required]
timeseries_type_id = 1
metadata_complete = True
mixs_compliant = True
number_samples_collected = 50
number_samples_promised = 25
portal_type_id = 3
principal_investigator = SomeDude, somedude@foo.bar
reprocess = False
study_alias = 'test study'
study_description = 'test study description'
study_abstract = 'study abstract'
efo_ids = 1,2,3,4
[optional]
lab_person = SomeDude, somedude@foo.bar
funding = 'funding source'
vamps_id = vamps_id
"""

CONFIG_2 = """[required]
timeseries_type_id = 1
metadata_complete = True
number_samples_collected = 50
number_samples_promised = 25
portal_type_id = 3
principal_investigator = SomeDude, somedude@foo.bar
reprocess = False
study_alias = 'test study'
study_description = 'test study description'
study_abstract = 'study abstract'
efo_ids = 1,2,3,4
[optional]
lab_person = SomeDude, somedude@foo.bar
funding = 'funding source'
vamps_id = vamps_id
"""

SAMPLE_TEMPLATE = (
    "#SampleID\trequired_sample_info_status_id\tcollection_timestamp\t"
    "sample_type\thas_physical_specimen\tphysical_location\thas_extracted_data"
    "\thost_subject_id\tTreatment\tDOB\tDescription\n"
    "PC.354\t1\t2014-06-18 16:44\ttype_1\tTrue\tLocation_1\tTrue\tHS_ID_PC.354"
    "\tControl\t20061218\tControl_mouse_I.D._354\n"
    "PC.593\t1\t2014-06-18 16:44\ttype_1\tTrue\tLocation_1\tTrue\tHS_ID_PC.593"
    "\tControl\t20071210\tControl_mouse_I.D._593\n"
    "PC.607\t1\t2014-06-18 16:44\ttype_1\tTrue\tLocation_1\tTrue\tHS_ID_PC.607"
    "\tFast\t20071112\tFasting_mouse_I.D._607\n"
    "PC.636\t1\t2014-06-18 16:44\ttype_1\tTrue\tLocation_1\tTrue\tHS_ID_PC.636"
    "\tFast\t20080116\tFasting_mouse_I.D._636")

if __name__ == "__main__":
    main()
