# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from StringIO import StringIO
from unittest import TestCase, main
from os import remove
from os.path import exists

from qiita_core.util import qiita_test_checker
from qiita_ware.exceptions import QiitaWareError
from qiita_db.study import Study, StudyPerson
from qiita_db.user import User
from qiita_db.util import get_count
from qiita_db.metadata_template.sample_template import SampleTemplate
from qiita_db.metadata_template.prep_template import PrepTemplate
from qiita_ware.metadata_pipeline import (
    create_templates_from_qiime_mapping_file)


@qiita_test_checker()
class TestMetadataPipeline(TestCase):
    def setUp(self):
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
        self.new_study = Study.create(
            User('test@foo.bar'), "Fried Chicken Microbiome", info)
        self._clean_up_files = []

    def tearDown(self):
        for fp in self._clean_up_files:
            if exists(fp):
                remove(fp)

        study_id = self.new_study.id
        for pt in self.new_study.prep_templates():
            PrepTemplate.delete(pt.id)
        if SampleTemplate.exists(study_id):
            SampleTemplate.delete(study_id)
        Study.delete(study_id)

    def test_create_templates_from_qiime_mapping_file(self):
        new_pt_id = get_count('qiita.prep_template') + 1
        obs_st, obs_pt = create_templates_from_qiime_mapping_file(
            StringIO(QIIME_MAP), self.new_study, "16S")

        # Be green: clean the environment
        for template in [obs_st, obs_pt]:
            for _, fp in template.get_filepaths():
                self._clean_up_files.append(fp)

        self.assertEqual(obs_st.id, self.new_study.id)
        self.assertEqual(obs_pt.id, new_pt_id)

        # Check that each template has the correct columns
        exp = {"physical_specimen_location", "physical_specimen_remaining",
               "dna_extracted", "sample_type", "host_subject_id", "latitude",
               "longitude", "taxon_id", "scientific_name",
               "collection_timestamp", "description"}
        self.assertEqual(set(obs_st.categories()), exp)

        exp = {"barcode", "primer", "center_name", "run_prefix", "platform",
               "library_construction_protocol", "instrument_model",
               "experiment_design_description"}
        self.assertEqual(set(obs_pt.categories()), exp)

    def test_create_templates_from_qiime_mapping_file_reverse_linker(self):
        curr_id = self.conn_handler.execute_fetchone(
            "SELECT last_value FROM "
            "qiita.prep_template_prep_template_id_seq")[0]
        obs_st, obs_pt = create_templates_from_qiime_mapping_file(
            StringIO(QIIME_MAP_WITH_REVERSE_LINKER_PRIMER),
            self.new_study, "16S")

        # Be green: clean the environment
        for template in [obs_st, obs_pt]:
            for _, fp in template.get_filepaths():
                self._clean_up_files.append(fp)

        self.assertEqual(obs_st.id, self.new_study.id)
        self.assertEqual(obs_pt.id, curr_id + 1)

        # Check that each template has the correct columns
        exp = {"physical_specimen_location", "physical_specimen_remaining",
               "dna_extracted", "sample_type", "host_subject_id", "latitude",
               "longitude", "taxon_id", "scientific_name",
               "collection_timestamp", "description"}
        self.assertEqual(set(obs_st.categories()), exp)

        exp = {"barcode", "primer", "center_name", "run_prefix", "platform",
               "library_construction_protocol", "instrument_model",
               "experiment_design_description", "reverselinkerprimer"}
        self.assertEqual(set(obs_pt.categories()), exp)

    def test_create_templates_from_qiime_mapping_file_error(self):
        with self.assertRaises(QiitaWareError):
            create_templates_from_qiime_mapping_file(
                StringIO(QIIME_MAP_ERROR), self.new_study, "16S")


QIIME_MAP = (
    u"#SampleID\tBarcodeSequence\tLinkerPrimerSequence\tinstrument_model\t"
    "physical_specimen_location\tphysical_specimen_remaining\tdna_extracted\t"
    "sample_type\thost_subject_id\tlatitude\tlongitude\ttaxon_id\t"
    "scientific_name\tcenter_name\trun_prefix\tplatform\t"
    "library_construction_protocol\texperiment_design_description\t"
    "collection_timestamp\tDescription\n"
    "Sample1\tGTCCGCAAGTTA\tGTGCCAGCMGCCGCGGTAA\tIllumina MiSeq\tUCSD\tTRUE\t"
    "TRUE\ttype1\tNotIdentified\t4.1\t4.1\t9606\thomo sapiens\tANL\trp_1\t"
    "ILLUMINA\tprotocol_1\tedd_1\t05/28/15 11:00:00\tDescription S1\n"
    "Sample2\tCGTAGAGCTCTC\tGTGCCAGCMGCCGCGGTAA\tIllumina MiSeq\tUCSD\tTRUE\t"
    "TRUE\ttype2\tNotIdentified\t4.2\t4.2\t9606\thomo sapiens\tANL\trp_1\t"
    "ILLUMINA\tprotocol_1\tedd_1\t05/28/15 11:00:00\tDescription S2\n"
    "Sample3\tCCTCTGAGAGCT\tGTGCCAGCMGCCGCGGTAA\tIllumina MiSeq\tUCSD\tTRUE\t"
    "TRUE\ttype3\tNotIdentified\t4.3\t4.3\t9606\thomo sapiens\tANL\trp_2\t"
    "ILLUMINA\tprotocol_1\tedd_1\t05/28/15 11:00:00\tDescription S3\n")

QIIME_MAP_WITH_REVERSE_LINKER_PRIMER = (
    u"#SampleID\tBarcodeSequence\tLinkerPrimerSequence\tReverseLinkerPrimer\t"
    "physical_specimen_location\tphysical_specimen_remaining\tdna_extracted\t"
    "sample_type\thost_subject_id\tlatitude\tlongitude\ttaxon_id\t"
    "scientific_name\tcenter_name\trun_prefix\tplatform\tinstrument_model\t"
    "library_construction_protocol\texperiment_design_description\t"
    "collection_timestamp\tDescription\n"
    "Sample1\tGTCCGCAAGTTA\tGTGCCAGCMGCCGCGGTAA\tGTGCCAGCMGCCGCGGTAA\tUCSD\t"
    "TRUE\tTRUE\ttype1\tNotIdentified\t4.1\t4.1\t9606\thomo sapiens\tANL\t"
    "rp_1\tILLUMINA\tIllumina MiSeq\tprotocol_1\tedd_1\t05/28/15 11:00:00\t"
    "Description S1\n"
    "Sample2\tCGTAGAGCTCTC\tGTGCCAGCMGCCGCGGTAA\tGTGCCAGCMGCCGCGGTAA\tUCSD\t"
    "TRUE\tTRUE\ttype2\tNotIdentified\t4.2\t4.2\t9606\thomo sapiens\tANL\t"
    "rp_1\tILLUMINA\tIllumina MiSeq\tprotocol_1\tedd_1\t05/28/15 11:00:00\t"
    "Description S2\n"
    "Sample3\tCCTCTGAGAGCT\tGTGCCAGCMGCCGCGGTAA\tGTGCCAGCMGCCGCGGTAA\tUCSD\t"
    "TRUE\tTRUE\ttype3\tNotIdentified\t4.3\t4.3\t9606\thomo sapiens\tANL\t"
    "rp_2\tILLUMINA\tIllumina MiSeq\tprotocol_1\tedd_1\t05/28/15 11:00:00\t"
    "Description S3\n")

QIIME_MAP_ERROR = (
    u"#SampleID\tBarcodeSequence\tphysical_specimen_location\t"
    "physical_specimen_remaining\tdna_extracted\tsample_type\t"
    "host_subject_id\tlatitude\tlongitude\ttaxon_id\tscientific_name\t"
    "center_name\trun_prefix\tplatform\tlibrary_construction_protocol\t"
    "experiment_design_description\tcollection_timestamp\tDescription\n"
    "Sample1\tGTCCGCAAGTTA\tUCSD\tTRUE\tTRUE\ttype1\tNotIdentified\t4.1\t4.1\t"
    "9606\thomo sapiens\tANL\trp_1\tILLUMINA\tprotocol_1\tedd_1\t"
    "05/28/15 11:00:00\tDescription S1\n"
    "Sample2\tCGTAGAGCTCTC\tUCSD\tTRUE\tTRUE\ttype2\tNotIdentified\t4.2\t4.2\t"
    "9606\thomo sapiens\tANL\trp_1\tILLUMINA\tprotocol_1\tedd_1\t"
    "05/28/15 11:00:00\tDescription S2\n"
    "Sample3\tCCTCTGAGAGCT\tUCSD\tTRUE\tTRUE\ttype3\tNotIdentified\t4.3\t4.3\t"
    "9606\thomo sapiens\tANL\trp_2\tILLUMINA\tprotocol_1\tedd_1\t"
    "05/28/15 11:00:00\tDescription S3\n")


if __name__ == "__main__":
    main()
