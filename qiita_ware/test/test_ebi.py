#!/usr/bin/env python

from __future__ import division

# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from warnings import simplefilter
from os import remove
from os.path import join, isdir
from shutil import rmtree
from tempfile import mkdtemp
from unittest import TestCase, main
from xml.etree import ElementTree as ET
from functools import partial
import pandas as pd
from datetime import date

from h5py import File

from qiita_ware.ebi import EBISubmission
from qiita_ware.exceptions import EBISubmissionError
from qiita_ware.demux import to_hdf5
from qiita_core.qiita_settings import qiita_config
from qiita_db.data import PreprocessedData
from qiita_db.study import Study
from qiita_db.metadata_template import PrepTemplate
from qiita_core.util import qiita_test_checker


class TestEBISubmission(TestCase):
    def setUp(self):
        self.files_to_remove = []
        self.temp_dir = mkdtemp()
        self.files_to_remove.append(self.temp_dir)

    def tearDown(self):
        for f in self.files_to_remove:
            if isdir(f):
                rmtree(f)
            else:
                remove(f)


class TestEBISubmissionReadOnly(TestEBISubmission):
    def test_init(self):
        ppd_id = 2
        action = 'ADD'

        e = EBISubmission(ppd_id, action)

        self.assertEqual(e.preprocessed_data_id, ppd_id)
        self.assertEqual(e.study_title, 'Identification of the Microbiomes '
                                        'for Cannabis Soils')
        self.assertEqual(e.study_abstract,
                         ('This is a preliminary study to examine the '
                          'microbiota associated with the Cannabis plant. '
                          'Soils samples from the bulk soil, soil associated '
                          'with the roots, and the rhizosphere were extracted '
                          'and the DNA sequenced. Roots from three '
                          'independent plants of different strains were '
                          'examined. These roots were obtained November 11, '
                          '2011 from plants that had been harvested in the '
                          'summer. Future studies will attempt to analyze the '
                          'soils and rhizospheres from the same location at '
                          'different time points in the plant lifecycle.'))
        self.assertEqual(e.investigation_type, 'Metagenomics')
        self.assertIsNone(e.new_investigation_type)
        self.assertItemsEqual(e.sample_template, e.samples)
        self.assertItemsEqual(e.pmids, ['123456', '7891011'])
        self.assertEqual(e.action, action)

        get_output_fp = partial(join, e.ebi_dir, 'xml_dir')
        self.assertEqual(e.xml_dir, get_output_fp())
        self.assertEqual(e.study_xml_fp, get_output_fp('study.xml'))
        self.assertEqual(e.sample_xml_fp, get_output_fp('sample.xml'))
        self.assertEqual(e.experiment_xml_fp,  get_output_fp('experiment.xml'))
        self.assertEqual(e.run_xml_fp, get_output_fp('run.xml'))
        self.assertEqual(e.submission_xml_fp, get_output_fp('submission.xml'))

        get_output_fp = partial(join, e.ebi_dir)
        self.assertEqual(e.ebi_dir, get_output_fp())
        for sample in e.sample_template:
            self.assertEqual(e.sample_template[sample], e.samples[sample])
            self.assertEqual(e.prep_template[sample], e.samples_prep[sample])
            self.assertEqual(e.sample_demux_fps[sample],
                             get_output_fp('%s.fastq.gz' % sample))

    def test_get_study_alias(self):
        e = EBISubmission(2, 'ADD')
        exp = '%s_sid_1' % qiita_config.ebi_organization_prefix
        self.assertEqual(e._get_study_alias(), exp)

    def test_get_sample_alias(self):
        e = EBISubmission(2, 'ADD')
        exp = '%s_sid_1:foo' % qiita_config.ebi_organization_prefix
        self.assertEqual(e._get_sample_alias('foo'), exp)
        self.assertEqual(e._sample_aliases, {exp: 'foo'})

    def test_get_experiment_alias(self):
        e = EBISubmission(2, 'ADD')
        exp = '%s_ptid_1:foo' % qiita_config.ebi_organization_prefix
        self.assertEqual(e._get_experiment_alias('foo'), exp)
        self.assertEqual(e._experiment_aliases, {exp: 'foo'})

    def test_get_submission_alias(self):
        e = EBISubmission(2, 'ADD')
        obs = e._get_submission_alias()
        exp = '%s_submission_2' % qiita_config.ebi_organization_prefix
        self.assertEqual(obs, exp)

    def test_get_run_alias(self):
        e = EBISubmission(2, 'ADD')
        exp = '%s_ppdid_2:foo' % qiita_config.ebi_organization_prefix
        self.assertEqual(e._get_run_alias('foo'), exp)
        self.assertEqual(e._run_aliases, {exp: 'foo'})

    def test_get_library_name(self):
        e = EBISubmission(2, 'ADD')
        obs = e._get_library_name("nasty<business>")
        exp = "nasty&lt;business&gt;"
        self.assertEqual(obs, exp)

    def test_add_dict_as_tags_and_values(self):
        e = EBISubmission(2, 'ADD')
        elm = ET.Element('TESTING', {'foo': 'bar'})

        e._add_dict_as_tags_and_values(elm, 'foo', {'x': 'y', '>x': '<y'})
        obs = ET.tostring(elm)
        exp = ''.join([v.strip() for v in ADDDICTTEST.splitlines()])
        self.assertEqual(obs, exp)

    def test_generate_study_xml(self):
        submission = EBISubmission(2, 'ADD')
        obs = ET.tostring(submission.generate_study_xml())
        exp = ''.join([l.strip() for l in STUDYXML.splitlines()])
        self.assertEqual(obs, exp)

    def test_generate_sample_xml(self):
        submission = EBISubmission(2, 'ADD')
        # removing samples so test text is easier to read
        keys_to_del = ['1.SKD6.640190', '1.SKM6.640187', '1.SKD9.640182',
                       '1.SKM8.640201', '1.SKM2.640199', '1.SKD2.640178',
                       '1.SKB7.640196', '1.SKD4.640185', '1.SKB8.640193',
                       '1.SKM3.640197', '1.SKD5.640186', '1.SKB1.640202',
                       '1.SKM1.640183', '1.SKD1.640179', '1.SKD3.640198',
                       '1.SKB5.640181', '1.SKB4.640189', '1.SKB9.640200',
                       '1.SKM9.640192', '1.SKD8.640184', '1.SKM5.640177',
                       '1.SKM7.640188', '1.SKD7.640191', '1.SKB6.640176',
                       '1.SKM4.640180']
        for k in keys_to_del:
            del(submission.samples[k])
            del(submission.samples_prep[k])
        obs = ET.tostring(submission.generate_sample_xml())
        exp = ''.join([l.strip() for l in SAMPLEXML.splitlines()])
        self.assertEqual(obs, exp)

    def test_generate_experiment_xml(self):
        submission = EBISubmission(2, 'ADD')
        # removing samples so test text is easier to read
        keys_to_del = ['1.SKD6.640190', '1.SKM6.640187', '1.SKD9.640182',
                       '1.SKM8.640201', '1.SKM2.640199', '1.SKD2.640178',
                       '1.SKB7.640196', '1.SKD4.640185', '1.SKB8.640193',
                       '1.SKM3.640197', '1.SKD5.640186', '1.SKB1.640202',
                       '1.SKM1.640183', '1.SKD1.640179', '1.SKD3.640198',
                       '1.SKB5.640181', '1.SKB4.640189', '1.SKB9.640200',
                       '1.SKM9.640192', '1.SKD8.640184', '1.SKM5.640177',
                       '1.SKM7.640188', '1.SKD7.640191', '1.SKB6.640176',
                       '1.SKM4.640180']
        for k in keys_to_del:
            del(submission.samples[k])
            del(submission.samples_prep[k])

        obs = ET.tostring(submission.generate_experiment_xml())
        exp = EXPERIMENTXML % {
            'organization_prefix': qiita_config.ebi_organization_prefix}
        exp = ''.join([l.strip() for l in exp.splitlines()])
        self.assertEqual(obs, exp)

    def test_generate_spot_descriptor(self):
        e = EBISubmission(2, 'ADD')
        elm = ET.Element('design', {'foo': 'bar'})

        e._generate_spot_descriptor(elm, 'LS454')
        exp = ''.join([l.strip() for l in GENSPOTDESC.splitlines()])
        obs = ET.tostring(elm)
        self.assertEqual(obs, exp)

    def test_generate_submission_xml(self):
        submission = EBISubmission(2, 'ADD')
        obs = ET.tostring(
            submission.generate_submission_xml(
                submission_date=date(2015, 9, 3)))
        exp = SUBMISSIONXML % {
            'submission_alias': submission._get_submission_alias(),
            'center_name': qiita_config.ebi_center_name}
        exp = ''.join([l.strip() for l in exp.splitlines()])
        self.assertEqual(obs, exp)

    def test_write_xml_file(self):
        element = ET.Element('TESTING', {'foo': 'bar'})
        e = EBISubmission(2, 'ADD')
        e.write_xml_file(element, 'testfile')
        self.files_to_remove.append('testfile')

        obs = open('testfile').read()
        exp = "<?xml version='1.0' encoding='UTF-8'?>\n<TESTING foo=\"bar\" />"
        self.assertEqual(obs, exp)

    def test_generate_curl_command(self):
        submission = EBISubmission(2, 'ADD')

        test_ebi_seq_xfer_user = 'ebi_seq_xfer_user'
        test_ebi_access_key = 'ebi_access_key'
        test_ebi_dropbox_url = 'ebi_dropbox_url'

        # Without curl certificate authentication
        test_ebi_skip_curl_cert = True
        obs = submission.generate_curl_command(test_ebi_seq_xfer_user,
                                               test_ebi_access_key,
                                               test_ebi_skip_curl_cert,
                                               test_ebi_dropbox_url)
        exp = ('curl -k '
               '-F "SUBMISSION=@%(xml_dir)s/submission.xml" '
               '-F "STUDY=@%(xml_dir)s/study.xml" '
               '-F "SAMPLE=@%(xml_dir)s/sample.xml" '
               '-F "RUN=@%(xml_dir)s/run.xml" '
               '-F "EXPERIMENT=@%(xml_dir)s/experiment.xml" '
               '"ebi_dropbox_url/?auth=ENA%%20ebi_seq_xfer_user'
               '%%20ebi_access_key"') % {'xml_dir': submission.xml_dir}
        self.assertEqual(obs, exp)

        # With curl certificate authentication
        test_ebi_skip_curl_cert = False
        obs = submission.generate_curl_command(test_ebi_seq_xfer_user,
                                               test_ebi_access_key,
                                               test_ebi_skip_curl_cert,
                                               test_ebi_dropbox_url)
        exp = ('curl '
               '-F "SUBMISSION=@%(xml_dir)s/submission.xml" '
               '-F "STUDY=@%(xml_dir)s/study.xml" '
               '-F "SAMPLE=@%(xml_dir)s/sample.xml" '
               '-F "RUN=@%(xml_dir)s/run.xml" '
               '-F "EXPERIMENT=@%(xml_dir)s/experiment.xml" '
               '"ebi_dropbox_url/?auth=ENA%%20ebi_seq_xfer_user'
               '%%20ebi_access_key"') % {'xml_dir': submission.xml_dir}
        self.assertEqual(obs, exp)


@qiita_test_checker()
class TestEBISubmissionWriteRead(TestEBISubmission):
    def write_demux_files(self, prep_template):
        """Writes a demux test file to avoid duplication of code"""
        fna_fp = join(self.temp_dir, 'seqs.fna')
        demux_fp = join(self.temp_dir, 'demux.seqs')
        with open(fna_fp, 'w') as f:
            f.write(FASTA_EXAMPLE)
        with File(demux_fp, "w") as f:
            to_hdf5(fna_fp, f)

        ppd = PreprocessedData.create(Study(1),
                                      "preprocessed_sequence_illumina_params",
                                      1, [(demux_fp, 6)], prep_template)

        return ppd

    def generate_new_prep_template_and_write_demux_files(self,
                                                         valid_metadata=False):
        """Creates new prep-template/demux-file to avoid duplication of code"""

        # ignoring warnings generated when adding templates
        simplefilter("ignore")
        # creating prep template without required EBI submission columns
        if not valid_metadata:
            metadata_dict = {
                'SKD6.640190': {'center_name': 'ANL',
                                'center_project_name': 'Test Project'},
                'SKM6.640187': {'center_name': 'ANL',
                                'center_project_name': 'Test Project',
                                'platform': 'ILLUMINA',
                                'instrument_model': 'Not valid'},
                'SKD9.640182': {'center_name': 'ANL',
                                'center_project_name': 'Test Project',
                                'platform': 'ILLUMINA',
                                'instrument_model': 'Illumina MiSeq',
                                'primer': 'GTGCCAGCMGCCGCGGTAA',
                                'experiment_design_description':
                                    'microbiome of soil and rhizosphere',
                                'library_construction_protocol':
                                    'PMID: 22402401'}
            }
            investigation_type = None
        else:
            metadata_dict = {
                'SKD6.640190': {'center_name': 'ANL',
                                'center_project_name': 'Test Project',
                                'platform': 'ILLUMINA',
                                'instrument_model': 'Illumina MiSeq',
                                'primer': 'GTGCCAGCMGCCGCGGTAA',
                                'experiment_design_description':
                                    'microbiome of soil and rhizosphere',
                                'library_construction_protocol':
                                    'PMID: 22402401'},
                'SKM6.640187': {'center_name': 'ANL',
                                'center_project_name': 'Test Project',
                                'platform': 'ILLUMINA',
                                'instrument_model': 'Illumina MiSeq',
                                'primer': 'GTGCCAGCMGCCGCGGTAA',
                                'experiment_design_description':
                                    'microbiome of soil and rhizosphere',
                                'library_construction_protocol':
                                    'PMID: 22402401'},
                'SKD9.640182': {'center_name': 'ANL',
                                'center_project_name': 'Test Project',
                                'platform': 'ILLUMINA',
                                'instrument_model': 'Illumina MiSeq',
                                'primer': 'GTGCCAGCMGCCGCGGTAA',
                                'experiment_design_description':
                                    'microbiome of soil and rhizosphere',
                                'library_construction_protocol':
                                    'PMID: 22402401'}
            }
            investigation_type = "Metagenomics"
        metadata = pd.DataFrame.from_dict(metadata_dict, orient='index')
        pt = PrepTemplate.create(metadata, Study(1), "18S",
                                 investigation_type=investigation_type)
        ppd = self.write_demux_files(pt)

        return ppd

    def test_init_exceptions(self):
        # not a valid action
        with self.assertRaises(EBISubmissionError):
            EBISubmission(1, 'This is not a valid action')

        # already submitted so can't continue
        with self.assertRaises(EBISubmissionError):
            EBISubmission(1, 'ADD')

        ppd = self.generate_new_prep_template_and_write_demux_files()
        # raise error as we are missing columns
        exp_text = ("Errors found during EBI submission for study #1, "
                    "preprocessed data #3 and prep template #2:\nUnrecognized "
                    "investigation type: 'None'. This term is neither one of "
                    "the official terms nor one of the user-defined terms in "
                    "the ENA ontology.\nThese samples do not have a valid "
                    "platform (instrumet model wasn't checked): "
                    "1.SKD6.640190\nThese samples do not have a valid "
                    "instrument model: 1.SKM6.640187")
        with self.assertRaises(EBISubmissionError) as e:
            EBISubmission(ppd.id, 'ADD')
        self.assertEqual(exp_text, str(e.exception))

    def test_prep_with_less_samples_than_sample_template(self):
        # the next line generates a valid prep template with less samples than
        # the sample template and basically we want to test that
        # the EBISubmission can be generated
        ppd = self.generate_new_prep_template_and_write_demux_files(True)
        e = EBISubmission(ppd.id, 'ADD')
        exp = ['1.SKD6.640190', '1.SKM6.640187', '1.SKD9.640182']
        self.assertItemsEqual(exp, e.samples)

    def test_generate_run_xml(self):
        ppd = self.write_demux_files(PrepTemplate(1))
        submission = EBISubmission(ppd.id, 'ADD')

        # removing samples so test text is easier to read
        keys_to_del = ['1.SKD6.640190', '1.SKM6.640187', '1.SKD9.640182',
                       '1.SKM8.640201', '1.SKM2.640199']
        for k in keys_to_del:
            del(submission.samples[k])
            del(submission.samples_prep[k])

        submission.generate_demultiplexed_fastq(mtime=1)
        self.files_to_remove.append(submission.ebi_dir)
        obs = ET.tostring(submission.generate_run_xml())

        exp = RUNXML % {
            'study_alias': submission._get_study_alias(),
            'ebi_dir': submission.ebi_dir,
            'organization_prefix': qiita_config.ebi_organization_prefix,
            'center_name': qiita_config.ebi_center_name}
        exp = ''.join([l.strip() for l in exp.splitlines()])
        self.assertEqual(obs, exp)

    def test_generate_demultiplexed_fastq(self):
        # generating demux file for testing
        exp_demux_samples = set(
            ['1.SKD6.640190', '1.SKM6.640187', '1.SKD9.640182',
             '1.SKB2.640194', '1.SKM8.640201', '1.SKM4.640180',
             '1.SKM2.640199', '1.SKB3.640195', '1.SKB6.640176'])

        ppd = self.write_demux_files(PrepTemplate(1))
        # This is testing that only the samples with sequences are going to
        # be created
        ebi_submission = EBISubmission(ppd.id, 'ADD')
        obs_demux_samples = ebi_submission.generate_demultiplexed_fastq()
        self.files_to_remove.append(ebi_submission.ebi_dir)
        self.assertItemsEqual(obs_demux_samples, exp_demux_samples)
        # testing that the samples/samples_prep and demux_samples are the same
        self.assertItemsEqual(obs_demux_samples, ebi_submission.samples.keys())
        self.assertItemsEqual(obs_demux_samples,
                              ebi_submission.samples_prep.keys())

        # If the last test passed then we can test that the folder already
        # exists and that we have the same files and ignore not fastq.gz files
        ebi_submission = EBISubmission(ppd.id, 'ADD')
        obs_demux_samples = ebi_submission.generate_demultiplexed_fastq()
        self.assertItemsEqual(obs_demux_samples, exp_demux_samples)
        # testing that the samples/samples_prep and demux_samples are the same
        self.assertItemsEqual(obs_demux_samples, ebi_submission.samples.keys())
        self.assertItemsEqual(obs_demux_samples,
                              ebi_submission.samples_prep.keys())

    def test_generate_send_sequences_cmd(self):
        ppd = self.write_demux_files(PrepTemplate(1))
        e = EBISubmission(ppd.id, 'ADD')
        e.generate_demultiplexed_fastq()
        self.files_to_remove.append(e.ebi_dir)
        e.write_xml_file(e.generate_study_xml(), e.study_xml_fp)
        e.write_xml_file(e.generate_sample_xml(), e.sample_xml_fp)
        e.write_xml_file(e.generate_experiment_xml(), e.experiment_xml_fp)
        e.write_xml_file(e.generate_run_xml(), e.run_xml_fp)
        e.write_xml_file(e.generate_submission_xml(), e.submission_xml_fp)
        obs = e.generate_send_sequences_cmd()
        exp = ['ascp --ignore-host-key -L- -d -QT -k2 '
               '/tmp/ebi_submission_3/1.SKB2.640194.fastq.gz '
               'Webin-41528@webin.ebi.ac.uk:.//tmp/ebi_submission_3/',
               'ascp --ignore-host-key -L- -d -QT -k2 '
               '/tmp/ebi_submission_3/1.SKM4.640180.fastq.gz '
               'Webin-41528@webin.ebi.ac.uk:.//tmp/ebi_submission_3/',
               'ascp --ignore-host-key -L- -d -QT -k2 '
               '/tmp/ebi_submission_3/1.SKB3.640195.fastq.gz '
               'Webin-41528@webin.ebi.ac.uk:.//tmp/ebi_submission_3/',
               'ascp --ignore-host-key -L- -d -QT -k2 '
               '/tmp/ebi_submission_3/1.SKB6.640176.fastq.gz '
               'Webin-41528@webin.ebi.ac.uk:.//tmp/ebi_submission_3/',
               'ascp --ignore-host-key -L- -d -QT -k2 '
               '/tmp/ebi_submission_3/1.SKD6.640190.fastq.gz '
               'Webin-41528@webin.ebi.ac.uk:.//tmp/ebi_submission_3/',
               'ascp --ignore-host-key -L- -d -QT -k2 '
               '/tmp/ebi_submission_3/1.SKM6.640187.fastq.gz '
               'Webin-41528@webin.ebi.ac.uk:.//tmp/ebi_submission_3/',
               'ascp --ignore-host-key -L- -d -QT -k2 '
               '/tmp/ebi_submission_3/1.SKD9.640182.fastq.gz '
               'Webin-41528@webin.ebi.ac.uk:.//tmp/ebi_submission_3/',
               'ascp --ignore-host-key -L- -d -QT -k2 '
               '/tmp/ebi_submission_3/1.SKM8.640201.fastq.gz '
               'Webin-41528@webin.ebi.ac.uk:.//tmp/ebi_submission_3/',
               'ascp --ignore-host-key -L- -d -QT -k2 '
               '/tmp/ebi_submission_3/1.SKM2.640199.fastq.gz '
               'Webin-41528@webin.ebi.ac.uk:.//tmp/ebi_submission_3/']
        self.assertEqual(obs, exp)

    def test_parse_EBI_reply(self):
        ppd = self.write_demux_files(PrepTemplate(1))
        e = EBISubmission(ppd.id, 'ADD')

        # removing samples so test text is easier to read
        keys_to_del = ['1.SKD6.640190', '1.SKM6.640187', '1.SKD9.640182',
                       '1.SKM8.640201', '1.SKM2.640199', '1.SKB3.640195']
        for k in keys_to_del:
            del(e.samples[k])
            del(e.samples_prep[k])

        # Genereate the XML files so the aliases are generated
        # and stored internally
        e.generate_demultiplexed_fastq(mtime=1)
        e.generate_study_xml()
        e.generate_sample_xml()
        e.generate_experiment_xml()
        e.generate_run_xml()
        e.generate_submission_xml()

        curl_result = ""
        with self.assertRaises(EBISubmissionError):
            stacc, saacc, bioacc, exacc, runacc = e.parse_EBI_reply(
                curl_result)

        curl_result = 'success="true"'
        with self.assertRaises(EBISubmissionError):
            stacc, saacc, bioacc, exacc, runacc = e.parse_EBI_reply(
                curl_result)

        curl_result = ('some general text success="true" more text'
                       '<STUDY accession="staccession" some text> '
                       'some othe text'
                       '<SUBMISSION accession="sbaccession" some text>'
                       'some final text')
        with self.assertRaises(EBISubmissionError):
            stacc, saacc, bioacc, exacc, runacc = e.parse_EBI_reply(
                curl_result)

        curl_result = CURL_RESULT.format(qiita_config.ebi_organization_prefix,
                                         ppd.id)
        stacc, saacc, bioacc, exacc, runacc = e.parse_EBI_reply(curl_result)
        self.assertEqual(stacc, 'ERP000000')
        exp_saacc = {'1.SKB2.640194': 'ERS000000',
                     '1.SKB6.640176': 'ERS000001',
                     '1.SKM4.640180': 'ERS000002'}
        self.assertEqual(saacc, exp_saacc)
        exp_bioacc = {'1.SKB2.640194': 'SAMEA0000000',
                      '1.SKB6.640176': 'SAMEA0000001',
                      '1.SKM4.640180': 'SAMEA0000002'}
        self.assertEqual(bioacc, exp_bioacc)
        exp_exacc = {'1.SKB2.640194': 'ERX0000000',
                     '1.SKB6.640176': 'ERX0000001',
                     '1.SKM4.640180': 'ERX0000002'}
        self.assertEqual(exacc, exp_exacc)
        exp_runacc = {'1.SKB2.640194': 'ERR0000000',
                      '1.SKB6.640176': 'ERR0000001',
                      '1.SKM4.640180': 'ERR0000002'}
        self.assertEqual(runacc, exp_runacc)


FASTA_EXAMPLE = """>1.SKB2.640194_1 X orig_bc=X new_bc=X bc_diffs=0
CCACCCAGTAAC
>1.SKB2.640194_2 X orig_bc=X new_bc=X bc_diffs=0
CCACCCAGTAAC
>1.SKB2.640194_3 X orig_bc=X new_bc=X bc_diffs=0
CCACCCAGTAAC
>1.SKM4.640180_4 X orig_bc=X new_bc=X bc_diffs=0
CCACCCAGTAAC
>1.SKM4.640180_5 X orig_bc=X new_bc=X bc_diffs=0
CCACCCAGTAAC
>1.SKB3.640195_6 X orig_bc=X new_bc=X bc_diffs=0
CCACCCAGTAAC
>1.SKB6.640176_7 X orig_bc=X new_bc=X bc_diffs=0
CCACCCAGTAAC
>1.SKD6.640190_8 X orig_bc=X new_bc=X bc_diffs=0
CCACCCAGTAAC
>1.SKM6.640187_9 X orig_bc=X new_bc=X bc_diffs=0
CCACCCAGTAAC
>1.SKD9.640182_10 X orig_bc=X new_bc=X bc_diffs=0
CCACCCAGTAAC
>1.SKM8.640201_11 X orig_bc=X new_bc=X bc_diffs=0
CCACCCAGTAAC
>1.SKM2.640199_12 X orig_bc=X new_bc=X bc_diffs=0
CCACCCAGTAAC
"""

SAMPLEXML = """
<SAMPLE_SET xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noName\
spaceSchemaLocation="ftp://ftp.sra.ebi.ac.uk/meta/xsd/sra_1_3/SRA.sample.xsd">
  <SAMPLE alias="%(organization_prefix)s_sid_1:1.SKB2.640194" \
center_name="%(center_name)s">
      <TITLE>1.SKB2.640194</TITLE>
    <SAMPLE_NAME>
      <TAXON_ID>410658</TAXON_ID>
      <SCIENTIFIC_NAME>1118232</SCIENTIFIC_NAME>
    </SAMPLE_NAME>
    <DESCRIPTION>Cannabis Soil Microbiome</DESCRIPTION>
    <SAMPLE_ATTRIBUTES>
      <SAMPLE_ATTRIBUTE>
        <TAG>altitude</TAG><VALUE>0.0</VALUE>
      </SAMPLE_ATTRIBUTE>
      <SAMPLE_ATTRIBUTE>
        <TAG>anonymized_name</TAG><VALUE>SKB2</VALUE>
      </SAMPLE_ATTRIBUTE>
      <SAMPLE_ATTRIBUTE>
        <TAG>assigned_from_geo</TAG><VALUE>n</VALUE>
      </SAMPLE_ATTRIBUTE>
      <SAMPLE_ATTRIBUTE>
        <TAG>collection_timestamp</TAG><VALUE>2011-11-11 13:00:00</VALUE>
      </SAMPLE_ATTRIBUTE>
      <SAMPLE_ATTRIBUTE>
        <TAG>common_name</TAG><VALUE>soil metagenome</VALUE>
      </SAMPLE_ATTRIBUTE>
      <SAMPLE_ATTRIBUTE>
        <TAG>country</TAG><VALUE>GAZ:United States of America</VALUE>
      </SAMPLE_ATTRIBUTE><SAMPLE_ATTRIBUTE>
        <TAG>depth</TAG><VALUE>0.15</VALUE>
      </SAMPLE_ATTRIBUTE>
      <SAMPLE_ATTRIBUTE>
        <TAG>description_duplicate</TAG><VALUE>Burmese bulk</VALUE>
      </SAMPLE_ATTRIBUTE>
      <SAMPLE_ATTRIBUTE>
        <TAG>dna_extracted</TAG><VALUE>True</VALUE>
      </SAMPLE_ATTRIBUTE>
      <SAMPLE_ATTRIBUTE>
        <TAG>elevation</TAG><VALUE>114.0</VALUE>
      </SAMPLE_ATTRIBUTE>
      <SAMPLE_ATTRIBUTE>
        <TAG>env_biome</TAG><VALUE>ENVO:Temperate grasslands, savannas, and \
shrubland biome</VALUE>
      </SAMPLE_ATTRIBUTE>
      <SAMPLE_ATTRIBUTE>
        <TAG>env_feature</TAG><VALUE>ENVO:plant-associated habitat</VALUE>
      </SAMPLE_ATTRIBUTE>
      <SAMPLE_ATTRIBUTE>
        <TAG>host_subject_id</TAG><VALUE>1001:B4</VALUE>
      </SAMPLE_ATTRIBUTE>
      <SAMPLE_ATTRIBUTE>
        <TAG>host_taxid</TAG><VALUE>3483</VALUE>
      </SAMPLE_ATTRIBUTE>
      <SAMPLE_ATTRIBUTE>
        <TAG>latitude</TAG><VALUE>35.2374368957</VALUE>
      </SAMPLE_ATTRIBUTE>
      <SAMPLE_ATTRIBUTE>
        <TAG>longitude</TAG><VALUE>68.5041623253</VALUE>
      </SAMPLE_ATTRIBUTE>
      <SAMPLE_ATTRIBUTE>
        <TAG>ph</TAG><VALUE>6.94</VALUE>
      </SAMPLE_ATTRIBUTE>
      <SAMPLE_ATTRIBUTE>
        <TAG>physical_specimen_location</TAG><VALUE>ANL</VALUE>
      </SAMPLE_ATTRIBUTE>
      <SAMPLE_ATTRIBUTE>
        <TAG>physical_specimen_remaining</TAG><VALUE>True</VALUE>
      </SAMPLE_ATTRIBUTE>
      <SAMPLE_ATTRIBUTE>
        <TAG>samp_salinity</TAG><VALUE>7.15</VALUE>
      </SAMPLE_ATTRIBUTE>
      <SAMPLE_ATTRIBUTE>
        <TAG>sample_type</TAG><VALUE>ENVO:soil</VALUE>
      </SAMPLE_ATTRIBUTE>
      <SAMPLE_ATTRIBUTE>
        <TAG>season_environment</TAG><VALUE>winter</VALUE>
      </SAMPLE_ATTRIBUTE>
      <SAMPLE_ATTRIBUTE>
        <TAG>temp</TAG><VALUE>15.0</VALUE></SAMPLE_ATTRIBUTE>
      <SAMPLE_ATTRIBUTE>
        <TAG>texture</TAG><VALUE>64.6 sand, 17.6 silt, 17.8 clay</VALUE>
      </SAMPLE_ATTRIBUTE>
      <SAMPLE_ATTRIBUTE>
        <TAG>tot_nitro</TAG><VALUE>1.41</VALUE>
      </SAMPLE_ATTRIBUTE>
      <SAMPLE_ATTRIBUTE>
        <TAG>tot_org_carb</TAG><VALUE>5.0</VALUE>
      </SAMPLE_ATTRIBUTE>
      <SAMPLE_ATTRIBUTE>
        <TAG>water_content_soil</TAG><VALUE>0.164</VALUE>
      </SAMPLE_ATTRIBUTE>
    </SAMPLE_ATTRIBUTES>
  </SAMPLE>
  <SAMPLE alias="%(organization_prefix)s_sid_1:1.SKB3.640195" \
center_name="%(center_name)s">
    <TITLE>1.SKB3.640195</TITLE>
    <SAMPLE_NAME>
      <TAXON_ID>410658</TAXON_ID>
      <SCIENTIFIC_NAME>1118232</SCIENTIFIC_NAME>
    </SAMPLE_NAME>
    <DESCRIPTION>Cannabis Soil Microbiome</DESCRIPTION>
      <SAMPLE_ATTRIBUTES>
      <SAMPLE_ATTRIBUTE>
        <TAG>altitude</TAG><VALUE>0.0</VALUE>
      </SAMPLE_ATTRIBUTE>
      <SAMPLE_ATTRIBUTE>
        <TAG>anonymized_name</TAG><VALUE>SKB3</VALUE>
      </SAMPLE_ATTRIBUTE>
      <SAMPLE_ATTRIBUTE>
        <TAG>assigned_from_geo</TAG><VALUE>n</VALUE>
      </SAMPLE_ATTRIBUTE>
      <SAMPLE_ATTRIBUTE>
        <TAG>collection_timestamp</TAG><VALUE>2011-11-11 13:00:00</VALUE>
      </SAMPLE_ATTRIBUTE>
      <SAMPLE_ATTRIBUTE>
        <TAG>common_name</TAG><VALUE>soil metagenome</VALUE>
      </SAMPLE_ATTRIBUTE>
      <SAMPLE_ATTRIBUTE>
        <TAG>country</TAG><VALUE>GAZ:United States of America</VALUE>
      </SAMPLE_ATTRIBUTE>
      <SAMPLE_ATTRIBUTE>
        <TAG>depth</TAG><VALUE>0.15</VALUE>
      </SAMPLE_ATTRIBUTE>
      <SAMPLE_ATTRIBUTE>
        <TAG>description_duplicate</TAG><VALUE>Burmese bulk</VALUE>
      </SAMPLE_ATTRIBUTE>
      <SAMPLE_ATTRIBUTE>
        <TAG>dna_extracted</TAG><VALUE>True</VALUE>
      </SAMPLE_ATTRIBUTE>
      <SAMPLE_ATTRIBUTE>
        <TAG>elevation</TAG><VALUE>114.0</VALUE>
      </SAMPLE_ATTRIBUTE>
      <SAMPLE_ATTRIBUTE>
        <TAG>env_biome</TAG><VALUE>ENVO:Temperate grasslands, savannas, and \
shrubland biome</VALUE>
      </SAMPLE_ATTRIBUTE>
      <SAMPLE_ATTRIBUTE>
        <TAG>env_feature</TAG><VALUE>ENVO:plant-associated habitat</VALUE>
      </SAMPLE_ATTRIBUTE>
      <SAMPLE_ATTRIBUTE>
        <TAG>host_subject_id</TAG><VALUE>1001:M6</VALUE>
      </SAMPLE_ATTRIBUTE>
      <SAMPLE_ATTRIBUTE>
        <TAG>host_taxid</TAG><VALUE>3483</VALUE>
      </SAMPLE_ATTRIBUTE>
      <SAMPLE_ATTRIBUTE>
        <TAG>latitude</TAG><VALUE>95.2060749748</VALUE>
      </SAMPLE_ATTRIBUTE>
      <SAMPLE_ATTRIBUTE>
        <TAG>longitude</TAG><VALUE>27.3592668624</VALUE>
      </SAMPLE_ATTRIBUTE>
      <SAMPLE_ATTRIBUTE>
        <TAG>ph</TAG><VALUE>6.94</VALUE>
      </SAMPLE_ATTRIBUTE>
      <SAMPLE_ATTRIBUTE>
        <TAG>physical_specimen_location</TAG><VALUE>ANL</VALUE>
      </SAMPLE_ATTRIBUTE>
      <SAMPLE_ATTRIBUTE>
        <TAG>physical_specimen_remaining</TAG><VALUE>True</VALUE>
      </SAMPLE_ATTRIBUTE>
      <SAMPLE_ATTRIBUTE>
        <TAG>samp_salinity</TAG><VALUE>7.15</VALUE>
      </SAMPLE_ATTRIBUTE>
      <SAMPLE_ATTRIBUTE>
        <TAG>sample_type</TAG><VALUE>ENVO:soil</VALUE>
      </SAMPLE_ATTRIBUTE>
      <SAMPLE_ATTRIBUTE>
        <TAG>season_environment</TAG><VALUE>winter</VALUE>
      </SAMPLE_ATTRIBUTE>
      <SAMPLE_ATTRIBUTE>
        <TAG>temp</TAG><VALUE>15.0</VALUE>
      </SAMPLE_ATTRIBUTE>
      <SAMPLE_ATTRIBUTE>
        <TAG>texture</TAG><VALUE>64.6 sand, 17.6 silt, 17.8 clay</VALUE>
      </SAMPLE_ATTRIBUTE>
      <SAMPLE_ATTRIBUTE>
        <TAG>tot_nitro</TAG><VALUE>1.41</VALUE>
      </SAMPLE_ATTRIBUTE>
      <SAMPLE_ATTRIBUTE>
        <TAG>tot_org_carb</TAG><VALUE>5.0</VALUE>
      </SAMPLE_ATTRIBUTE>
      <SAMPLE_ATTRIBUTE>
        <TAG>water_content_soil</TAG><VALUE>0.164</VALUE>
      </SAMPLE_ATTRIBUTE>
    </SAMPLE_ATTRIBUTES>
  </SAMPLE>
 </SAMPLE_SET>
 """ % {'organization_prefix': qiita_config.ebi_organization_prefix,
        'center_name': qiita_config.ebi_center_name}

STUDYXML = """
<STUDY_SET xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noName\
spaceSchemaLocation="ftp://ftp.sra.ebi.ac.uk/meta/xsd/sra_1_3/SRA.study.xsd">
  <STUDY alias="%(organization_prefix)s_sid_1" center_name="%(center_name)s">
    <DESCRIPTOR>
      <STUDY_TITLE>
        Identification of the Microbiomes for Cannabis Soils
      </STUDY_TITLE>
      <STUDY_TYPE existing_study_type="Metagenomics" />
      <STUDY_ABSTRACT>
        This is a preliminary study to examine the microbiota associated with \
the Cannabis plant. Soils samples from the bulk soil, soil associated with \
the roots, and the rhizosphere were extracted and the DNA sequenced. Roots \
from three independent plants of different strains were examined. These roots \
were obtained November 11, 2011 from plants that had been harvested in the \
summer. Future studies will attempt to analyze the soils and rhizospheres \
from the same location at different time points in the plant lifecycle.
      </STUDY_ABSTRACT>
    </DESCRIPTOR>
    <STUDY_LINKS>
      <STUDY_LINK>
        <XREF_LINK>
          <DB>PUBMED</DB><ID>123456</ID>
        </XREF_LINK>
      </STUDY_LINK>
      <STUDY_LINK>
        <XREF_LINK>
          <DB>PUBMED</DB><ID>7891011</ID>
        </XREF_LINK>
      </STUDY_LINK>
    </STUDY_LINKS>
  </STUDY>
</STUDY_SET>
""" % {'organization_prefix': qiita_config.ebi_organization_prefix,
       'center_name': qiita_config.ebi_center_name}

EXPERIMENTXML = """
<EXPERIMENT_SET xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:no\
NamespaceSchemaLocation="ftp://ftp.sra.ebi.ac.uk/meta/xsd/sra_1_3/SRA.\
experiment.xsd">
  <EXPERIMENT alias="%(organization_prefix)s_ptid_1:1.SKB2.640194" \
center_name="%(center_name)s">
    <TITLE>%(organization_prefix)s_ptid_1:1.SKB2.640194</TITLE>
    <STUDY_REF refname="%(organization_prefix)s_sid_1" />
    <DESIGN>
      <DESIGN_DESCRIPTION>
        micro biome of soil and rhizosphere of cannabis plants from CA
      </DESIGN_DESCRIPTION>
      <SAMPLE_DESCRIPTOR refname="%(organization_prefix)s_sid_1:1.SKB2.\
640194" />
      <LIBRARY_DESCRIPTOR>
        <LIBRARY_NAME>1.SKB2.640194</LIBRARY_NAME>
        <LIBRARY_SOURCE>METAGENOMIC</LIBRARY_SOURCE>
        <LIBRARY_SELECTION>PCR</LIBRARY_SELECTION>
        <LIBRARY_LAYOUT><SINGLE /></LIBRARY_LAYOUT>
        <LIBRARY_CONSTRUCTION_PROTOCOL>This analysis was done as in Caporaso \
et al 2011 Genome research. The PCR primers (F515/R806) were developed \
against the V4 region of the 16S rRNA (both bacteria and archaea), which we \
determined would yield optimal community clustering with reads of this length \
using a procedure similar to that of ref. 15. [For reference, this primer \
pair amplifies the region 533_786 in the Escherichia coli strain 83972 \
sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR \
primer is barcoded with a 12-base error-correcting Golay code to facilitate \
multiplexing of up to 1,500 samples per lane, and both PCR primers contain \
sequencer adapter regions.
        </LIBRARY_CONSTRUCTION_PROTOCOL>
      </LIBRARY_DESCRIPTOR>
    </DESIGN>
    <PLATFORM>
      <ILLUMINA><INSTRUMENT_MODEL>Illumina MiSeq</INSTRUMENT_MODEL></ILLUMINA>
    </PLATFORM>
    <EXPERIMENT_ATTRIBUTES>
      <EXPERIMENT_ATTRIBUTE>
        <TAG>barcode</TAG><VALUE>CGTAGAGCTCTC</VALUE>
      </EXPERIMENT_ATTRIBUTE>
      <EXPERIMENT_ATTRIBUTE>
        <TAG>center_name</TAG><VALUE>ANL</VALUE>
      </EXPERIMENT_ATTRIBUTE>
      <EXPERIMENT_ATTRIBUTE>
        <TAG>center_project_name</TAG><VALUE>None</VALUE>
      </EXPERIMENT_ATTRIBUTE>
      <EXPERIMENT_ATTRIBUTE>
        <TAG>emp_status</TAG><VALUE>EMP</VALUE>
      </EXPERIMENT_ATTRIBUTE>
      <EXPERIMENT_ATTRIBUTE>
        <TAG>experiment_center</TAG><VALUE>ANL</VALUE>
      </EXPERIMENT_ATTRIBUTE>
      <EXPERIMENT_ATTRIBUTE>
        <TAG>experiment_title</TAG><VALUE>Cannabis Soil Microbiome</VALUE>
      </EXPERIMENT_ATTRIBUTE>
      <EXPERIMENT_ATTRIBUTE>
        <TAG>illumina_technology</TAG><VALUE>MiSeq</VALUE>
      </EXPERIMENT_ATTRIBUTE>
      <EXPERIMENT_ATTRIBUTE>
        <TAG>pcr_primers</TAG><VALUE>FWD:GTGCCAGCMGCCGCGGTAA; \
REV:GGACTACHVGGGTWTCTAAT</VALUE>
      </EXPERIMENT_ATTRIBUTE>
      <EXPERIMENT_ATTRIBUTE>
        <TAG>primer</TAG><VALUE>GTGCCAGCMGCCGCGGTAA</VALUE>
      </EXPERIMENT_ATTRIBUTE>
      <EXPERIMENT_ATTRIBUTE>
        <TAG>run_center</TAG><VALUE>ANL</VALUE>
      </EXPERIMENT_ATTRIBUTE>
      <EXPERIMENT_ATTRIBUTE>
        <TAG>run_date</TAG><VALUE>8/1/12</VALUE>
      </EXPERIMENT_ATTRIBUTE>
      <EXPERIMENT_ATTRIBUTE>
        <TAG>run_prefix</TAG><VALUE>s_G1_L001_sequences</VALUE>
      </EXPERIMENT_ATTRIBUTE>
      <EXPERIMENT_ATTRIBUTE>
        <TAG>samp_size</TAG><VALUE>.25,g</VALUE>
      </EXPERIMENT_ATTRIBUTE>
      <EXPERIMENT_ATTRIBUTE>
        <TAG>sample_center</TAG><VALUE>ANL</VALUE>
      </EXPERIMENT_ATTRIBUTE>
      <EXPERIMENT_ATTRIBUTE>
        <TAG>sequencing_meth</TAG><VALUE>Sequencing by synthesis</VALUE>
      </EXPERIMENT_ATTRIBUTE>
      <EXPERIMENT_ATTRIBUTE>
        <TAG>study_center</TAG><VALUE>CCME</VALUE>
      </EXPERIMENT_ATTRIBUTE>
      <EXPERIMENT_ATTRIBUTE>
        <TAG>target_gene</TAG><VALUE>16S rRNA</VALUE>
      </EXPERIMENT_ATTRIBUTE>
      <EXPERIMENT_ATTRIBUTE>
        <TAG>target_subfragment</TAG><VALUE>V4</VALUE>
      </EXPERIMENT_ATTRIBUTE>
    </EXPERIMENT_ATTRIBUTES>
  </EXPERIMENT>
  <EXPERIMENT alias="%(organization_prefix)s_ptid_1:1.SKB3.640195" \
center_name="%(center_name)s">
    <TITLE>%(organization_prefix)s_ptid_1:1.SKB3.640195</TITLE>
    <STUDY_REF refname="%(organization_prefix)s_sid_1" />
    <DESIGN>
      <DESIGN_DESCRIPTION>
        micro biome of soil and rhizosphere of cannabis plants from CA
      </DESIGN_DESCRIPTION>
      <SAMPLE_DESCRIPTOR refname="%(organization_prefix)s_sid_1:1.SKB3.\
640195" />
      <LIBRARY_DESCRIPTOR>
        <LIBRARY_NAME>1.SKB3.640195</LIBRARY_NAME>
        <LIBRARY_SOURCE>METAGENOMIC</LIBRARY_SOURCE>
        <LIBRARY_SELECTION>PCR</LIBRARY_SELECTION>
        <LIBRARY_LAYOUT><SINGLE /></LIBRARY_LAYOUT>
        <LIBRARY_CONSTRUCTION_PROTOCOL>This analysis was done as in Caporaso \
et al 2011 Genome research. The PCR primers (F515/R806) were developed \
against the V4 region of the 16S rRNA (both bacteria and archaea), which we \
determined would yield optimal community clustering with reads of this length \
using a procedure similar to that of ref. 15. [For reference, this primer \
pair amplifies the region 533_786 in the Escherichia coli strain 83972 \
sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR \
primer is barcoded with a 12-base error-correcting Golay code to facilitate \
multiplexing of up to 1,500 samples per lane, and both PCR primers contain \
sequencer adapter regions.
        </LIBRARY_CONSTRUCTION_PROTOCOL>
      </LIBRARY_DESCRIPTOR>
    </DESIGN>
    <PLATFORM>
      <ILLUMINA><INSTRUMENT_MODEL>Illumina MiSeq</INSTRUMENT_MODEL></ILLUMINA>
    </PLATFORM>
    <EXPERIMENT_ATTRIBUTES>
      <EXPERIMENT_ATTRIBUTE>
        <TAG>barcode</TAG><VALUE>CCTCTGAGAGCT</VALUE>
      </EXPERIMENT_ATTRIBUTE>
      <EXPERIMENT_ATTRIBUTE>
        <TAG>center_name</TAG><VALUE>ANL</VALUE>
      </EXPERIMENT_ATTRIBUTE>
      <EXPERIMENT_ATTRIBUTE>
        <TAG>center_project_name</TAG><VALUE>None</VALUE>
      </EXPERIMENT_ATTRIBUTE>
      <EXPERIMENT_ATTRIBUTE>
        <TAG>emp_status</TAG><VALUE>EMP</VALUE>
      </EXPERIMENT_ATTRIBUTE>
      <EXPERIMENT_ATTRIBUTE>
        <TAG>experiment_center</TAG><VALUE>ANL</VALUE>
      </EXPERIMENT_ATTRIBUTE>
      <EXPERIMENT_ATTRIBUTE>
        <TAG>experiment_title</TAG><VALUE>Cannabis Soil Microbiome</VALUE>
      </EXPERIMENT_ATTRIBUTE>
      <EXPERIMENT_ATTRIBUTE>
        <TAG>illumina_technology</TAG><VALUE>MiSeq</VALUE>
      </EXPERIMENT_ATTRIBUTE>
      <EXPERIMENT_ATTRIBUTE>
        <TAG>pcr_primers</TAG><VALUE>FWD:GTGCCAGCMGCCGCGGTAA; \
REV:GGACTACHVGGGTWTCTAAT</VALUE>
      </EXPERIMENT_ATTRIBUTE>
      <EXPERIMENT_ATTRIBUTE>
        <TAG>primer</TAG><VALUE>GTGCCAGCMGCCGCGGTAA</VALUE>
      </EXPERIMENT_ATTRIBUTE>
      <EXPERIMENT_ATTRIBUTE>
        <TAG>run_center</TAG><VALUE>ANL</VALUE>
      </EXPERIMENT_ATTRIBUTE>
      <EXPERIMENT_ATTRIBUTE>
        <TAG>run_date</TAG><VALUE>8/1/12</VALUE>
      </EXPERIMENT_ATTRIBUTE>
      <EXPERIMENT_ATTRIBUTE>
        <TAG>run_prefix</TAG><VALUE>s_G1_L001_sequences</VALUE>
      </EXPERIMENT_ATTRIBUTE>
      <EXPERIMENT_ATTRIBUTE>
        <TAG>samp_size</TAG><VALUE>.25,g</VALUE>
      </EXPERIMENT_ATTRIBUTE>
      <EXPERIMENT_ATTRIBUTE>
        <TAG>sample_center</TAG><VALUE>ANL</VALUE>
      </EXPERIMENT_ATTRIBUTE>
      <EXPERIMENT_ATTRIBUTE>
        <TAG>sequencing_meth</TAG><VALUE>Sequencing by synthesis</VALUE>
      </EXPERIMENT_ATTRIBUTE>
      <EXPERIMENT_ATTRIBUTE>
        <TAG>study_center</TAG><VALUE>CCME</VALUE>
      </EXPERIMENT_ATTRIBUTE>
      <EXPERIMENT_ATTRIBUTE>
        <TAG>target_gene</TAG><VALUE>16S rRNA</VALUE>
      </EXPERIMENT_ATTRIBUTE>
      <EXPERIMENT_ATTRIBUTE>
        <TAG>target_subfragment</TAG><VALUE>V4</VALUE>
      </EXPERIMENT_ATTRIBUTE>
    </EXPERIMENT_ATTRIBUTES>
  </EXPERIMENT>
</EXPERIMENT_SET>
""" % {'organization_prefix': qiita_config.ebi_organization_prefix,
       'center_name': qiita_config.ebi_center_name}

RUNXML = """
<RUN_SET xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespace\
SchemaLocation="ftp://ftp.sra.ebi.ac.uk/meta/xsd/sra_1_3/SRA.run.xsd">
  <RUN alias="%(organization_prefix)s_ppdid_3:1.SKB2.640194" \
center_name="%(center_name)s">
    <EXPERIMENT_REF refname="%(organization_prefix)s_ptid_1:1.SKB2.640194" />
    <DATA_BLOCK>
      <FILES>
        <FILE checksum="938c29679790b9c17e4dab060fa4c8c5" \
checksum_method="MD5" filename="%(ebi_dir)s/1.SKB2.640194.fastq.gz" \
filetype="fastq" quality_scoring_system="phred" />
      </FILES>
    </DATA_BLOCK>
  </RUN>
  <RUN alias="%(organization_prefix)s_ppdid_3:1.SKM4.640180" \
center_name="%(center_name)s">
    <EXPERIMENT_REF refname="%(organization_prefix)s_ptid_1:1.SKM4.640180" />
    <DATA_BLOCK>
      <FILES>
        <FILE checksum="2f8f469a8075b42e401ff0a2c85dc0e5" \
checksum_method="MD5" filename="%(ebi_dir)s/1.SKM4.640180.fastq.gz" \
filetype="fastq" quality_scoring_system="phred" />
      </FILES>
    </DATA_BLOCK>
  </RUN>
  <RUN alias="%(organization_prefix)s_ppdid_3:1.SKB3.640195" \
center_name="%(center_name)s">
    <EXPERIMENT_REF refname="%(organization_prefix)s_ptid_1:1.SKB3.640195" />
    <DATA_BLOCK>
      <FILES>
        <FILE checksum="550794cf00ec86b9d3e2feb08cb7a97b" \
checksum_method="MD5" filename="%(ebi_dir)s/1.SKB3.640195.fastq.gz" \
filetype="fastq" quality_scoring_system="phred" />
      </FILES>
    </DATA_BLOCK>
  </RUN>
  <RUN alias="%(organization_prefix)s_ppdid_3:1.SKB6.640176" \
center_name="%(center_name)s">
    <EXPERIMENT_REF refname="%(organization_prefix)s_ptid_1:1.SKB6.640176" />
    <DATA_BLOCK>
      <FILES>
        <FILE checksum="adcc754811b86a240f0cc3d59c188cd0" \
checksum_method="MD5" filename="%(ebi_dir)s/1.SKB6.640176.fastq.gz" \
filetype="fastq" quality_scoring_system="phred" />
      </FILES>
    </DATA_BLOCK>
  </RUN>
</RUN_SET>
"""

SUBMISSIONXML = """
<SUBMISSION_SET xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:no\
NamespaceSchemaLocation="ftp://ftp.sra.ebi.ac.uk/meta/xsd/sra_1_3/\
SRA.submission.xsd">
  <SUBMISSION alias="%(submission_alias)s" center_name="%(center_name)s">
    <ACTIONS>
      <ACTION><ADD schema="study" source="study.xml" /></ACTION>
      <ACTION><ADD schema="sample" source="sample.xml" /></ACTION>
      <ACTION><ADD schema="experiment" source="experiment.xml" /></ACTION>
      <ACTION><ADD schema="run" source="run.xml" /></ACTION>
      <ACTION><HOLD HoldUntilDate="2016-09-02" /></ACTION>
    </ACTIONS>
  </SUBMISSION>
</SUBMISSION_SET>
"""

ADDDICTTEST = """<TESTING foo="bar">
    <foo>
        <TAG>&gt;x</TAG>
        <VALUE>&lt;y</VALUE>
    </foo>
    <foo>
        <TAG>x</TAG>
        <VALUE>y</VALUE>
    </foo>
</TESTING>
"""

GENSPOTDESC = """<design foo="bar">
    <SPOT_DESCRIPTOR>
        <SPOT_DECODE_SPEC />
        <READ_SPEC>
            <READ_INDEX>0</READ_INDEX>
            <READ_CLASS>Application Read</READ_CLASS>
            <READ_TYPE>Forward</READ_TYPE>
            <BASE_COORD>1</BASE_COORD>
        </READ_SPEC>
    </SPOT_DESCRIPTOR>
</design>
"""

CURL_RESULT = """<?xml version="1.0" encoding="UTF-8"?>
<?xml-stylesheet type="text/xsl" href="receipt.xsl"?>
<RECEIPT receiptDate="2015-09-20T23:27:01.924+01:00" \
submissionFile="submission.xml" success="true">
  <EXPERIMENT accession="ERX0000000" alias="{0}_ptid_1:1.SKB2.640194" \
status="PRIVATE"/>
  <EXPERIMENT accession="ERX0000001" alias="{0}_ptid_1:1.SKB6.640176" \
status="PRIVATE"/>
  <EXPERIMENT accession="ERX0000002" alias="{0}_ptid_1:1.SKM4.640180" \
status="PRIVATE"/>
  <RUN accession="ERR0000000" alias="{0}_ppdid_{1}:1.SKB2.640194" \
status="PRIVATE"/>
  <RUN accession="ERR0000001" alias="{0}_ppdid_{1}:1.SKB6.640176" \
status="PRIVATE"/>
  <RUN accession="ERR0000002" alias="{0}_ppdid_{1}:1.SKM4.640180" \
status="PRIVATE"/>
  <SAMPLE accession="ERS000000" alias="{0}_sid_1:1.SKB2.640194"
status="PRIVATE">
    <EXT_ID accession="SAMEA0000000" type="biosample"/>
  </SAMPLE>
  <SAMPLE accession="ERS000001" alias="{0}_sid_1:1.SKB6.640176"
status="PRIVATE">
    <EXT_ID accession="SAMEA0000001" type="biosample"/>
  </SAMPLE>
  <SAMPLE accession="ERS000002" alias="{0}_sid_1:1.SKM4.640180"
status="PRIVATE">
    <EXT_ID accession="SAMEA0000002" type="biosample"/>
  </SAMPLE>
  <STUDY accession="ERP000000" alias="{0}_sid_1" status="PRIVATE" \
holdUntilDate="2016-09-19+01:00"/>
  <SUBMISSION accession="ERA000000" alias="qiime_submission_570"/>
  <MESSAGES>
    <INFO> ADD action for the following XML: study.xml sample.xml \
experiment.xml run.xml       </INFO>
  </MESSAGES>
  <ACTIONS>ADD</ACTIONS>
  <ACTIONS>ADD</ACTIONS>
  <ACTIONS>ADD</ACTIONS>
  <ACTIONS>ADD</ACTIONS>
  <ACTIONS>HOLD</ACTIONS>
</RECEIPT>
"""

if __name__ == "__main__":
    main()
