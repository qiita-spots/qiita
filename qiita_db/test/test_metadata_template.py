# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import TestCase, main
from datetime import datetime
from tempfile import mkstemp
from os import close, remove

import pandas as pd

from qiita_core.util import qiita_test_checker
from qiita_core.exceptions import IncompetentQiitaDeveloperError
from qiita_db.study import Study
from qiita_db.metadata_template import (MetadataTemplate, SampleTemplate,
                                        PrepTemplate)


@qiita_test_checker()
class TestMetadataTemplate(TestCase):
    """Tests the MetadataTemplate base class"""
    def setUp(self):
        self.study = Study(1)
        self.metadata = pd.DataFrame.from_dict({})

    def test_create(self):
        """Create raises an error because it's not called from a subclass"""
        with self.assertRaises(IncompetentQiitaDeveloperError):
            MetadataTemplate.create(self.metadata, self.study)


# @qiita_test_checker()
# class TestSampleTemplate(TestCase):
#     """Tests the SampleTemplate class"""

#     def setUp(self):
#         metadata_dict = {
#             'Sample1': {'physical_location': 'location1',
#                         'has_physical_specimen': True,
#                         'has_extracted_data': True,
#                         'sample_type': 'type1',
#                         'required_sample_info_status_id': 1,
#                         'collection_timestamp':
#                             datetime(2014, 5, 29, 12, 24, 51),
#                         'host_subject_id': 'NotIdentified',
#                         'description': 'Test Sample 1'},
#             'Sample2': {'physical_location': 'location1',
#                         'has_physical_specimen': True,
#                         'has_extracted_data': True,
#                         'sample_type': 'type1',
#                         'required_sample_info_status_id': 1,
#                         'collection_timestamp':
#                             datetime(2014, 5, 29, 12, 24, 51),
#                         'host_subject_id': 'NotIdentified',
#                         'description': 'Test Sample2'},
#             'Sample3': {'physical_location': 'location1',
#                         'has_physical_specimen': True,
#                         'has_extracted_data': True,
#                         'sample_type': 'type1',
#                         'required_sample_info_status_id': 1,
#                         'collection_timestamp':
#                             datetime(2014, 5, 29, 12, 24, 51),
#                         'host_subject_id': 'NotIdentified',
#                         'description': 'Test Sample 3'}
#         }
#         self.metadata = pd.DataFrame.from_dict(metadata_dict, orient='index')
#         self.test_study = Study(1)
#         # self.new_study = Study.create()

#     def test_exists_true(self):
#         self.assertTrue(SampleTemplate.exists(self.test_study))

#     def test_exists_false(self):
#         self.assertFalse(SampleTemplate.exists(Study(2)))

#     def test_create_duplicate(self):
#         SampleTemplate.create(self.metadata, self.test_study)


@qiita_test_checker()
class TestPrepTemplate(TestCase):
    """Tests the PrepTemplate class"""

    def setUp(self):
        metamap = {
            'SKB8.640193': {'center_name': 'ANL',
                            'center_project_name': 'ANL_name_1',
                            'emp_status_id': 1,
                            'data_type_id': 2},
            'SKD8.640184': {'center_name': 'ANL',
                            'center_project_name': 'ANL_name_1',
                            'emp_status_id': 1,
                            'data_type_id': 2},
            'SKB7.640196': {'center_name': 'ANL',
                            'center_project_name': 'ANL_name_1',
                            'emp_status_id': 1,
                            'data_type_id': 2}
        }
        self.metadata = pd.DataFrame.from_dict(metamap, orient='index')
        self._clean_up_files = []

    def tearDown(self):
        map(remove, self._clean_up_files)


if __name__ == '__main__':
    main()
