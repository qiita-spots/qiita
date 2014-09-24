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
        submission = EBISubmission('001', 'teststudy', 'test asbstract',
                                   'metagenome')
        xmlelement = submission.generate_study_xml()
        xml = minidom.parseString(ET.tostring(xmlelement))
        xmlstring = xml.toprettyxml(indent='  ', encoding='UTF-8')
        self.assertEqual(xmlstring, STUDYXML)

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
        submission = EBISubmission('001', 'teststudy', 'test asbstract',
                                   'metagenome')
        submission.add_sample('test1')
        submission.add_sample('test2')
        xmlelement = submission.generate_sample_xml()
        xml = minidom.parseString(ET.tostring(xmlelement))
        xmlstring = xml.toprettyxml(indent='  ', encoding='UTF-8')
        self.assertEqual(xmlstring, SAMPLEXML)

    def test_add_sample_prep(self):
        submission = EBISubmission('001', 'teststudy', 'test asbstract',
                                   'metagenome')
        submission.add_sample('test1')
        submission.add_sample('test2')
        submission.add_sample_prep('test1', 'ILLUMINA', 'fastq',
                                   'fakepath', 'experiment description',
                                   'library protocol')
        prep_info = submission.samples['test1']['preps'][0]
        self.assertEqual(prep_info['platform'], 'ILLUMINA')
        self.assertEqual(prep_info['file_path'], 'fakepath')
        with self.assertRaises(KeyError):
            submission.add_sample_prep('test3', 'ILLUMINA', 'fastq',
                                       'fakepath', 'experiment description',
                                       'library protocol')

    def test__generate_library_descriptor(self):
        # raise NotImplementedError()
        pass

    def test__generate_spot_descriptor(self):
        # raise NotImplementedError()
        pass

    def test_generate_experiment_xml(self):
        submission = EBISubmission('001', 'teststudy', 'test asbstract',
                                   'metagenome')
        submission.add_sample('test1')
        submission.add_sample_prep('test1', 'ILLUMINA', 'fastq',
                                   'fakepath', 'experiment description',
                                   'library protocol')
        xmlelement = submission.generate_experiment_xml()
        xml = minidom.parseString(ET.tostring(xmlelement))
        xmlstring = xml.toprettyxml(indent='  ', encoding='UTF-8')
        self.assertEqual(xmlstring, EXPERIEMENTXML)

    def test_generate_run_xml(self):
        submission = EBISubmission('001', 'teststudy', 'test asbstract',
                                   'metagenome')
        submission.add_sample('test1')
        submission.add_sample_prep('test1', 'ILLUMINA', 'fastq',
                                   'fakepath', 'experiment description',
                                   'library protocol')
        xmlelement = submission.generate_run_xml()
        xml = minidom.parseString(ET.tostring(xmlelement))
        xmlstring = xml.toprettyxml(indent='  ', encoding='UTF-8')
        # waiting for checksum function to be done

    def test_generate_submission_xml(self):
        submission = EBISubmission('001', 'teststudy', 'test asbstract',
                                   'metagenome')
        submission.add_sample('test1')
        submission.add_sample_prep('test1', 'ILLUMINA', 'fastq',
                                   'fakepath', 'experiment description',
                                   'library protocol')
        with self.assertRaises(NoXMLError):
            xmlelement = submission.generate_submission_xml('VALIDATE')
        # add more tests

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


SAMPLEXML = """<?xml version="1.0" encoding="UTF-8"?>
<SAMPLE_SET xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noName\
spaceSchemaLocation="ftp://ftp.sra.ebi.ac.uk/meta/xsd/sra_1_3/SRA.sample.xsd">
  <SAMPLE alias="qiime_study_001:test1" center_name="CCME-COLORADO">
    <TITLE>test1</TITLE>
    <SAMPLE_NAME>
      <TAXON_ID>no_data</TAXON_ID>
    </SAMPLE_NAME>
    <DESCRIPTION>no_data</DESCRIPTION>
  </SAMPLE>
  <SAMPLE alias="qiime_study_001:test2" center_name="CCME-COLORADO">
    <TITLE>test2</TITLE>
    <SAMPLE_NAME>
      <TAXON_ID>no_data</TAXON_ID>
    </SAMPLE_NAME>
    <DESCRIPTION>no_data</DESCRIPTION>
  </SAMPLE>
</SAMPLE_SET>
"""

STUDYXML = """<?xml version="1.0" encoding="UTF-8"?>
<STUDY_SET xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noName\
spaceSchemaLocation="ftp://ftp.sra.ebi.ac.uk/meta/xsd/sra_1_3/SRA.study.xsd">
  <STUDY alias="qiime_study_001" center_name="CCME-COLORADO">
    <DESCRIPTOR>
      <STUDY_TITLE>teststudy</STUDY_TITLE>
      <STUDY_TYPE existing_study_type="metagenome"/>
      <STUDY_ABSTRACT>test asbstract</STUDY_ABSTRACT>
    </DESCRIPTOR>
  </STUDY>
</STUDY_SET>
"""

EXPERIEMENTXML = """<?xml version="1.0" encoding="UTF-8"?>
<EXPERIMENT_SET xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:no\
NamespaceSchemaLocation="ftp://ftp.sra.ebi.ac.uk/meta/xsd/sra_1_3/SRA.\
experiment.xsd">
  <EXPERIMENT alias="qiime_study_001:test1:0" center_name="CCME-COLORADO">
    <TITLE>qiime_study_001:test1:0</TITLE>
    <STUDY_REF refname="qiime_study_001"/>
    <DESIGN>
      <DESIGN_DESCRIPTION>experiment description</DESIGN_DESCRIPTION>
      <SAMPLE_DESCRIPTOR refname="qiime_study_001:test1"/>
      <LIBRARY_DESCRIPTOR>
        <LIBRARY_NAME>test1:0</LIBRARY_NAME>
        <LIBRARY_STRATEGY>POOLCLONE</LIBRARY_STRATEGY>
        <LIBRARY_SOURCE>METAGENOMIC</LIBRARY_SOURCE>
        <LIBRARY_SELECTION>unspecififed</LIBRARY_SELECTION>
        <LIBRARY_LAYOUT>
          <SINGLE/>
        </LIBRARY_LAYOUT>
        <LIBRARY_CONSTRUCTION_PROTOCOL>library protocol</LIBRARY_CONSTRUCTION\
_PROTOCOL>
      </LIBRARY_DESCRIPTOR>
    </DESIGN>
    <PLATFORM>
      <ILLUMINA>
        <INSTRUMENT_MODEL>unspecified</INSTRUMENT_MODEL>
      </ILLUMINA>
    </PLATFORM>
    <EXPERIMENT_ATTRIBUTES>
      <EXPERIMENT_ATTRIBUTE>
        <TAG>experiment_design_description</TAG>
        <VALUE>experiment description</VALUE>
      </EXPERIMENT_ATTRIBUTE>
      <EXPERIMENT_ATTRIBUTE>
        <TAG>file_path</TAG>
        <VALUE>fakepath</VALUE>
      </EXPERIMENT_ATTRIBUTE>
      <EXPERIMENT_ATTRIBUTE>
        <TAG>file_type</TAG>
        <VALUE>fastq</VALUE>
      </EXPERIMENT_ATTRIBUTE>
      <EXPERIMENT_ATTRIBUTE>
        <TAG>library_construction_protocol</TAG>
        <VALUE>library protocol</VALUE>
      </EXPERIMENT_ATTRIBUTE>
      <EXPERIMENT_ATTRIBUTE>
        <TAG>platform</TAG>
        <VALUE>ILLUMINA</VALUE>
      </EXPERIMENT_ATTRIBUTE>
    </EXPERIMENT_ATTRIBUTES>
  </EXPERIMENT>
</EXPERIMENT_SET>
"""

if __name__ == "__main__":
    main()
