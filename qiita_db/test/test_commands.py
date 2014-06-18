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

from qiita_core.util import qiita_test_checker
from qiita_db.study import Study, StudyPerson
from qiita_db.user import User
from qiita_db.commands import sample_template_adder


@qiita_test_checker()
class SampleTemplateAdderTests(TestCase):
    """"""

    def setUp(self):
        """"""
        # Create a sample template file
        fd, self.samp_temp_path = mkstemp(suffix='_sample_temp.txt')
        close(fd)
        with open(self.samp_temp_path, 'U') as f:
            f.write(
                "#SampleID\tBarcodeSequence\tLinkerPrimerSequence\tTreatment\t"
                "DOB\tDescription\n#Example mapping file for Qiita.  These 4 "
                "samples are from a study of the effects of exercise and diet "
                "on mouse cardiac physiology (Crawford, et al, PNAS, 2009).\n"
                "PC.354\tAGCACGAGCCTA\tYATGCTGCCTCCCGTAGGAGT\tControl\t"
                "20061218\tControl_mouse_I.D._354\nPC.355\tAACTCGTCGATG\t"
                "YATGCTGCCTCCCGTAGGAGT\tControl\t20061218\t"
                "Control_mouse_I.D._355\nPC.635\tACCGCAGAGTCA\t"
                "YATGCTGCCTCCCGTAGGAGT\tFast\t20080116\tFasting_mouse_I.D._635"
                "\nPC.636\tACGGTGAGTGTC\tYATGCTGCCTCCCGTAGGAGT\tFast\t20080116"
                "\tFasting_mouse_I.D._636\n")
        self._clean_up_files = [self.samp_temp_path]

        # create a new study to attach the sample template
        info = {
            "timeseries_type_id": 1,
            "metadata_complete": True,
            "mixs_compliant": True,
            "number_samples_collected": 4,
            "number_samples_promised": 4,
            "portal_type_id": 3,
            "study_alias": "CrawfordPNAS2009",
            "study_description": "More info at Crawford, et al, PNAS, 2009",
            "study_abstract": "Example mapping file for Qiita.  These 4 "
                              "samples are from a study of the effects of "
                              "exercise and diet on mouse cardiac physiology "
                              "(Crawford, et al, PNAS, 2009).",
            "emp_person_id": StudyPerson(2),
            "principal_investigator_id": StudyPerson(3),
            "lab_person_id": StudyPerson(1)
        }
        self.study_id = Study.create(User('test@foo.bar'),
                                     "Fried Chicken Microbiome", [1], info)

    def tearDown(self):
        for f in self._clean_up_files:
            remove(f)

    def test_sample_template_adder(self):
        """Correctly adds a sample template to the DB"""
        st = sample_template_adder(self.samp_temp_path, self.study_id)
        self.assertEqual(st.id, self.study_id)


if __name__ == '__main__':
    main()
