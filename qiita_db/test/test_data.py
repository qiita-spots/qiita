# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

# TODO: Modify DB to fix 1084

from unittest import TestCase, main
from datetime import datetime
from os import close, remove
from os.path import join, basename, exists
from tempfile import mkstemp

import pandas as pd

from qiita_core.util import qiita_test_checker
from qiita_core.exceptions import IncompetentQiitaDeveloperError
from qiita_db.exceptions import (QiitaDBError, QiitaDBUnknownIDError,
                                 QiitaDBStatusError, QiitaDBLookupError)
from qiita_db.study import Study, StudyPerson
from qiita_db.user import User
from qiita_db.util import get_mountpoint, get_count
from qiita_db.data import BaseData, RawData, PreprocessedData, ProcessedData
from qiita_db.metadata_template import PrepTemplate


@qiita_test_checker()
class BaseDataTests(TestCase):
    """Tests the BaseData class"""

    def test_init(self):
        """Raises an error if trying to instantiate the base data"""
        with self.assertRaises(IncompetentQiitaDeveloperError):
            BaseData(1)


@qiita_test_checker()
class RawDataTests(TestCase):
    """Tests the RawData class"""

    def setUp(self):
        fd, self.seqs_fp = mkstemp(suffix='_seqs.fastq')
        close(fd)
        fd, self.barcodes_fp = mkstemp(suffix='_barcodes.fastq')
        close(fd)
        self.filetype = 2
        self.filepaths = [(self.seqs_fp, 1), (self.barcodes_fp, 2)]
        _, self.db_test_raw_dir = get_mountpoint('raw_data')[0]

        with open(self.seqs_fp, "w") as f:
            f.write("\n")
        with open(self.barcodes_fp, "w") as f:
            f.write("\n")
        self._clean_up_files = []

        # Create some new PrepTemplates
        metadata_dict = {
            'SKB8.640193': {'center_name': 'ANL',
                            'primer': 'GTGCCAGCMGCCGCGGTAA',
                            'barcode': 'GTCCGCAAGTTA',
                            'run_prefix': "s_G1_L001_sequences",
                            'platform': 'ILLUMINA',
                            'instrument_model': 'Illumina MiSeq',
                            'library_construction_protocol': 'AAAA',
                            'experiment_design_description': 'BBBB'}}
        metadata = pd.DataFrame.from_dict(metadata_dict, orient='index')
        self.pt1 = PrepTemplate.create(metadata, Study(1), "16S")
        self.pt2 = PrepTemplate.create(metadata, Study(1), "18S")
        self.prep_templates = [self.pt1, self.pt2]

    def tearDown(self):
        for f in self._clean_up_files:
            remove(f)

    def test_create(self):
        """Correctly creates all the rows in the DB for the raw data"""
        # Check that the returned object has the correct id
        exp_id = get_count("qiita.raw_data") + 1
        obs = RawData.create(self.filetype, self.prep_templates,
                             self.filepaths)
        self.assertEqual(obs.id, exp_id)

        # Check that the raw data have been correctly added to the DB
        obs = self.conn_handler.execute_fetchall(
            "SELECT * FROM qiita.raw_data WHERE raw_data_id=%d" % exp_id)
        # raw_data_id, filetype, link_filepaths_status
        self.assertEqual(obs, [[exp_id, 2, 'idle']])

        # Check that the raw data has been correctly linked with the prep
        # templates
        sql = """SELECT prep_template_id
                 FROM qiita.prep_template
                 WHERE raw_data_id = %s
                 ORDER BY prep_template_id"""
        obs = self.conn_handler.execute_fetchall(sql, (exp_id,))
        self.assertEqual(obs, [[self.pt1.id], [self.pt2.id]])

        # Check that the files have been copied to right location
        exp_seqs_fp = join(self.db_test_raw_dir,
                           "%d_%s" % (exp_id, basename(self.seqs_fp)))
        self.assertTrue(exists(exp_seqs_fp))
        self._clean_up_files.append(exp_seqs_fp)

        exp_bc_fp = join(self.db_test_raw_dir,
                         "%d_%s" % (exp_id, basename(self.barcodes_fp)))
        self.assertTrue(exists(exp_bc_fp))
        self._clean_up_files.append(exp_bc_fp)

        # Check that the filepaths have been correctly added to the DB
        top_id = self.conn_handler.execute_fetchone(
            "SELECT count(1) FROM qiita.filepath")[0]
        obs = self.conn_handler.execute_fetchall(
            "SELECT * FROM qiita.filepath WHERE filepath_id=%d or "
            "filepath_id=%d" % (top_id - 1, top_id))
        exp_seqs_fp = "%d_%s" % (exp_id, basename(self.seqs_fp))
        exp_bc_fp = "%d_%s" % (exp_id, basename(self.barcodes_fp))
        # filepath_id, path, filepath_type_id
        exp = [[top_id - 1, exp_seqs_fp, 1, '852952723', 1, 5],
               [top_id, exp_bc_fp, 2, '852952723', 1, 5]]
        self.assertEqual(obs, exp)

        # Check that the raw data have been correctly linked with the filepaths
        obs = self.conn_handler.execute_fetchall(
            "SELECT * FROM qiita.raw_filepath WHERE raw_data_id=%d" % exp_id)
        # raw_data_id, filepath_id
        self.assertEqual(obs, [[exp_id, top_id - 1], [exp_id, top_id]])

    def test_create_error(self):
        with self.assertRaises(QiitaDBError):
            RawData.create(self.filetype, [PrepTemplate(1)], self.filepaths)

    def test_get_filepaths(self):
        """Correctly returns the filepaths to the raw files"""
        rd = RawData(1)
        obs = rd.get_filepaths()
        exp = [
            (1, join(self.db_test_raw_dir, '1_s_G1_L001_sequences.fastq.gz'),
             "raw_forward_seqs"),
            (2, join(self.db_test_raw_dir,
             '1_s_G1_L001_sequences_barcodes.fastq.gz'), "raw_barcodes")]
        self.assertEqual(obs, exp)

    def test_studies(self):
        """Correctly returns the study ids"""
        rd = RawData(1)
        self.assertEqual(rd.studies, [1])

    def test_data_types(self):
        """Correctly returns the data_types of raw_data"""
        rd = RawData(1)
        self.assertEqual(rd.data_types(), ["18S"])

    def test_data_types_id(self):
        """Correctly returns the data_types of raw_data"""
        rd = RawData(1)
        self.assertEqual(rd.data_types(ret_id=True), [2])

    def test_filetype(self):
        rd = RawData(1)
        self.assertEqual(rd.filetype, "FASTQ")

    def test_prep_templates(self):
        rd = RawData(1)
        self.assertEqual(rd.prep_templates, [1])

    def test_link_filepaths_status(self):
        rd = RawData(1)
        self.assertEqual(rd.link_filepaths_status, 'idle')

    def test_link_filepaths_status_setter(self):
        rd = RawData(1)
        self.assertEqual(rd.link_filepaths_status, 'idle')
        rd._set_link_filepaths_status('linking')
        self.assertEqual(rd.link_filepaths_status, 'linking')
        rd._set_link_filepaths_status('unlinking')
        self.assertEqual(rd.link_filepaths_status, 'unlinking')
        rd._set_link_filepaths_status('failed: error')
        self.assertEqual(rd.link_filepaths_status, 'failed: error')

    def test_link_filepaths_status_setter_error(self):
        rd = RawData(1)
        with self.assertRaises(ValueError):
            rd._set_link_filepaths_status('not a valid status')

    def test_is_preprocessed(self):
        self.assertTrue(RawData(1)._is_preprocessed())
        rd = RawData.create(self.filetype, self.prep_templates, self.filepaths)
        self.assertFalse(rd._is_preprocessed())

    def test_clear_filepaths(self):
        rd = RawData.create(self.filetype, [self.pt1], self.filepaths)
        self.assertTrue(self.conn_handler.execute_fetchone(
            "SELECT EXISTS(SELECT * FROM qiita.raw_filepath "
            "WHERE raw_data_id=%s)", (rd.id,))[0])

        # add files to clean before cleaning the filepaths
        study_id = rd.studies[0]
        path_for_removal = join(get_mountpoint("uploads")[0][1], str(study_id))
        self._clean_up_files = [join(path_for_removal,
                                     basename(f).split('_', 1)[1])
                                for _, f, _ in rd.get_filepaths()]

        # cleaning the filepaths
        rd.clear_filepaths()
        self.assertFalse(self.conn_handler.execute_fetchone(
            "SELECT EXISTS(SELECT * FROM qiita.raw_filepath "
            "WHERE raw_data_id=%s)", (rd.id,))[0])

    def test_clear_filepaths_error(self):
        with self.assertRaises(QiitaDBError):
            RawData(1).clear_filepaths()

    def test_exists(self):
        self.assertTrue(RawData.exists(1))
        self.assertFalse(RawData.exists(1000))

    def test_delete_error_no_exists(self):
        # the raw data doesn't exist
        with self.assertRaises(QiitaDBUnknownIDError):
            RawData.delete(1000, 0)

    def test_delete_error_raw_data_not_linked(self):
        # the raw data and the prep template id are not linked
        with self.assertRaises(QiitaDBError):
            RawData.delete(1, self.pt2.id)

    def test_delete_error_prep_template_no_exists(self):
        # the prep template does not exist
        with self.assertRaises(QiitaDBError):
            RawData.delete(1, 1000)

    def test_delete_error_linked_files(self):
        # the raw data has linked files
        with self.assertRaises(QiitaDBError):
            RawData.delete(1, 1)

    def test_delete(self):
        rd = RawData.create(self.filetype, self.prep_templates,
                            self.filepaths)

        sql_pt = """SELECT prep_template_id
                    FROM qiita.prep_template
                    WHERE raw_data_id = %s
                    ORDER BY prep_template_id"""
        obs = self.conn_handler.execute_fetchall(sql_pt, (rd.id,))
        self.assertEqual(obs, [[self.pt1.id], [self.pt2.id]])

        # This delete call will only unlink the raw data from the prep template
        RawData.delete(rd.id, self.pt2.id)

        # Check that it successfully unlink the raw data from pt2
        obs = self.conn_handler.execute_fetchall(sql_pt, (rd.id,))
        self.assertEqual(obs, [[self.pt1.id]])
        self.assertEqual(self.pt2.raw_data, None)

        # If we try to remove the RawData now, it should raise an error
        # because it still has files attached to it
        with self.assertRaises(QiitaDBError):
            RawData.delete(rd.id, self.pt1.id)

        # Clear the files so we can actually remove the RawData
        study_id = rd.studies[0]
        path_for_removal = join(get_mountpoint("uploads")[0][1], str(study_id))
        self._clean_up_files.extend([join(path_for_removal,
                                     basename(f).split('_', 1)[1])
                                    for _, f, _ in rd.get_filepaths()])
        rd.clear_filepaths()

        RawData.delete(rd.id, self.pt1.id)
        obs = self.conn_handler.execute_fetchall(sql_pt, (rd.id,))
        self.assertEqual(obs, [])

        # Check that all expected rows have been deleted
        sql = """SELECT EXISTS(
                    SELECT * FROM qiita.raw_filepath
                    WHERE raw_data_id = %s)"""
        self.assertFalse(self.conn_handler.execute_fetchone(sql, (rd.id,))[0])

        sql = """SELECT EXISTS(
                    SELECT * FROM qiita.raw_data
                    WHERE raw_data_id=%s)"""
        self.assertFalse(self.conn_handler.execute_fetchone(sql, (rd.id,))[0])

    def test_status(self):
        rd = RawData(1)
        s = Study(1)
        self.assertEqual(rd.status(s), 'private')

        # Since the status is inferred from the processed data, change the
        # status of the processed data so we can check how it changes in the
        # preprocessed data
        pd = ProcessedData(1)
        pd.status = 'public'
        self.assertEqual(rd.status(s), 'public')

        # Check that new raw data has sandbox as status since no
        # processed data exists for them
        rd = RawData.create(self.filetype, self.prep_templates, self.filepaths)
        self.assertEqual(rd.status(s), 'sandbox')

    def test_status_error(self):
        # Let's create a new study, so we can check that the error is raised
        # because the new study does not have access to the raw data
        info = {
            "timeseries_type_id": 1,
            "metadata_complete": True,
            "mixs_compliant": True,
            "number_samples_collected": 25,
            "number_samples_promised": 28,
            "study_alias": "FCM",
            "study_description": "Microbiome of people who eat nothing but "
                                 "fried chicken",
            "study_abstract": "Exploring how a high fat diet changes the "
                              "gut microbiome",
            "emp_person_id": StudyPerson(2),
            "principal_investigator_id": StudyPerson(3),
            "lab_person_id": StudyPerson(1)
        }
        s = Study.create(User('test@foo.bar'), "Fried chicken microbiome",
                         [1], info)
        rd = RawData(1)

        with self.assertRaises(QiitaDBStatusError):
            rd.status(s)


@qiita_test_checker()
class PreprocessedDataTests(TestCase):
    """Tests the PreprocessedData class"""
    def setUp(self):
        self.prep_template = PrepTemplate(1)
        self.study = Study(1)
        self.params_table = "preprocessed_sequence_illumina_params"
        self.params_id = 1
        fd, self.fna_fp = mkstemp(suffix='_seqs.fna')
        close(fd)
        fd, self.qual_fp = mkstemp(suffix='_seqs.qual')
        close(fd)
        self.filepaths = [(self.fna_fp, 4), (self.qual_fp, 5)]
        _, self.db_test_ppd_dir = get_mountpoint(
            'preprocessed_data')[0]
        self.ebi_submission_accession = "EBI123456-A"
        self.ebi_study_accession = "EBI123456-B"

        with open(self.fna_fp, "w") as f:
            f.write("\n")
        with open(self.qual_fp, "w") as f:
            f.write("\n")
        self._clean_up_files = []

    def tearDown(self):
        for f in self._clean_up_files:
            remove(f)

    def test_create(self):
        """Correctly creates all the rows in the DB for preprocessed data"""
        # Check that the returned object has the correct id
        obs = PreprocessedData.create(
            self.study, self.params_table,
            self.params_id, self.filepaths, prep_template=self.prep_template,
            ebi_submission_accession=self.ebi_submission_accession,
            ebi_study_accession=self.ebi_study_accession)
        self.assertEqual(obs.id, 3)

        # Check that the preprocessed data have been correctly added to the DB
        obs = self.conn_handler.execute_fetchall(
            "SELECT * FROM qiita.preprocessed_data WHERE "
            "preprocessed_data_id=3")
        # preprocessed_data_id, preprocessed_params_table,
        # preprocessed_params_id, submitted_to_insdc_status,
        # ebi_submission_accession, ebi_study_accession, data_type_id,
        # link_filepaths_status, vamps_status, processing_status
        exp = [[3, "preprocessed_sequence_illumina_params", 1,
                'not submitted', "EBI123456-A", "EBI123456-B", 2, 'idle',
                'not submitted', 'not_processed']]
        self.assertEqual(obs, exp)

        # Check that the preprocessed data has been linked with its study
        obs = self.conn_handler.execute_fetchall(
            "SELECT * FROM qiita.study_preprocessed_data WHERE "
            "preprocessed_data_id=3")
        exp = [[1, 3]]
        self.assertEqual(obs, exp)

        # Check that the files have been copied to right location
        exp_fna_fp = join(self.db_test_ppd_dir,
                          "3_%s" % basename(self.fna_fp))
        self.assertTrue(exists(exp_fna_fp))
        self._clean_up_files.append(exp_fna_fp)

        exp_qual_fp = join(self.db_test_ppd_dir,
                           "3_%s" % basename(self.qual_fp))
        self.assertTrue(exists(exp_qual_fp))
        self._clean_up_files.append(exp_qual_fp)

        # Check that the filepaths have been correctly added to the DB
        obs_id = self.conn_handler.execute_fetchone(
            "SELECT count(1) from qiita.filepath")[0]
        obs = self.conn_handler.execute_fetchall(
            "SELECT * FROM qiita.filepath WHERE filepath_id=%d or "
            "filepath_id=%d" % (obs_id - 1, obs_id))
        exp_fna_fp = "3_%s" % basename(self.fna_fp)
        exp_qual_fp = "3_%s" % basename(self.qual_fp)
        # filepath_id, path, filepath_type_id
        exp = [[obs_id - 1, exp_fna_fp, 4, '852952723', 1, 3],
               [obs_id, exp_qual_fp, 5, '852952723', 1, 3]]
        self.assertEqual(obs, exp)

    def test_create_data_type_only(self):
        # Check that the returned object has the correct id
        obs = PreprocessedData.create(self.study, self.params_table,
                                      self.params_id, self.filepaths,
                                      data_type="18S")
        self.assertEqual(obs.id, 3)

        # Check that the preprocessed data have been correctly added to the DB
        obs = self.conn_handler.execute_fetchall(
            "SELECT * FROM qiita.preprocessed_data WHERE "
            "preprocessed_data_id=3")
        # preprocessed_data_id, preprocessed_params_table,
        # preprocessed_params_id, submitted_to_insdc_status,
        # ebi_submission_accession, ebi_study_accession, data_type_id,
        # link_filepaths_status, vamps_status, processing_status
        exp = [[3, "preprocessed_sequence_illumina_params", 1,
                'not submitted', None, None, 2, 'idle', 'not submitted',
                'not_processed']]
        self.assertEqual(obs, exp)

        # Check that the preprocessed data has been linked with its study
        obs = self.conn_handler.execute_fetchall(
            "SELECT * FROM qiita.study_preprocessed_data WHERE "
            "preprocessed_data_id=3")
        exp = [[1, 3]]
        self.assertEqual(obs, exp)

        # Check that the files have been copied to right location
        exp_fna_fp = join(self.db_test_ppd_dir,
                          "3_%s" % basename(self.fna_fp))
        self.assertTrue(exists(exp_fna_fp))
        self._clean_up_files.append(exp_fna_fp)

        exp_qual_fp = join(self.db_test_ppd_dir,
                           "3_%s" % basename(self.qual_fp))
        self.assertTrue(exists(exp_qual_fp))
        self._clean_up_files.append(exp_qual_fp)

        # Check that the filepaths have been correctly added to the DB
        obs_id = self.conn_handler.execute_fetchone(
            "SELECT count(1) from qiita.filepath")[0]
        obs = self.conn_handler.execute_fetchall(
            "SELECT * FROM qiita.filepath WHERE filepath_id=%d or "
            "filepath_id=%d" % (obs_id - 1, obs_id))
        exp_fna_fp = "3_%s" % basename(self.fna_fp)
        exp_qual_fp = "3_%s" % basename(self.qual_fp)
        # filepath_id, path, filepath_type_id
        exp = [[obs_id - 1, exp_fna_fp, 4, '852952723', 1, 3],
               [obs_id, exp_qual_fp, 5, '852952723', 1, 3]]
        self.assertEqual(obs, exp)

        # Check that the preprocessed data have been correctly
        # linked with the filepaths
        obs = self.conn_handler.execute_fetchall(
            "SELECT * FROM qiita.preprocessed_filepath WHERE "
            "preprocessed_data_id=3")
        # preprocessed_data_id, filepath_id
        self.assertEqual(obs, [[3, obs_id - 1], [3, obs_id]])

    def test_delete_basic(self):
        """Correctly deletes a preprocessed data"""
        # testing regular delete
        ppd = PreprocessedData.create(
            self.study, self.params_table,
            self.params_id, self.filepaths, prep_template=self.prep_template,
            ebi_submission_accession=self.ebi_submission_accession,
            ebi_study_accession=self.ebi_study_accession)
        PreprocessedData.delete(ppd.id)

        # testing that the deleted preprocessed data can't be instantiated
        with self.assertRaises(QiitaDBUnknownIDError):
            PreprocessedData(ppd.id)
        # and for completeness testing that it raises an error if ID
        # doesn't exist
        with self.assertRaises(QiitaDBUnknownIDError):
            PreprocessedData.delete(ppd.id)

        # testing that we can not remove cause the preprocessed data != sandbox
        with self.assertRaises(QiitaDBStatusError):
            PreprocessedData.delete(1)

    def test_delete_advanced(self):
        # testing that we can not remove cause preprocessed data has been
        # submitted to EBI or VAMPS
        ppd = PreprocessedData.create(
            self.study, self.params_table,
            self.params_id, self.filepaths, prep_template=self.prep_template,
            ebi_submission_accession=self.ebi_submission_accession,
            ebi_study_accession=self.ebi_study_accession)

        # fails due to VAMPS submission
        ppd.update_vamps_status('success')
        with self.assertRaises(QiitaDBStatusError):
            PreprocessedData.delete(ppd.id)
        ppd.update_vamps_status('failed')

        # fails due to EBI submission
        ppd.update_insdc_status('success', 'AAAA', 'AAAA')
        with self.assertRaises(QiitaDBStatusError):
            PreprocessedData.delete(ppd.id)

    def test_create_error_dynamic_table(self):
        """Raises an error if the preprocessed_params_table does not exist"""
        with self.assertRaises(IncompetentQiitaDeveloperError):
            PreprocessedData.create(self.study, "foo", self.params_id,
                                    self.filepaths, data_type="18S")
        with self.assertRaises(IncompetentQiitaDeveloperError):
            PreprocessedData.create(self.study, "preprocessed_foo",
                                    self.params_id, self.filepaths,
                                    data_type="18S")
        with self.assertRaises(IncompetentQiitaDeveloperError):
            PreprocessedData.create(self.study, "foo_params", self.params_id,
                                    self.filepaths, data_type="18S")
        with self.assertRaises(IncompetentQiitaDeveloperError):
            PreprocessedData.create(self.study, "preprocessed_foo_params",
                                    self.params_id, self.filepaths,
                                    data_type="18S")

    def test_create_error_data_type(self):
        with self.assertRaises(QiitaDBLookupError):
            PreprocessedData.create(self.study,
                                    "preprocessed_sequence_illumina_params",
                                    self.params_id, self.filepaths,
                                    data_type="Metabolomics")
        with self.assertRaises(IncompetentQiitaDeveloperError):
            PreprocessedData.create(self.study,
                                    "preprocessed_sequence_illumina_params",
                                    self.params_id, self.filepaths,
                                    data_type="Metabolomics",
                                    prep_template=self.prep_template)

    def test_get_filepaths(self):
        """Correctly returns the filepaths to the preprocessed files"""
        ppd = PreprocessedData(1)
        obs = ppd.get_filepaths()
        exp = [(3, join(self.db_test_ppd_dir, '1_seqs.fna'),
                "preprocessed_fasta"),
               (4, join(self.db_test_ppd_dir, '1_seqs.qual'),
                "preprocessed_fastq"),
               (5, join(self.db_test_ppd_dir, '1_seqs.demux'),
                "preprocessed_demux")]
        self.assertItemsEqual(obs, exp)

    def test_processed_data(self):
        """Correctly returns the processed data id"""
        ppd = PreprocessedData(1)
        self.assertEqual(ppd.processed_data, [1])

    def test_prep_template(self):
        """Correctly returns the prep template"""
        ppd = PreprocessedData(1)
        self.assertEqual(ppd.prep_template, 1)

    def test_study(self):
        """Correctly returns the study"""
        ppd = PreprocessedData(1)
        self.assertEqual(ppd.study, 1)

    def test_ebi_submission_accession(self):
        """Correctly returns the ebi_submission_accession"""
        ppd = PreprocessedData(1)
        self.assertEqual(ppd.ebi_submission_accession, 'EBI123456-AA')

    def test_ebi_ebi_study_accession(self):
        """Correctly returns the ebi_study_accession"""
        ppd = PreprocessedData(1)
        self.assertEqual(ppd.ebi_study_accession, 'EBI123456-BB')

    def test_set_ebi_submission_accession(self):
        new = PreprocessedData.create(
            self.study, self.params_table, self.params_id, self.filepaths,
            prep_template=self.prep_template,
            ebi_submission_accession=self.ebi_submission_accession,
            ebi_study_accession=self.ebi_study_accession)

        new.ebi_submission_accession = 'EBI12345-CC'
        self.assertEqual(new.ebi_submission_accession, 'EBI12345-CC')

    def test_ebi_study_accession(self):
        new = PreprocessedData.create(
            self.study, self.params_table,
            self.params_id, self.filepaths, prep_template=self.prep_template,
            ebi_submission_accession=self.ebi_submission_accession,
            ebi_study_accession=self.ebi_study_accession)

        new.ebi_study_accession = 'EBI12345-DD'
        self.assertEqual(new.ebi_study_accession, 'EBI12345-DD')

    def test_submitted_to_insdc_status(self):
        """submitted_to_insdc_status works correctly"""
        # False case
        pd = PreprocessedData(1)
        self.assertEqual(pd.submitted_to_insdc_status(), 'submitting')
        # True case
        pd = PreprocessedData(2)
        self.assertEqual(pd.submitted_to_insdc_status(), 'not submitted')

    def test_update_insdc_status(self):
        """Able to update insdc status"""
        pd = PreprocessedData(1)
        self.assertEqual(pd.submitted_to_insdc_status(), 'submitting')
        pd.update_insdc_status('failed')
        self.assertEqual(pd.submitted_to_insdc_status(), 'failed')

        pd.update_insdc_status('success', 'foo', 'bar')
        self.assertEqual(pd.submitted_to_insdc_status(), 'success')
        self.assertEqual(pd.ebi_study_accession, 'foo')
        self.assertEqual(pd.ebi_submission_accession, 'bar')

        with self.assertRaises(ValueError):
            pd.update_insdc_status('not valid state')

        with self.assertRaises(ValueError):
            pd.update_insdc_status('success', 'only one accession')

    def test_data_type(self):
        """Correctly returns the data_type of preprocessed_data"""
        pd = ProcessedData(1)
        self.assertEqual(pd.data_type(), "18S")

    def test_data_type_id(self):
        """Correctly returns the data_type of preprocessed_data"""
        pd = ProcessedData(1)
        self.assertEqual(pd.data_type(ret_id=True), 2)

    def test_link_filepaths_status(self):
        ppd = PreprocessedData(1)
        self.assertEqual(ppd.link_filepaths_status, 'idle')

    def test_link_filepaths_status_setter(self):
        ppd = PreprocessedData(1)
        self.assertEqual(ppd.link_filepaths_status, 'idle')
        ppd._set_link_filepaths_status('linking')
        self.assertEqual(ppd.link_filepaths_status, 'linking')
        ppd._set_link_filepaths_status('unlinking')
        self.assertEqual(ppd.link_filepaths_status, 'unlinking')
        ppd._set_link_filepaths_status('failed: error')
        self.assertEqual(ppd.link_filepaths_status, 'failed: error')

    def test_link_filepaths_status_setter_error(self):
        ppd = PreprocessedData(1)
        with self.assertRaises(ValueError):
            ppd._set_link_filepaths_status('not a valid status')

    def test_insdc_status(self):
        ppd = PreprocessedData(1)

        # verifying current value
        self.assertEqual(ppd.submitted_to_insdc_status(), 'submitting')

        # changing value and then verifying new value
        ppd.update_insdc_status('failed')
        self.assertEqual(ppd.submitted_to_insdc_status(), 'failed')

        # checking failure
        with self.assertRaises(ValueError):
            ppd.update_insdc_status('not a valid status')

    def test_vamps_status(self):
        ppd = PreprocessedData(1)

        # verifying current value
        self.assertEqual(ppd.submitted_to_vamps_status(), 'not submitted')

        # changing value and then verifying new value
        ppd.update_vamps_status('failed')
        self.assertEqual(ppd.submitted_to_vamps_status(), 'failed')

        # checking failure
        with self.assertRaises(ValueError):
            ppd.update_vamps_status('not a valid status')

    def test_processing_status(self):
        """processing_status works correctly"""
        # Processed case
        ppd = PreprocessedData(1)
        self.assertEqual(ppd.processing_status, 'not_processed')

        # not processed case
        ppd = PreprocessedData.create(self.study, self.params_table,
                                      self.params_id, self.filepaths,
                                      data_type="18S")
        self.assertEqual(ppd.processing_status, 'not_processed')

    def test_processing_status_setter(self):
        """Able to update the processing status"""
        ppd = PreprocessedData.create(self.study, self.params_table,
                                      self.params_id, self.filepaths,
                                      data_type="18S")
        self.assertEqual(ppd.processing_status, 'not_processed')
        ppd.processing_status = 'processing'
        self.assertEqual(ppd.processing_status, 'processing')
        ppd.processing_status = 'processed'
        self.assertEqual(ppd.processing_status, 'processed')
        state = 'failed: some error message'
        ppd.processing_status = state
        self.assertEqual(ppd.processing_status, state)

    def test_processing_status_setter_valueerror(self):
        """Raises an error if the processing status is not recognized"""
        ppd = PreprocessedData.create(self.study, self.params_table,
                                      self.params_id, self.filepaths,
                                      data_type="18S")
        with self.assertRaises(ValueError):
            ppd.processing_status = 'not a valid state'

    def test_exists(self):
        self.assertTrue(PreprocessedData.exists(1))
        self.assertFalse(PreprocessedData.exists(1000))

    def test_status(self):
        ppd = PreprocessedData(1)
        self.assertEqual(ppd.status, 'private')

        # Since the status is inferred from the processed data, change the
        # status of the processed data so we can check how it changes in the
        # preprocessed data
        pd = ProcessedData(1)
        pd.status = 'public'
        self.assertEqual(ppd.status, 'public')

        # Check that new preprocessed data has sandbox as status since no
        # processed data exists for them
        ppd = PreprocessedData.create(self.study, self.params_table,
                                      self.params_id, self.filepaths,
                                      data_type="16S")
        self.assertEqual(ppd.status, 'sandbox')


@qiita_test_checker()
class ProcessedDataTests(TestCase):
    """Tests the ProcessedData class"""
    def setUp(self):
        self.preprocessed_data = PreprocessedData(1)
        self.params_table = "processed_params_uclust"
        self.params_id = 1
        fd, self.biom_fp = mkstemp(suffix='_table.biom')
        close(fd)
        self.filepaths = [(self.biom_fp, 6)]
        self.date = datetime(2014, 5, 29, 12, 24, 51)
        _, self.db_test_pd_dir = get_mountpoint(
            'processed_data')[0]

        with open(self.biom_fp, "w") as f:
            f.write("\n")
        self._clean_up_files = []

    def tearDown(self):
        for f in self._clean_up_files:
            remove(f)

    def test_create(self):
        """Correctly creates all the rows in the DB for the processed data"""
        # Check that the returned object has the correct id
        obs = ProcessedData.create(self.params_table, self.params_id,
                                   self.filepaths,
                                   preprocessed_data=self.preprocessed_data,
                                   processed_date=self.date)
        self.assertEqual(obs.id, 2)

        # Check that the processed data have been correctly added to the DB
        obs = self.conn_handler.execute_fetchall(
            "SELECT * FROM qiita.processed_data WHERE processed_data_id=2")
        # processed_data_id, processed_params_table, processed_params_id,
        # processed_date, data_type_id, link_filepaths_status,
        # processed_data_status_id
        exp = [[2, "processed_params_uclust", 1, self.date, 2, 'idle', 4]]
        self.assertEqual(obs, exp)

        # Check that the files have been copied to right location
        exp_biom_fp = join(self.db_test_pd_dir,
                           "2_%s" % basename(self.biom_fp))
        self.assertTrue(exists(exp_biom_fp))
        self._clean_up_files.append(exp_biom_fp)

        # Check that the filepaths have been correctly added to the DB
        obs_id = self.conn_handler.execute_fetchone(
            "SELECT count(1) from qiita.filepath")[0]
        obs = self.conn_handler.execute_fetchall(
            "SELECT * FROM qiita.filepath WHERE filepath_id=%d" % obs_id)
        exp_biom_fp = "2_%s" % basename(self.biom_fp)
        # Filepath_id, path, filepath_type_id
        exp = [[obs_id, exp_biom_fp, 6, '852952723', 1, 4]]
        self.assertEqual(obs, exp)

        # Check that the processed data have been correctly linked
        # with the fileapths
        obs = self.conn_handler.execute_fetchall(
            "SELECT * FROM qiita.processed_filepath WHERE processed_data_id=2")
        # processed_data_id, filepath_id
        self.assertEqual(obs, [[2, obs_id]])

        # Check that the processed data have been correctly linked with the
        # study
        obs = self.conn_handler.execute_fetchall(
            "SELECT * FROM qiita.study_processed_data WHERE "
            "processed_data_id=2")
        # study_id, processed_data
        self.assertEqual(obs, [[1, 2]])

        # Check that the processed data have been correctly linked with the
        # preprocessed data
        obs = self.conn_handler.execute_fetchall(
            "SELECT * FROM qiita.preprocessed_processed_data WHERE "
            "processed_data_id=2")
        # preprocessed_data_id, processed_Data_id
        self.assertEqual(obs, [[1, 2]])

    def test_delete(self):
        """Correctly deletes a processed data"""
        # testing regular delete
        pd = ProcessedData.create(self.params_table, self.params_id,
                                  self.filepaths,
                                  preprocessed_data=self.preprocessed_data,
                                  processed_date=self.date)
        ProcessedData.delete(pd.id)

        # testing that it raises an error if ID doesn't exist
        with self.assertRaises(QiitaDBUnknownIDError):
            ProcessedData.delete(pd.id)

        # testing that we can not remove cause the processed data != sandbox
        with self.assertRaises(QiitaDBStatusError):
            ProcessedData.delete(1)

        # testing that we can not remove cause processed data has analyses
        pd = ProcessedData(1)
        pd.status = 'sandbox'
        with self.assertRaises(QiitaDBError):
            ProcessedData.delete(1)

    def test_create_no_date(self):
        """Correctly adds a processed data with no date on it"""
        # All the other settings have been already tested on test_create
        # here we will only check that the code added a good date
        before = datetime.now()
        ProcessedData.create(self.params_table, self.params_id, self.filepaths,
                             preprocessed_data=self.preprocessed_data)
        after = datetime.now()
        obs = self.conn_handler.execute_fetchone(
            "SELECT processed_date FROM qiita.processed_data WHERE "
            "processed_data_id=2")[0]

        # Make sure that we clean up the environment
        exp_biom_fp = join(self.db_test_pd_dir,
                           "2_%s" % basename(self.biom_fp))
        self._clean_up_files.append(exp_biom_fp)

        self.assertTrue(before <= obs <= after)

    def test_create_w_study(self):
        """Correctly adds a processed data passing a study"""
        obs = ProcessedData.create(self.params_table, self.params_id,
                                   self.filepaths, study=Study(1),
                                   processed_date=self.date, data_type="18S")

        # Check that the processed data have been correctly added to the DB
        obs = self.conn_handler.execute_fetchall(
            "SELECT * FROM qiita.processed_data WHERE processed_data_id=2")
        # processed_data_id, processed_params_table, processed_params_id,
        # processed_date, data_type_id, link_filepaths_status,
        # processed_data_status_id
        exp = [[2, "processed_params_uclust", 1, self.date, 2, 'idle', 4]]
        self.assertEqual(obs, exp)

        # Check that the files have been copied to right location
        exp_biom_fp = join(self.db_test_pd_dir,
                           "2_%s" % basename(self.biom_fp))
        self.assertTrue(exists(exp_biom_fp))
        self._clean_up_files.append(exp_biom_fp)

        # Check that the filepaths have been correctly added to the DB
        obs_id = self.conn_handler.execute_fetchone(
            "SELECT count(1) from qiita.filepath")[0]
        obs = self.conn_handler.execute_fetchall(
            "SELECT * FROM qiita.filepath WHERE filepath_id=%d" % obs_id)
        exp_biom_fp = "2_%s" % basename(self.biom_fp)
        # Filepath_id, path, filepath_type_id
        exp = [[obs_id, exp_biom_fp, 6, '852952723', 1, 4]]
        self.assertEqual(obs, exp)

        # Check that the processed data have been correctly linked
        # with the fileapths
        obs = self.conn_handler.execute_fetchall(
            "SELECT * FROM qiita.processed_filepath WHERE processed_data_id=2")
        # processed_data_id, filepath_id
        self.assertTrue(obs, [[2, 10]])

        # Check that the processed data have been correctly linked with the
        # study
        obs = self.conn_handler.execute_fetchall(
            "SELECT * FROM qiita.study_processed_data WHERE "
            "processed_data_id=2")
        # study_id, processed_data
        self.assertEqual(obs, [[1, 2]])

    def test_create_params_table_error(self):
        """Raises an error if the processed_params_table does not exist"""
        with self.assertRaises(IncompetentQiitaDeveloperError):
            ProcessedData.create("foo", self.params_id, self.filepaths,
                                 preprocessed_data=self.preprocessed_data)
        with self.assertRaises(IncompetentQiitaDeveloperError):
            ProcessedData.create("processed_params_foo", self.params_id,
                                 self.filepaths,
                                 preprocessed_data=self.preprocessed_data)
        with self.assertRaises(IncompetentQiitaDeveloperError):
            ProcessedData.create("processed_params_", self.params_id,
                                 self.filepaths,
                                 preprocessed_data=self.preprocessed_data)

    def test_create_no_preprocessed_no_study_error(self):
        with self.assertRaises(IncompetentQiitaDeveloperError):
            ProcessedData.create(self.params_table, self.params_id,
                                 self.filepaths)

    def test_create_preprocessed_and_study_error(self):
        with self.assertRaises(IncompetentQiitaDeveloperError):
            ProcessedData.create(self.params_table, self.params_id,
                                 self.filepaths,
                                 preprocessed_data=self.preprocessed_data,
                                 study=Study(1))

    def test_create_preprocessed_and_data_type_error(self):
        with self.assertRaises(IncompetentQiitaDeveloperError):
            ProcessedData.create(self.params_table, self.params_id,
                                 self.filepaths,
                                 preprocessed_data=self.preprocessed_data,
                                 data_type="Metabolomics",)

    def test_create_no_preprocessed_and_study_error(self):
        with self.assertRaises(IncompetentQiitaDeveloperError):
            ProcessedData.create(self.params_table, self.params_id,
                                 self.filepaths)

    def test_get_filepath(self):
        """Correctly returns the filepaths to the processed files"""
        # check the test data
        pd = ProcessedData(1)
        obs = pd.get_filepaths()
        exp = [(9, join(self.db_test_pd_dir,
                '1_study_1001_closed_reference_otu_table.biom'), "biom")]
        self.assertEqual(obs, exp)

    def test_get_filepath_ids(self):
        pd = ProcessedData(1)
        self.assertEqual(pd.get_filepath_ids(), [9])

    def test_preprocessed_data(self):
        """Correctly returns the preprocessed_data"""
        pd = ProcessedData(1)
        self.assertEqual(pd.preprocessed_data, 1)

    def test_data_type(self):
        pd = ProcessedData(1)
        self.assertEqual(pd.data_type(), "18S")

    def test_data_type_id(self):
        pd = ProcessedData(1)
        self.assertEqual(pd.data_type(ret_id=True), 2)

    def test_link_filepaths_status(self):
        pd = ProcessedData(1)
        self.assertEqual(pd.link_filepaths_status, 'idle')

    def test_link_filepaths_status_setter(self):
        pd = ProcessedData(1)
        self.assertEqual(pd.link_filepaths_status, 'idle')
        pd._set_link_filepaths_status('linking')
        self.assertEqual(pd.link_filepaths_status, 'linking')
        pd._set_link_filepaths_status('unlinking')
        self.assertEqual(pd.link_filepaths_status, 'unlinking')
        pd._set_link_filepaths_status('failed: error')
        self.assertEqual(pd.link_filepaths_status, 'failed: error')

    def test_processing_info(self):
        pd = ProcessedData(1)
        exp = {
            'algorithm': 'uclust',
            'processed_date': datetime(2012, 10, 1, 9, 30, 27),
            'enable_rev_strand_match': True,
            'similarity': 0.97,
            'suppress_new_clusters': True,
            'reference_name': 'Greengenes',
            'reference_version': '13_8',
            'sequence_filepath': 'GreenGenes_13_8_97_otus.fasta',
            'taxonomy_filepath': 'GreenGenes_13_8_97_otu_taxonomy.txt',
            'tree_filepath': 'GreenGenes_13_8_97_otus.tree'}
        self.assertEqual(pd.processing_info, exp)

    def test_samples(self):
        pd = ProcessedData(1)
        obs = pd.samples
        exp = {
            '1.SKB2.640194', '1.SKM4.640180', '1.SKB3.640195', '1.SKB6.640176',
            '1.SKD6.640190', '1.SKM6.640187', '1.SKD9.640182', '1.SKM8.640201',
            '1.SKM2.640199', '1.SKD2.640178', '1.SKB7.640196', '1.SKD4.640185',
            '1.SKB8.640193', '1.SKM3.640197', '1.SKD5.640186', '1.SKB1.640202',
            '1.SKM1.640183', '1.SKD1.640179', '1.SKD3.640198', '1.SKB5.640181',
            '1.SKB4.640189', '1.SKB9.640200', '1.SKM9.640192', '1.SKD8.640184',
            '1.SKM5.640177', '1.SKM7.640188', '1.SKD7.640191'}
        self.assertEqual(obs, exp)

    def test_status(self):
        pd = ProcessedData(1)
        self.assertEqual(pd.status, 'private')

        pd = ProcessedData.create(self.params_table, self.params_id,
                                  self.filepaths,
                                  preprocessed_data=self.preprocessed_data)
        self.assertEqual(pd.status, 'sandbox')

    def test_status_setter(self):
        pd = ProcessedData(1)
        self.assertEqual(pd.status, 'private')

        pd.status = 'sandbox'
        self.assertEqual(pd.status, 'sandbox')

    def test_status_setter_error(self):
        pd = ProcessedData(1)
        pd.status = 'public'
        self.assertEqual(pd.status, 'public')

        with self.assertRaises(QiitaDBStatusError):
            pd.status = 'sandbox'

    def test_status_setter_error_not_existant(self):
        pd = ProcessedData(1)
        with self.assertRaises(QiitaDBLookupError):
            pd.status = 'does-not-exist'

    def test_get_by_status(self):
        pds = ProcessedData.get_by_status('sandbox')
        self.assertEqual(pds, set())

        pds = ProcessedData.get_by_status('private')
        self.assertEqual(pds, set([1]))

        ProcessedData.create(self.params_table, self.params_id,
                             self.filepaths,
                             preprocessed_data=self.preprocessed_data)
        pds = ProcessedData.get_by_status('sandbox')
        self.assertEqual(pds, set([2]))

        pds = ProcessedData.get_by_status('private')
        self.assertEqual(pds, set([1]))

    def test_get_by_status_grouped_by_study(self):
        obs = ProcessedData.get_by_status_grouped_by_study('sandbox')
        self.assertEqual(obs, dict())

        obs = ProcessedData.get_by_status_grouped_by_study('private')
        self.assertEqual(obs, {1: [1]})

        ProcessedData.create(self.params_table, self.params_id,
                             self.filepaths,
                             preprocessed_data=self.preprocessed_data)
        obs = ProcessedData.get_by_status_grouped_by_study('sandbox')
        self.assertEqual(obs, {1: [2]})


if __name__ == '__main__':
    main()
