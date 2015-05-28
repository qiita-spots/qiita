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
from qiita_db.study import Study, StudyPerson
from qiita_db.user import User
from qiita_db.util import get_count
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
            "portal_type_id": 3,
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
            User('test@foo.bar'), "Fried Chicken Microbiome", [1], info)
        self._clean_up_files = []

    def tearDown(self):
        for fp in self._clean_up_files:
            if exists(fp):
                remove(fp)

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
               "library_construction_protocol",
               "experiment_design_description"}
        self.assertEqual(set(obs_pt.categories()), exp)


QIIME_MAP = (
    "#SampleID\tBarcodeSequence\tLinkerPrimerSequence\t"
    "physical_specimen_location\tphysical_specimen_remaining\tdna_extracted\t"
    "sample_type\thost_subject_id\tlatitude\tlongitude\ttaxon_id\t"
    "scientific_name\tcenter_name\trun_prefix\tplatform\t"
    "library_construction_protocol\texperiment_design_description\t"
    "collection_timestamp\tDescription\n"
    "Sample1\tGTCCGCAAGTTA\tGTGCCAGCMGCCGCGGTAA\tUCSD\tTRUE\tTRUE\ttype1\t"
    "NotIdentified\t4.1\t4.1\t9606\thomo sapiens\tANL\trp_1\tILLUMINA\t"
    "protocol_1\tedd_1\t05/28/15 11:00\tDescription S1\n"
    "Sample2\tCGTAGAGCTCTC\tGTGCCAGCMGCCGCGGTAA\tUCSD\tTRUE\tTRUE\ttype2\t"
    "NotIdentified\t4.2\t4.2\t9606\thomo sapiens\tANL\trp_1\tILLUMINA\t"
    "protocol_1\tedd_1\t05/28/15 11:00\tDescription S2\n"
    "Sample3\tCCTCTGAGAGCT\tGTGCCAGCMGCCGCGGTAA\tUCSD\tTRUE\tTRUE\ttype3\t"
    "NotIdentified\t4.3\t4.3\t9606\thomo sapiens\tANL\trp_2\tILLUMINA\t"
    "protocol_1\tedd_1\t05/28/15 11:00\tDescription S3\n")


if __name__ == "__main__":
    main()
