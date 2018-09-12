# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import TestCase, main

from qiita_core.exceptions import IncompetentQiitaDeveloperError
import qiita_db as qdb


class TestBaseSample(TestCase):
    """Tests the BaseSample class"""

    def test_init(self):
        """BaseSample init should raise an error (it's a base class)"""
        with self.assertRaises(IncompetentQiitaDeveloperError):
            qdb.metadata_template.base_metadata_template.BaseSample(
                'SKM7.640188',
                qdb.metadata_template.sample_template.SampleTemplate(1))

    def test_exists(self):
        """exists should raise an error if called from the base class"""
        with self.assertRaises(IncompetentQiitaDeveloperError):
            qdb.metadata_template.base_metadata_template.BaseSample.exists(
                'SKM7.640188',
                qdb.metadata_template.sample_template.SampleTemplate(1))


class TestMetadataTemplateReadOnly(TestCase):
    """Tests the MetadataTemplate base class"""
    def setUp(self):
        self.study = qdb.study.Study(1)

    def test_init(self):
        """Init raises an error because it's not called from a subclass"""
        MT = qdb.metadata_template.base_metadata_template.MetadataTemplate
        with self.assertRaises(IncompetentQiitaDeveloperError):
            MT(1)

    def test_exist(self):
        """Exists raises an error because it's not called from a subclass"""
        MT = qdb.metadata_template.base_metadata_template.MetadataTemplate
        with self.assertRaises(IncompetentQiitaDeveloperError):
            MT.exists(self.study)

    def test_table_name(self):
        """table name raises an error because it's not called from a subclass
        """
        MT = qdb.metadata_template.base_metadata_template.MetadataTemplate
        with self.assertRaises(IncompetentQiitaDeveloperError):
            MT._table_name(self.study)

    def test_common_creation_steps(self):
        """common_creation_steps raises an error from base class
        """
        MT = qdb.metadata_template.base_metadata_template.MetadataTemplate
        with self.assertRaises(IncompetentQiitaDeveloperError):
            MT._common_creation_steps(None, 1)

    def test_clean_validate_template(self):
        """_clean_validate_template raises an error from base class"""
        MT = qdb.metadata_template.base_metadata_template.MetadataTemplate
        with self.assertRaises(IncompetentQiitaDeveloperError):
            MT._clean_validate_template(None, 1)


if __name__ == '__main__':
    main()
