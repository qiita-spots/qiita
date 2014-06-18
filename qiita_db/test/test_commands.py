# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import TestCase, main
from os.path import join, dirname

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
        self.samp_temp_path = join(dirname(__file__), 'test_data',
                                   'sample_template.txt')

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
        st = sample_template_adder(self.samp_temp_path, self.study.id)
        self.assertEqual(st.id, self.study.id)


if __name__ == '__main__':
    main()
