#!/usr/bin/env python

from __future__ import division

# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import TestCase, main
from xml.etree import ElementTree as ET
from xml.dom import minidom

from qiita_ware.ebi import (InvalidMetadataError, SampleAlreadyExistsError,
                            NoXMLError, EBISubmission)


class TestEBISubmission(TestCase):
    def test___init__(self):
        # raise NotImplementedError()
        pass

    def test__stringify_kwargs(self):
        # raise NotImplementedError()
        pass

    def test__get_study_alias(self):
        # raise NotImplementedError()
        pass

    def test__get_sample_alias(self):
        # raise NotImplementedError()
        pass

    def test__get_experiment_alias(self):
        # raise NotImplementedError()
        pass

    def test__get_submission_alias(self):
        # raise NotImplementedError()
        pass

    def test__get_library_name(self):
        # raise NotImplementedError()
        pass

    def test__add_dict_as_tags_and_values(self):
        # raise NotImplementedError()
        pass

    def test_generate_study_xml(self):
        # raise NotImplementedError()
        pass

    def test_add_sample(self):
        submission = EBISubmission('001', 'teststudy', 'test asbstract',
                                   'metagenome')
        submission.add_sample('test1')
        submission.add_sample('test2')
        samples = submission.samples
        self.assertTrue('test1' in samples and 'test2' in samples)
        with self.assertRaises(SampleAlreadyExistsError):
            submission.add_sample('test1')

    def test_generate_sample_xml(self):
        # submission = EBISubmission('001', 'teststudy', 'test asbstract',
        #                            'metagenome')
        # submission.add_sample('test1')
        # submission.add_sample('test2')
        # xmlelement = submission.generate_sample_xml()
        # #print minidom.parseString(ET.tostring(xmlelement))
        pass

    def test_add_sample_prep(self):
        # raise NotImplementedError()
        pass

    def test__generate_library_descriptor(self):
        # raise NotImplementedError()
        pass

    def test__generate_spot_descriptor(self):
        # raise NotImplementedError()
        pass

    def test_generate_experiment_xml(self):
        # raise NotImplementedError()
        pass

    def test_generate_run_xml(self):
        # raise NotImplementedError()
        pass

    def test_generate_submission_xml(self):
        # raise NotImplementedError()
        pass

    def test__write_xml_file(self):
        # raise NotImplementedError()
        pass

    def test_write_study_xml(self):
        # raise NotImplementedError()
        pass

    def test_write_sample_xml(self):
        # raise NotImplementedError()
        pass

    def test_write_experiment_xml(self):
        # raise NotImplementedError()
        pass

    def test_write_run_xml(self):
        # raise NotImplementedError()
        pass

    def test_write_submission_xml(self):
        # raise NotImplementedError()
        pass

    def test_write_all_xml_files(self):
        # raise NotImplementedError()
        pass

    def test_add_samples_from_templates(self):
        # raise NotImplementedError()
        pass

    def test_from_templates_and_demux_fastq(self):
        # raise NotImplementedError()
        pass

    def test_from_templates_and_per_sample_fastqs(self):
        # raise NotImplementedError()
        pass


if __name__ == "__main__":
    main()
