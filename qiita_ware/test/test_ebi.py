# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from os import remove
from os.path import join, isdir, exists
from shutil import rmtree
from tempfile import mkdtemp
from unittest import TestCase, main
from xml.etree import ElementTree as ET
from functools import partial
import pandas as pd
import warnings
from datetime import date
from skbio.util import safe_md5

from h5py import File
from qiita_files.demux import to_hdf5

from qiita_core.qiita_settings import qiita_config
from qiita_core.util import qiita_test_checker
from qiita_db.util import get_mountpoint, convert_to_id
from qiita_db.study import Study, StudyPerson
from qiita_db.metadata_template.prep_template import PrepTemplate
from qiita_db.metadata_template.sample_template import SampleTemplate
from qiita_db.user import User
from qiita_db.artifact import Artifact
from qiita_db.software import Parameters, DefaultParameters
from qiita_db.ontology import Ontology
from qiita_ware.ebi import EBISubmission
from qiita_ware.exceptions import EBISubmissionError


@qiita_test_checker()
class TestEBISubmission(TestCase):
    def setUp(self):
        self.files_to_remove = []
        self.temp_dir = mkdtemp()
        self.files_to_remove.append(self.temp_dir)
        self.study_id = None

    def tearDown(self):
        if self.study_id and Study.exists("Test EBI study"):
            study = Study(self.study_id)
            for a in study.artifacts():
                Artifact.delete(a.id)
            for pt in study.prep_templates():
                PrepTemplate.delete(pt.id)
            SampleTemplate.delete(self.study_id)
            Study.delete(self.study_id)

        for f in self.files_to_remove:
            if exists(f):
                if isdir(f):
                    rmtree(f)
                else:
                    remove(f)

    def test_init(self):
        artifact_id = 3
        action = 'ADD'

        e = EBISubmission(artifact_id, action)
        self.files_to_remove.append(e.full_ebi_dir)

        self.assertEqual(e.artifact_id, artifact_id)
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
        self.assertCountEqual(e.sample_template, e.samples)
        self.assertCountEqual(e.publications, [
            ['10.100/123456', True], ['123456', False],
            ['10.100/7891011', True], ['7891011', False]])
        self.assertEqual(e.action, action)

        self.assertEqual(e.ascp_reply, join(e.full_ebi_dir, 'ascp_reply.txt'))
        self.assertEqual(e.curl_reply, join(e.full_ebi_dir, 'curl_reply.xml'))
        get_output_fp = partial(join, e.full_ebi_dir)
        self.assertEqual(e.xml_dir, get_output_fp('xml_dir'))
        self.assertIsNone(e.study_xml_fp)
        self.assertIsNone(e.sample_xml_fp)
        self.assertIsNone(e.experiment_xml_fp)
        self.assertIsNone(e.run_xml_fp)
        self.assertIsNone(e.submission_xml_fp)

        for sample in e.sample_template:
            self.assertEqual(e.sample_template[sample], e.samples[sample])
            self.assertEqual(e.prep_template[sample], e.samples_prep[sample])
            self.assertEqual(e.sample_demux_fps[sample], get_output_fp(sample))

    def test_get_study_alias(self):
        e = EBISubmission(3, 'ADD')
        self.files_to_remove.append(e.full_ebi_dir)
        exp = '%s_sid_1' % qiita_config.ebi_organization_prefix
        self.assertEqual(e._get_study_alias(), exp)

    def test_get_sample_alias(self):
        e = EBISubmission(3, 'ADD')
        self.files_to_remove.append(e.full_ebi_dir)
        exp = '%s_sid_1:foo' % qiita_config.ebi_organization_prefix
        self.assertEqual(e._get_sample_alias('foo'), exp)
        self.assertEqual(e._sample_aliases, {exp: 'foo'})

    def test_get_experiment_alias(self):
        e = EBISubmission(3, 'ADD')
        self.files_to_remove.append(e.full_ebi_dir)
        exp = '%s_ptid_1:foo' % qiita_config.ebi_organization_prefix
        self.assertEqual(e._get_experiment_alias('foo'), exp)
        self.assertEqual(e._experiment_aliases, {exp: 'foo'})

    def test_get_submission_alias(self):
        artifact_id = 3
        e = EBISubmission(artifact_id, 'ADD')
        self.files_to_remove.append(e.full_ebi_dir)
        obs = e._get_submission_alias()
        exp = '%s_submission_%d' % (qiita_config.ebi_organization_prefix,
                                    artifact_id)
        self.assertEqual(obs, exp)

    def test_get_run_alias(self):
        artifact_id = 3
        e = EBISubmission(artifact_id, 'ADD')
        self.files_to_remove.append(e.full_ebi_dir)
        exp = '%s_ppdid_%d:foo' % (qiita_config.ebi_organization_prefix,
                                   artifact_id)
        self.assertEqual(e._get_run_alias('foo'), exp)
        self.assertEqual(e._run_aliases, {exp: 'foo'})

    def test_get_library_name(self):
        e = EBISubmission(3, 'ADD')
        self.files_to_remove.append(e.full_ebi_dir)
        obs = e._get_library_name("nasty<business>")
        exp = "nasty&lt;business&gt;"
        self.assertEqual(obs, exp)

    def test_add_dict_as_tags_and_values(self):
        e = EBISubmission(3, 'ADD')
        self.files_to_remove.append(e.full_ebi_dir)
        elm = ET.Element('TESTING', {'foo': 'bar'})

        e._add_dict_as_tags_and_values(elm, 'foo', {'x': 'y',
                                                    '>x': '<y',
                                                    'none': None})
        obs = ET.tostring(elm)
        exp = ''.join([v.strip() for v in ADDDICTTEST.splitlines()])
        self.assertEqual(obs.decode('ascii'), exp)

    def test_generate_study_xml(self):
        submission = EBISubmission(3, 'ADD')
        self.files_to_remove.append(submission.full_ebi_dir)
        obs = ET.tostring(submission.generate_study_xml())
        exp = ''.join([line.strip() for line in STUDYXML.splitlines()])
        self.assertEqual(obs.decode('ascii'), exp)

    def test_generate_sample_xml(self):
        submission = EBISubmission(3, 'ADD')
        self.files_to_remove.append(submission.full_ebi_dir)

        samples = ['1.SKB2.640194', '1.SKB3.640195']
        obs = ET.tostring(submission.generate_sample_xml(samples=samples))
        exp = ('<SAMPLE_SET xmlns:xsi="http://www.w3.org/2001/XMLSchema-'
               'instance" xsi:noNamespaceSchemaLocation="ftp://ftp.sra.ebi.ac.'
               'uk/meta/xsd/sra_1_3/SRA.sample.xsd" />')
        self.assertEqual(obs.decode('ascii'), exp)

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
        self.assertEqual(obs.decode('ascii'), exp)

        obs = ET.tostring(submission.generate_sample_xml(samples=[]))
        self.assertEqual(obs.decode('ascii'), exp)

    def test_generate_spot_descriptor(self):
        e = EBISubmission(3, 'ADD')
        self.files_to_remove.append(e.full_ebi_dir)
        elm = ET.Element('design', {'foo': 'bar'})

        e._generate_spot_descriptor(elm, 'LS454')
        exp = ''.join([line.strip() for line in GENSPOTDESC.splitlines()])
        obs = ET.tostring(elm)
        self.assertEqual(obs.decode('ascii'), exp)

    def test_generate_submission_xml(self):
        submission = EBISubmission(3, 'ADD')
        self.files_to_remove.append(submission.full_ebi_dir)
        submission.experiment_xml_fp = "/some/path/experiment.xml"
        submission.run_xml_fp = "/some/path/run.xml"
        obs = ET.tostring(
            submission.generate_submission_xml(
                submission_date=date(2015, 9, 3)))
        exp = SUBMISSIONXML % {
            'submission_alias': submission._get_submission_alias(),
            'center_name': qiita_config.ebi_center_name}
        exp = ''.join([line.strip() for line in exp.splitlines()])
        self.assertEqual(obs.decode('ascii'), exp)

        submission.study_xml_fp = "/some/path/study.xml"
        submission.sample_xml_fp = "/some/path/sample.xml"
        submission.experiment_xml_fp = "/some/path/experiment.xml"
        submission.run_xml_fp = "/some/path/run.xml"
        obs = ET.tostring(
            submission.generate_submission_xml(
                submission_date=date(2015, 9, 3)))
        exp = SUBMISSIONXML_FULL % {
            'submission_alias': submission._get_submission_alias(),
            'center_name': qiita_config.ebi_center_name}
        exp = ''.join([line.strip() for line in exp.splitlines()])
        self.assertEqual(obs.decode('ascii'), exp)

    def test_write_xml_file(self):
        element = ET.Element('TESTING', {'foo': 'bar'})
        e = EBISubmission(3, 'ADD')
        self.files_to_remove.append(e.full_ebi_dir)
        e.write_xml_file(element, 'testfile')
        self.files_to_remove.append('testfile')

        obs = open('testfile').read()
        exp = "<?xml version='1.0' encoding='UTF-8'?>\n<TESTING foo=\"bar\" />"
        self.assertEqual(obs, exp)

    def test_generate_curl_command(self):
        submission = EBISubmission(3, 'ADD')
        self.files_to_remove.append(submission.full_ebi_dir)

        test_ebi_seq_xfer_user = 'ebi_seq_xfer_user'
        test_ebi_seq_xfer_pass = 'ebi_seq_xfer_pass'
        test_ebi_dropbox_url = 'ebi_dropbox_url'

        submission.study_xml_fp = "/some/path/study.xml"
        submission.sample_xml_fp = "/some/path/sample.xml"
        submission.experiment_xml_fp = "/some/path/experiment.xml"
        submission.run_xml_fp = "/some/path/run.xml"
        submission.submission_xml_fp = "/some/path/submission.xml"
        obs = submission.generate_curl_command(test_ebi_seq_xfer_user,
                                               test_ebi_seq_xfer_pass,
                                               test_ebi_dropbox_url)
        exp = ('curl -sS -k '
               '-F "SUBMISSION=@/some/path/submission.xml" '
               '-F "STUDY=@/some/path/study.xml" '
               '-F "SAMPLE=@/some/path/sample.xml" '
               '-F "RUN=@/some/path/run.xml" '
               '-F "EXPERIMENT=@/some/path/experiment.xml" '
               '"ebi_dropbox_url/?auth=ENA%20ebi_seq_xfer_user'
               '%20ebi_seq_xfer_pass"')
        self.assertEqual(obs, exp)

    def write_demux_files(self, prep_template, sequences='FASTA-EXAMPLE'):
        """Writes a demux test file to avoid duplication of code"""
        fna_fp = join(self.temp_dir, 'seqs.fna')
        demux_fp = join(self.temp_dir, 'demux.seqs')
        if sequences == 'FASTA-EXAMPLE':
            with open(fna_fp, 'w') as f:
                f.write(FASTA_EXAMPLE)
            with File(demux_fp, "w") as f:
                to_hdf5(fna_fp, f)
        elif sequences == 'WRONG-SEQS':
            with open(fna_fp, 'w') as f:
                f.write('>a_1 X orig_bc=X new_bc=X bc_diffs=0\nCCC')
            with File(demux_fp, "w") as f:
                to_hdf5(fna_fp, f)
        elif sequences == 'EMPTY':
            with open(demux_fp, 'w') as f:
                f.write("")
        else:
            raise ValueError('Wrong sequences values: %s. Valid values: '
                             'FASTA_EXAMPLE, WRONG-SEQS, EMPTY' % sequences)

        if prep_template.artifact is None:
            artifact = Artifact.create(
                [(demux_fp, 6)], "Demultiplexed", prep_template=prep_template)
        else:
            params = Parameters.from_default_params(
                DefaultParameters(1),
                {'input_data': prep_template.artifact.id})
            artifact = Artifact.create(
                [(demux_fp, 6)], "Demultiplexed",
                parents=[prep_template.artifact],
                processing_parameters=params)

        return artifact

    def generate_new_prep_template_and_write_demux_files(self,
                                                         valid_metadata=False):
        """Creates new prep-template/demux-file to avoid duplication of code"""

        # creating prep template without required EBI submission columns
        if not valid_metadata:
            metadata_dict = {
                'SKD6.640190': {'center_name': 'ANL', 'barcode': 'AAA',
                                'center_project_name': 'Test Project'},
                'SKM6.640187': {'center_name': 'ANL', 'barcode': 'AAA',
                                'center_project_name': 'Test Project',
                                'platform': 'Illumina',
                                'instrument_model': 'Not valid'},
                'SKD9.640182': {'center_name': 'ANL', 'barcode': 'AAA',
                                'center_project_name': 'Test Project',
                                'platform': 'Illumina',
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
                'SKD6.640190': {'center_name': 'ANL', 'barcode': 'AAA',
                                'center_project_name': 'Test Project',
                                'platform': 'Illumina',
                                'instrument_model': 'Illumina MiSeq',
                                'primer': 'GTGCCAGCMGCCGCGGTAA',
                                'experiment_design_description':
                                    'microbiome of soil and rhizosphere',
                                'library_construction_protocol':
                                    'PMID: 22402401'},
                'SKM6.640187': {'center_name': 'ANL', 'barcode': 'AAA',
                                'center_project_name': 'Test Project',
                                'platform': 'Illumina',
                                'instrument_model': 'Illumina MiSeq',
                                'primer': 'GTGCCAGCMGCCGCGGTAA',
                                'experiment_design_description':
                                    'microbiome of soil and rhizosphere',
                                'library_construction_protocol':
                                    'PMID: 22402401',
                                'extra_value': 1.2},
                'SKD9.640182': {'center_name': 'ANL', 'barcode': 'AAA',
                                'center_project_name': 'Test Project',
                                'platform': 'Illumina',
                                'instrument_model': 'Illumina MiSeq',
                                'primer': 'GTGCCAGCMGCCGCGGTAA',
                                'experiment_design_description':
                                    'microbiome of soil and rhizosphere',
                                'library_construction_protocol':
                                    'PMID: 22402401',
                                'extra_value': 'Unspecified'}
            }
            investigation_type = "Metagenomics"
        metadata = pd.DataFrame.from_dict(metadata_dict, orient='index',
                                          dtype=str)

        with warnings.catch_warnings(record=True):
            pt = PrepTemplate.create(metadata, Study(1), "18S",
                                     investigation_type=investigation_type)
        artifact = self.write_demux_files(pt)

        return artifact

    def generate_new_study_with_preprocessed_data(self):
        """Creates a new study up to the processed data for testing"""
        info = {
            "timeseries_type_id": 1,
            "metadata_complete": True,
            "mixs_compliant": True,
            "study_alias": "Test EBI",
            "study_description": "Study for testing EBI",
            "study_abstract": "Study for testing EBI",
            "principal_investigator_id": StudyPerson(3),
            "lab_person_id": StudyPerson(1)
        }
        study = Study.create(User('test@foo.bar'), "Test EBI study", info)
        self.study_id = study.id
        metadata_dict = {
            'Sample1': {'collection_timestamp': '06/01/15 07:00:00',
                        'physical_specimen_location': 'location1',
                        'taxon_id': 9606,
                        'scientific_name': 'homo sapiens',
                        'Description': 'Test Sample 1'},
            'Sample2': {'collection_timestamp': '06/02/15 07:00:00',
                        'physical_specimen_location': 'location1',
                        'taxon_id': 9606,
                        'scientific_name': 'homo sapiens',
                        'Description': 'Test Sample 2'},
            'Sample3': {'collection_timestamp': '06/03/15 07:00:00',
                        'physical_specimen_location': 'location1',
                        'taxon_id': 9606,
                        'scientific_name': 'homo sapiens',
                        'Description': 'Test Sample 3'}
        }
        metadata = pd.DataFrame.from_dict(metadata_dict, orient='index',
                                          dtype=str)
        with warnings.catch_warnings(record=True):
            SampleTemplate.create(metadata, study)
        metadata_dict = {
            'Sample1': {'primer': 'GTGCCAGCMGCCGCGGTAA',
                        'barcode': 'CGTAGAGCTCTC',
                        'center_name': 'KnightLab',
                        'platform': 'Illumina',
                        'instrument_model': 'Illumina MiSeq',
                        'library_construction_protocol': 'Protocol ABC',
                        'experiment_design_description': "Random value 1"},
            'Sample2': {'primer': 'GTGCCAGCMGCCGCGGTAA',
                        'barcode': 'CGTAGAGCTCTA',
                        'center_name': 'KnightLab',
                        'platform': 'Illumina',
                        'instrument_model': 'Illumina MiSeq',
                        'library_construction_protocol': 'Protocol ABC',
                        'experiment_design_description': "Random value 2"},
            'Sample3': {'primer': 'GTGCCAGCMGCCGCGGTAA',
                        'barcode': 'CGTAGAGCTCTT',
                        'center_name': 'KnightLab',
                        'platform': 'Illumina',
                        'instrument_model': 'Illumina MiSeq',
                        'library_construction_protocol': 'Protocol ABC',
                        'experiment_design_description': "Random value 3"},
        }
        metadata = pd.DataFrame.from_dict(metadata_dict, orient='index',
                                          dtype=str)
        with warnings.catch_warnings(record=True):
            pt = PrepTemplate.create(metadata, study, "16S", 'Metagenomics')
        fna_fp = join(self.temp_dir, 'seqs.fna')
        demux_fp = join(self.temp_dir, 'demux.seqs')
        with open(fna_fp, 'w') as f:
            f.write(FASTA_EXAMPLE_2.format(study.id))
        with File(demux_fp, 'w') as f:
            to_hdf5(fna_fp, f)

        # Magic number 6: the id of the preprocessed_demux filepath_type
        artifact = Artifact.create(
            [(demux_fp, 6)], "Demultiplexed", prep_template=pt)

        return artifact

    def test_init_exceptions(self):
        # not a valid action
        with self.assertRaises(EBISubmissionError):
            EBISubmission(1, 'This is not a valid action')

        # artifact can't be submitted
        with self.assertRaises(EBISubmissionError):
            EBISubmission(1, 'ADD')

        # artifact has been already submitted
        with self.assertRaises(EBISubmissionError):
            EBISubmission(2, 'ADD')

        artifact = self.generate_new_prep_template_and_write_demux_files()
        # raise error as we are missing columns
        # artifact.prep_templates[0] cause there should only be 1
        exp_text = ("Errors found during EBI submission for study #1, "
                    "artifact #%d and prep template #%d:\nUnrecognized "
                    "investigation type: 'None'. This term is neither one of "
                    "the official terms nor one of the user-defined terms in "
                    "the ENA ontology.\nThese samples do not have a valid "
                    "platform (instrumet model wasn't checked): "
                    "1.SKD6.640190\nThese samples do not have a valid "
                    "instrument model: 1.SKM6.640187" % (
                        artifact.id, artifact.prep_templates[0].id))
        with self.assertRaises(EBISubmissionError) as e:
            EBISubmission(artifact.id, 'ADD')
        self.assertEqual(exp_text, str(e.exception))

    def test_prep_with_less_samples_than_sample_template(self):
        # the next line generates a valid prep template with less samples than
        # the sample template and basically we want to test that
        # the EBISubmission can be generated
        artifact = self.generate_new_prep_template_and_write_demux_files(True)
        e = EBISubmission(artifact.id, 'ADD')
        self.files_to_remove.append(e.full_ebi_dir)
        exp = ['1.SKD6.640190', '1.SKM6.640187', '1.SKD9.640182']
        self.assertCountEqual(exp, e.samples)

    def test_generate_experiment_xml(self):
        artifact = self.generate_new_study_with_preprocessed_data()
        submission = EBISubmission(artifact.id, 'ADD')
        self.files_to_remove.append(submission.full_ebi_dir)
        obs = ET.tostring(submission.generate_experiment_xml())
        exp = EXPERIMENTXML_NEWSTUDY % {
            'organization_prefix': qiita_config.ebi_organization_prefix,
            'center_name': qiita_config.ebi_center_name,
            'study_id': artifact.study.id,
            'pt_id': artifact.prep_templates[0].id
        }
        exp = ''.join([line.strip() for line in exp.splitlines()])
        self.assertEqual(obs.decode('ascii'), exp)

        artifact_id = 3

        submission = EBISubmission(artifact_id, 'ADD')
        self.files_to_remove.append(submission.full_ebi_dir)
        samples = ['1.SKB2.640194', '1.SKB3.640195']
        obs = ET.tostring(submission.generate_experiment_xml(samples=samples))
        exp = EXPERIMENTXML
        exp = ''.join([line.strip() for line in exp.splitlines()])
        self.assertEqual(obs.decode('ascii'), exp)

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
        self.assertEqual(obs.decode('ascii'), exp)

        # changing investigation_type to test user defined terms, first let's
        # create a new term
        new_term = 'ULTIMATE TERM'
        ena_ontology = Ontology(convert_to_id('ENA', 'ontology'))
        ena_ontology.add_user_defined_term(new_term)
        # set the preparation with the new term
        submission.prep_template.investigation_type = new_term
        # regenerate submission to make sure everything is just fine ...
        submission = EBISubmission(artifact_id, 'ADD')
        self.assertEqual(submission.investigation_type, 'Other')
        self.assertEqual(submission.new_investigation_type, new_term)

        obs = ET.tostring(submission.generate_experiment_xml())
        exp = '<LIBRARY_STRATEGY>%s</LIBRARY_STRATEGY>' % new_term
        self.assertIn(exp, obs.decode('ascii'))

        # returnging investigation_type to it's value
        submission.prep_template.investigation_type = 'Metagenomics'

    def test_generate_run_xml(self):
        artifact = self.generate_new_study_with_preprocessed_data()
        submission = EBISubmission(artifact.id, 'ADD')
        self.files_to_remove.append(submission.full_ebi_dir)
        submission.generate_demultiplexed_fastq(mtime=1)
        obs = ET.tostring(submission.generate_run_xml())

        md5_sums = {}
        for s, fp in submission.sample_demux_fps.items():
            md5_sums[s] = safe_md5(
                open(fp + submission.FWD_READ_SUFFIX, 'rb')).hexdigest()

        exp = RUNXML_NEWSTUDY % {
            'study_alias': submission._get_study_alias(),
            'ebi_dir': submission.ebi_dir,
            'organization_prefix': qiita_config.ebi_organization_prefix,
            'center_name': qiita_config.ebi_center_name,
            'artifact_id': artifact.id,
            'study_id': artifact.study.id,
            'pt_id': artifact.prep_templates[0].id,
            'sample_1': md5_sums['%d.Sample1' % self.study_id],
            'sample_2': md5_sums['%d.Sample2' % self.study_id],
            'sample_3': md5_sums['%d.Sample3' % self.study_id]
        }
        exp = ''.join([line.strip() for line in exp.splitlines()])
        self.assertEqual(obs.decode('ascii'), exp)

        artifact = self.write_demux_files(PrepTemplate(1))
        submission = EBISubmission(artifact.id, 'ADD')

        # removing samples so test text is easier to read
        keys_to_del = ['1.SKD6.640190', '1.SKM6.640187', '1.SKD9.640182',
                       '1.SKM8.640201', '1.SKM2.640199']
        for k in keys_to_del:
            del(submission.samples[k])
            del(submission.samples_prep[k])

        submission.generate_demultiplexed_fastq(mtime=1)
        self.files_to_remove.append(submission.full_ebi_dir)
        obs = ET.tostring(submission.generate_run_xml())

        exp = RUNXML % {
            'study_alias': submission._get_study_alias(),
            'ebi_dir': submission.ebi_dir,
            'organization_prefix': qiita_config.ebi_organization_prefix,
            'center_name': qiita_config.ebi_center_name,
            'artifact_id': artifact.id}
        exp = ''.join([line.strip() for line in exp.splitlines()])
        self.assertEqual(obs.decode('ascii'), exp)

    def test_generate_xml_files(self):
        artifact = self.generate_new_study_with_preprocessed_data()
        e = EBISubmission(artifact.id, 'ADD')
        self.files_to_remove.append(e.full_ebi_dir)
        e.generate_demultiplexed_fastq()
        self.assertIsNone(e.run_xml_fp)
        self.assertIsNone(e.experiment_xml_fp)
        self.assertIsNone(e.sample_xml_fp)
        self.assertIsNone(e.study_xml_fp)
        self.assertIsNone(e.submission_xml_fp)
        e.generate_xml_files()
        self.assertIsNotNone(e.run_xml_fp)
        self.assertIsNotNone(e.experiment_xml_fp)
        self.assertIsNotNone(e.sample_xml_fp)
        self.assertIsNotNone(e.study_xml_fp)
        self.assertIsNotNone(e.submission_xml_fp)

        artifact = self.generate_new_prep_template_and_write_demux_files(True)
        e = EBISubmission(artifact.id, 'ADD')
        self.files_to_remove.append(e.full_ebi_dir)
        e.generate_demultiplexed_fastq()
        self.assertIsNone(e.run_xml_fp)
        self.assertIsNone(e.experiment_xml_fp)
        self.assertIsNone(e.sample_xml_fp)
        self.assertIsNone(e.study_xml_fp)
        self.assertIsNone(e.submission_xml_fp)
        e.generate_xml_files()
        self.assertIsNotNone(e.run_xml_fp)
        self.assertIsNotNone(e.experiment_xml_fp)
        self.assertIsNone(e.sample_xml_fp)
        self.assertIsNone(e.study_xml_fp)
        self.assertIsNotNone(e.submission_xml_fp)

        artifact = self.write_demux_files(PrepTemplate(1))
        e = EBISubmission(artifact.id, 'ADD')
        self.files_to_remove.append(e.full_ebi_dir)
        e.generate_demultiplexed_fastq()
        self.assertIsNone(e.run_xml_fp)
        self.assertIsNone(e.experiment_xml_fp)
        self.assertIsNone(e.sample_xml_fp)
        self.assertIsNone(e.study_xml_fp)
        self.assertIsNone(e.submission_xml_fp)
        e.generate_xml_files()
        self.assertIsNotNone(e.run_xml_fp)
        self.assertIsNone(e.experiment_xml_fp)
        self.assertIsNone(e.sample_xml_fp)
        self.assertIsNone(e.study_xml_fp)
        self.assertIsNotNone(e.submission_xml_fp)

    def test_generate_demultiplexed_fastq_failure(self):
        # generating demux file for testing
        artifact = self.write_demux_files(PrepTemplate(1), 'EMPTY')

        ebi_submission = EBISubmission(artifact.id, 'ADD')
        self.files_to_remove.append(ebi_submission.full_ebi_dir)
        with self.assertRaises(EBISubmissionError):
            ebi_submission.generate_demultiplexed_fastq(rewrite_fastq=True)

        artifact = self.write_demux_files(PrepTemplate(1), 'WRONG-SEQS')
        ebi_submission = EBISubmission(artifact.id, 'ADD')
        self.files_to_remove.append(ebi_submission.full_ebi_dir)
        with self.assertRaises(EBISubmissionError):
            ebi_submission.generate_demultiplexed_fastq()

    def test_generate_demultiplexed_fastq(self):
        # generating demux file for testing
        exp_demux_samples = set(
            ['1.SKD6.640190', '1.SKM6.640187', '1.SKD9.640182',
             '1.SKB2.640194', '1.SKM8.640201', '1.SKM4.640180',
             '1.SKM2.640199', '1.SKB3.640195', '1.SKB6.640176'])

        artifact = self.write_demux_files(PrepTemplate(1))
        # This is testing that only the samples with sequences are going to
        # be created
        ebi_submission = EBISubmission(artifact.id, 'ADD')
        # adding rewrite_fastq=True as it's possible to have duplicated ids
        # and this will assure to get the right test
        obs_demux_samples = ebi_submission.generate_demultiplexed_fastq(
            rewrite_fastq=True)

        self.files_to_remove.append(ebi_submission.full_ebi_dir)
        self.assertCountEqual(obs_demux_samples, exp_demux_samples)
        # testing that the samples/samples_prep and demux_samples are the same
        self.assertCountEqual(obs_demux_samples, ebi_submission.samples.keys())
        self.assertCountEqual(obs_demux_samples,
                              ebi_submission.samples_prep.keys())

        # If the last test passed then we can test that the folder already
        # exists and that we have the same files and ignore not fastq.gz files
        ebi_submission = EBISubmission(artifact.id, 'ADD')
        obs_demux_samples = ebi_submission.generate_demultiplexed_fastq()
        self.files_to_remove.append(ebi_submission.full_ebi_dir)
        self.assertCountEqual(obs_demux_samples, exp_demux_samples)
        # testing that the samples/samples_prep and demux_samples are the same
        self.assertCountEqual(obs_demux_samples, ebi_submission.samples.keys())
        self.assertCountEqual(obs_demux_samples,
                              ebi_submission.samples_prep.keys())

    def _generate_per_sample_FASTQs(self, prep_template, sequences):
        # generating a per_sample_FASTQ artifact, adding should_rename so
        # we can test that the script uses the correct names during
        # copy/gz-generation
        files = []
        for sn, seqs in sequences.items():
            fn = join(self.temp_dir, sn + 'should_rename.fastq')
            with open(fn, 'w') as fh:
                fh.write(seqs)
            files.append(fn)
            self.files_to_remove.append(fn)

        if prep_template.artifact is None:
            artifact = Artifact.create(
                [(fp, 1) for fp in files], "per_sample_FASTQ",
                prep_template=prep_template)
        else:
            params = Parameters.from_default_params(
                DefaultParameters(1),
                {'input_data': prep_template.artifact.id})
            artifact = Artifact.create(
                # 1 is raw_forward_seqs
                [(fp, 1) for fp in files], "per_sample_FASTQ",
                parents=[prep_template.artifact],
                processing_parameters=params)

        return artifact

    def test_generate_demultiplexed_per_sample_fastq(self):
        # testing failure due to "extra" filepaths
        artifact = self._generate_per_sample_FASTQs(
            PrepTemplate(1), FASTQ_EXAMPLE)
        ebi_submission = EBISubmission(artifact.id, 'ADD')
        self.files_to_remove.append(ebi_submission.full_ebi_dir)

        with self.assertRaises(EBISubmissionError):
            ebi_submission.generate_demultiplexed_fastq()

        # testing that we generate the correct samples
        exp_samples = ['1.SKM4.640180', '1.SKB2.640194']
        metadata_dict = {
            'SKB2.640194': {'center_name': 'ANL',
                            'center_project_name': 'Test Project',
                            'platform': 'Illumina',
                            'instrument_model': 'Illumina MiSeq',
                            'experiment_design_description':
                                'microbiome of soil and rhizosphere',
                            'library_construction_protocol':
                                'PMID: 22402401',
                            'run_prefix': '1.SKB2.640194'},
            'SKM4.640180': {'center_name': 'ANL',
                            'center_project_name': 'Test Project',
                            'platform': 'Illumina',
                            'instrument_model': 'Illumina MiSeq',
                            'experiment_design_description':
                                'microbiome of soil and rhizosphere',
                            'library_construction_protocol':
                                'PMID: 22402401',
                            'run_prefix': '1.SKM4.640180'}}
        metadata = pd.DataFrame.from_dict(
            metadata_dict, orient='index', dtype=str)
        with warnings.catch_warnings(record=True):
            pt = PrepTemplate.create(metadata, Study(1), "18S",
                                     investigation_type="Metagenomics")
        artifact = self._generate_per_sample_FASTQs(pt, FASTQ_EXAMPLE)

        # this should fail due to missing columns
        with self.assertRaises(EBISubmissionError) as err:
            ebi_submission = EBISubmission(artifact.id, 'ADD')
        self.assertIn('Missing column in the prep template: barcode',
                      str(err.exception))
        metadata_dict = {
            'SKB2.640194': {'barcode': 'AAA', 'primer': 'CCCC'},
            'SKM4.640180': {'barcode': 'CCC', 'primer': 'AAAA'}}
        metadata = pd.DataFrame.from_dict(
            metadata_dict, orient='index', dtype=str)

        with warnings.catch_warnings(record=True):
            pt.extend_and_update(metadata)
        ebi_submission = EBISubmission(artifact.id, 'ADD')
        self.files_to_remove.append(ebi_submission.full_ebi_dir)

        obs_demux_samples = ebi_submission.generate_demultiplexed_fastq()
        self.assertCountEqual(obs_demux_samples, exp_samples)
        self.assertCountEqual(ebi_submission.samples.keys(), exp_samples)
        self.assertCountEqual(ebi_submission.samples_prep.keys(), exp_samples)

        ebi_submission.generate_xml_files()
        obs_run_xml = open(ebi_submission.run_xml_fp).read()
        obs_experiment_xml = open(ebi_submission.experiment_xml_fp).read()
        self.assertIn('1.SKB2.640194.R1.fastq.gz', obs_run_xml)
        self.assertNotIn('1.SKB2.640194.R2.fastq.gz', obs_run_xml)
        self.assertIn('1.SKM4.640180.R1.fastq.gz', obs_run_xml)
        self.assertNotIn('1.SKM4.640180.R2.fastq.gz', obs_run_xml)
        self.assertNotIn('PAIRED', obs_experiment_xml)
        self.assertIn('SINGLE', obs_experiment_xml)
        # generate_send_sequences_cmd returns a list of commands so joining
        # for easier testing
        obs_cmd = '|'.join(ebi_submission.generate_send_sequences_cmd())
        self.assertIn('1.SKB2.640194.R1.fastq.gz', obs_cmd)
        self.assertNotIn('1.SKB2.640194.R2.fastq.gz', obs_cmd)
        self.assertIn('1.SKM4.640180.R1.fastq.gz', obs_cmd)
        self.assertNotIn('1.SKM4.640180.R2.fastq.gz', obs_cmd)

        # at this point the full_ebi_dir has been created so we can test that
        # the ADD actually works without rewriting the files
        ebi_submission = EBISubmission(artifact.id, 'ADD')
        obs_demux_samples = ebi_submission.generate_demultiplexed_fastq()
        self.assertCountEqual(obs_demux_samples, exp_samples)
        self.assertCountEqual(ebi_submission.samples.keys(), exp_samples)
        self.assertCountEqual(ebi_submission.samples_prep.keys(), exp_samples)

        ebi_submission.generate_xml_files()
        obs_run_xml = open(ebi_submission.run_xml_fp).read()
        obs_experiment_xml = open(ebi_submission.experiment_xml_fp).read()
        self.assertIn('1.SKB2.640194.R1.fastq.gz', obs_run_xml)
        self.assertNotIn('1.SKB2.640194.R2.fastq.gz', obs_run_xml)
        self.assertIn('1.SKM4.640180.R1.fastq.gz', obs_run_xml)
        self.assertNotIn('1.SKM4.640180.R2.fastq.gz', obs_run_xml)
        self.assertNotIn('PAIRED', obs_experiment_xml)
        self.assertIn('SINGLE', obs_experiment_xml)
        # generate_send_sequences_cmd returns a list of commands so joining
        # for easier testing
        obs_cmd = '|'.join(ebi_submission.generate_send_sequences_cmd())
        self.assertIn('1.SKB2.640194.R1.fastq.gz', obs_cmd)
        self.assertNotIn('1.SKB2.640194.R2.fastq.gz', obs_cmd)
        self.assertIn('1.SKM4.640180.R1.fastq.gz', obs_cmd)
        self.assertNotIn('1.SKM4.640180.R2.fastq.gz', obs_cmd)

        Artifact.delete(artifact.id)
        PrepTemplate.delete(pt.id)

    def test_generate_demultiplexed_per_sample_fastq_reverse(self):
        metadata_dict = {
            'SKB2.640194': {'barcode': 'AAA',
                            'primer': 'CCCC',
                            'center_name': 'ANL',
                            'center_project_name': 'Test Project',
                            'platform': 'Illumina',
                            'instrument_model': 'Illumina MiSeq',
                            'experiment_design_description':
                                'microbiome of soil and rhizosphere',
                            'library_construction_protocol':
                                'PMID: 22402401',
                            'run_prefix': '1.SKB2.640194'},
            'SKM4.640180': {'barcode': 'CCC',
                            'primer': 'AAAA',
                            'center_name': 'ANL',
                            'center_project_name': 'Test Project',
                            'platform': 'Illumina',
                            'instrument_model': 'Illumina MiSeq',
                            'experiment_design_description':
                                'microbiome of soil and rhizosphere',
                            'library_construction_protocol':
                                'PMID: 22402401',
                            'run_prefix': '1.SKM4.640180'}}
        metadata = pd.DataFrame.from_dict(
            metadata_dict, orient='index', dtype=str)
        with warnings.catch_warnings(record=True):
            pt = PrepTemplate.create(metadata, Study(1), "18S",
                                     investigation_type="Metagenomics")
        filepaths = []
        for sn in pt:
            # 1 is forward, 2 is reverse
            filepaths.append((join(self.temp_dir, sn + '_rename.R1.fastq'), 1))
            filepaths.append((join(self.temp_dir, sn + '_rename.R2.fastq'), 2))
        for fn, _ in filepaths:
            with open(fn, 'w') as fh:
                fh.write('some text')
            self.files_to_remove.append(fn)
        artifact = Artifact.create(
            filepaths, "per_sample_FASTQ", prep_template=pt)

        ebi_submission = EBISubmission(artifact.id, 'ADD')
        self.files_to_remove.append(ebi_submission.full_ebi_dir)

        obs_demux_samples = ebi_submission.generate_demultiplexed_fastq()
        exp_samples = ['1.SKM4.640180', '1.SKB2.640194']
        self.assertCountEqual(obs_demux_samples, exp_samples)
        self.assertCountEqual(ebi_submission.samples.keys(), exp_samples)
        self.assertCountEqual(ebi_submission.samples_prep.keys(), exp_samples)

        ebi_submission.generate_xml_files()
        obs_run_xml = open(ebi_submission.run_xml_fp).read()
        obs_experiment_xml = open(ebi_submission.experiment_xml_fp).read()
        self.assertIn('1.SKB2.640194.R1.fastq.gz', obs_run_xml)
        self.assertIn('1.SKB2.640194.R2.fastq.gz', obs_run_xml)
        self.assertIn('1.SKM4.640180.R1.fastq.gz', obs_run_xml)
        self.assertIn('1.SKM4.640180.R2.fastq.gz', obs_run_xml)
        self.assertIn('PAIRED', obs_experiment_xml)
        self.assertNotIn('SINGLE', obs_experiment_xml)
        # generate_send_sequences_cmd returns a list of commands so joining
        # for easier testing
        obs_cmd = '|'.join(ebi_submission.generate_send_sequences_cmd())
        self.assertIn('1.SKB2.640194.R1.fastq.gz', obs_cmd)
        self.assertIn('1.SKB2.640194.R2.fastq.gz', obs_cmd)
        self.assertIn('1.SKM4.640180.R1.fastq.gz', obs_cmd)
        self.assertIn('1.SKM4.640180.R2.fastq.gz', obs_cmd)

        # now we have a full submission so let's test if a new one will create
        # the correct values without rewriting the fastq files
        ebi_submission = EBISubmission(artifact.id, 'ADD')
        obs_demux_samples = ebi_submission.generate_demultiplexed_fastq()
        exp_samples = ['1.SKM4.640180', '1.SKB2.640194']
        self.assertCountEqual(obs_demux_samples, exp_samples)
        self.assertCountEqual(ebi_submission.samples.keys(), exp_samples)
        self.assertCountEqual(ebi_submission.samples_prep.keys(), exp_samples)

        ebi_submission.generate_xml_files()
        obs_run_xml = open(ebi_submission.run_xml_fp).read()
        obs_experiment_xml = open(ebi_submission.experiment_xml_fp).read()
        self.assertIn('1.SKB2.640194.R1.fastq.gz', obs_run_xml)
        self.assertIn('1.SKB2.640194.R2.fastq.gz', obs_run_xml)
        self.assertIn('1.SKM4.640180.R1.fastq.gz', obs_run_xml)
        self.assertIn('1.SKM4.640180.R2.fastq.gz', obs_run_xml)
        self.assertIn('PAIRED', obs_experiment_xml)
        self.assertNotIn('SINGLE', obs_experiment_xml)
        # generate_send_sequences_cmd returns a list of commands so joining
        # for easier testing
        obs_cmd = '|'.join(ebi_submission.generate_send_sequences_cmd())
        self.assertIn('1.SKB2.640194.R1.fastq.gz', obs_cmd)
        self.assertIn('1.SKB2.640194.R2.fastq.gz', obs_cmd)
        self.assertIn('1.SKM4.640180.R1.fastq.gz', obs_cmd)
        self.assertIn('1.SKM4.640180.R2.fastq.gz', obs_cmd)

        Artifact.delete(artifact.id)
        PrepTemplate.delete(pt.id)

    def test_generate_send_sequences_cmd(self):
        artifact = self.write_demux_files(PrepTemplate(1))
        e = EBISubmission(artifact.id, 'ADD')
        e.generate_demultiplexed_fastq()
        self.files_to_remove.append(e.full_ebi_dir)
        e.generate_xml_files()
        obs = e.generate_send_sequences_cmd()
        _, base_fp = get_mountpoint("preprocessed_data")[0]
        exp = ('ascp --ignore-host-key -d -QT -k2 '
               '%(ebi_dir)s/1.SKB2.640194.R1.fastq.gz '
               'Webin-41528@webin.ebi.ac.uk:./%(aid)d_ebi_submission/\n'
               'ascp --ignore-host-key -d -QT -k2 '
               '%(ebi_dir)s/1.SKM4.640180.R1.fastq.gz '
               'Webin-41528@webin.ebi.ac.uk:./%(aid)d_ebi_submission/\n'
               'ascp --ignore-host-key -d -QT -k2 '
               '%(ebi_dir)s/1.SKB3.640195.R1.fastq.gz '
               'Webin-41528@webin.ebi.ac.uk:./%(aid)d_ebi_submission/\n'
               'ascp --ignore-host-key -d -QT -k2 '
               '%(ebi_dir)s/1.SKB6.640176.R1.fastq.gz '
               'Webin-41528@webin.ebi.ac.uk:./%(aid)d_ebi_submission/\n'
               'ascp --ignore-host-key -d -QT -k2 '
               '%(ebi_dir)s/1.SKD6.640190.R1.fastq.gz '
               'Webin-41528@webin.ebi.ac.uk:./%(aid)d_ebi_submission/\n'
               'ascp --ignore-host-key -d -QT -k2 '
               '%(ebi_dir)s/1.SKM6.640187.R1.fastq.gz '
               'Webin-41528@webin.ebi.ac.uk:./%(aid)d_ebi_submission/\n'
               'ascp --ignore-host-key -d -QT -k2 '
               '%(ebi_dir)s/1.SKD9.640182.R1.fastq.gz '
               'Webin-41528@webin.ebi.ac.uk:./%(aid)d_ebi_submission/\n'
               'ascp --ignore-host-key -d -QT -k2 '
               '%(ebi_dir)s/1.SKM8.640201.R1.fastq.gz '
               'Webin-41528@webin.ebi.ac.uk:./%(aid)d_ebi_submission/\n'
               'ascp --ignore-host-key -d -QT -k2 '
               '%(ebi_dir)s/1.SKM2.640199.R1.fastq.gz '
               'Webin-41528@webin.ebi.ac.uk:./%(aid)d_ebi_submission/' % {
                   'ebi_dir': e.full_ebi_dir, 'aid': artifact.id}).split('\n')
        self.assertCountEqual(obs, exp)

    def test_parse_EBI_reply(self):
        artifact = self.generate_new_study_with_preprocessed_data()
        study_id = artifact.study.id
        e = EBISubmission(artifact.id, 'ADD')
        self.files_to_remove.append(e.full_ebi_dir)
        e.generate_demultiplexed_fastq(mtime=1)
        e.generate_xml_files()
        curl_result = CURL_RESULT_FULL.format(
            qiita_config.ebi_organization_prefix, artifact.id, study_id,
            artifact.prep_templates[0].id)
        stacc, saacc, bioacc, exacc, runacc = e.parse_EBI_reply(curl_result)

        self.assertEqual(stacc, 'ERP000000')
        study_id = artifact.study.id
        exp_saacc = {'%d.Sample1' % study_id: 'ERS000000',
                     '%d.Sample2' % study_id: 'ERS000001',
                     '%d.Sample3' % study_id: 'ERS000002'}
        self.assertEqual(saacc, exp_saacc)
        exp_bioacc = {'%d.Sample1' % study_id: 'SAMEA0000000',
                      '%d.Sample2' % study_id: 'SAMEA0000001',
                      '%d.Sample3' % study_id: 'SAMEA0000002'}
        self.assertEqual(bioacc, exp_bioacc)
        exp_exacc = {'%d.Sample1' % study_id: 'ERX0000000',
                     '%d.Sample2' % study_id: 'ERX0000001',
                     '%d.Sample3' % study_id: 'ERX0000002'}
        self.assertEqual(exacc, exp_exacc)
        exp_runacc = {'%d.Sample1' % study_id: 'ERR0000000',
                      '%d.Sample2' % study_id: 'ERR0000001',
                      '%d.Sample3' % study_id: 'ERR0000002'}
        self.assertEqual(runacc, exp_runacc)

        artifact = self.write_demux_files(PrepTemplate(1))
        e = EBISubmission(artifact.id, 'ADD')
        self.files_to_remove.append(e.full_ebi_dir)
        # removing samples so test text is easier to read
        keys_to_del = ['1.SKD6.640190', '1.SKM6.640187', '1.SKD9.640182',
                       '1.SKM8.640201', '1.SKM2.640199', '1.SKB3.640195']
        for k in keys_to_del:
            del(e.samples[k])
            del(e.samples_prep[k])

        # Genereate the XML files so the aliases are generated
        # and stored internally
        e.generate_demultiplexed_fastq(mtime=1)
        e.generate_xml_files()

        curl_result = ""
        with self.assertRaises(EBISubmissionError):
            e.parse_EBI_reply(curl_result)

        curl_result = 'success="true"'
        with self.assertRaises(EBISubmissionError):
            e.parse_EBI_reply(curl_result)

        curl_result = ('some general text success="true" more text'
                       '<STUDY accession="staccession" some text> '
                       'some othe text'
                       '<SUBMISSION accession="sbaccession" some text>'
                       'some final text')
        with self.assertRaises(EBISubmissionError):
            e.parse_EBI_reply(curl_result)

        curl_result = CURL_RESULT_2_STUDY.format(
            qiita_config.ebi_organization_prefix, artifact.id)
        with self.assertRaises(EBISubmissionError):
            e.parse_EBI_reply(curl_result)

        curl_result = CURL_RESULT.format(qiita_config.ebi_organization_prefix,
                                         artifact.id)
        stacc, saacc, bioacc, exacc, runacc = e.parse_EBI_reply(curl_result)
        self.assertEqual(stacc, None)
        self.assertEqual(saacc, {})
        self.assertEqual(bioacc, {})
        self.assertEqual(exacc, {})
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

FASTQ_EXAMPLE = {
    '1.SKB2.640194': """@1.SKB2.640194_1 X orig_bc=X new_bc=X bc_diffs=0
CCACCCAGTAAC
+
~~~~~~~~~~~~
@1.SKB2.640194_2 X orig_bc=X new_bc=X bc_diffs=0
CCACCCAGTAAC
+
~~~~~~~~~~~~
@1.SKB2.640194_3 X orig_bc=X new_bc=X bc_diffs=0
+
~~~~~~~~~~~~
CCACCCAGTAAC""",
    '1.SKM4.640180': """@1.SKM4.640180_4 X orig_bc=X new_bc=X bc_diffs=0
CCACCCAGTAAC
+
~~~~~~~~~~~~
>1.SKM4.640180_5 X orig_bc=X new_bc=X bc_diffs=0
CCACCCAGTAAC
+
~~~~~~~~~~~~"""
}

FASTA_EXAMPLE_2 = """>{0}.Sample1_1 X orig_bc=X new_bc=X bc_diffs=0
CCACCCAGTAAC
>{0}.Sample1_2 X orig_bc=X new_bc=X bc_diffs=0
CCACCCAGTAAC
>{0}.Sample1_3 X orig_bc=X new_bc=X bc_diffs=0
CCACCCAGTAAC
>{0}.Sample2_4 X orig_bc=X new_bc=X bc_diffs=0
CCACCCAGTAAC
>{0}.Sample2_5 X orig_bc=X new_bc=X bc_diffs=0
CCACCCAGTAAC
>{0}.Sample2_6 X orig_bc=X new_bc=X bc_diffs=0
CCACCCAGTAAC
>{0}.Sample3_7 X orig_bc=X new_bc=X bc_diffs=0
CCACCCAGTAAC
>{0}.Sample3_8 X orig_bc=X new_bc=X bc_diffs=0
CCACCCAGTAAC
>{0}.Sample3_9 X orig_bc=X new_bc=X bc_diffs=0
CCACCCAGTAAC
"""

SAMPLEXML = """
<SAMPLE_SET xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noName\
spaceSchemaLocation="ftp://ftp.sra.ebi.ac.uk/meta/xsd/sra_1_3/SRA.sample.xsd">
  <SAMPLE accession="ERS000008" center_name="%(center_name)s">
      <TITLE>1.SKB2.640194</TITLE>
    <SAMPLE_NAME>
      <TAXON_ID>410658</TAXON_ID>
      <SCIENTIFIC_NAME>1118232</SCIENTIFIC_NAME>
    </SAMPLE_NAME>
    <DESCRIPTION>Cannabis Soil Microbiome</DESCRIPTION>
    <SAMPLE_ATTRIBUTES>
      <SAMPLE_ATTRIBUTE>
        <TAG>altitude</TAG><VALUE>0</VALUE>
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
        <TAG>dna_extracted</TAG><VALUE>true</VALUE>
      </SAMPLE_ATTRIBUTE>
      <SAMPLE_ATTRIBUTE>
        <TAG>elevation</TAG><VALUE>114</VALUE>
      </SAMPLE_ATTRIBUTE>
      <SAMPLE_ATTRIBUTE>
        <TAG>env_biome</TAG><VALUE>ENVO:Temperate grasslands, savannas, and \
shrubland biome</VALUE>
      </SAMPLE_ATTRIBUTE>
      <SAMPLE_ATTRIBUTE>
        <TAG>env_feature</TAG><VALUE>ENVO:plant-associated habitat</VALUE>
      </SAMPLE_ATTRIBUTE>
      <SAMPLE_ATTRIBUTE>
        <TAG>env_package</TAG><VALUE>soil</VALUE>
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
        <TAG>physical_specimen_remaining</TAG><VALUE>true</VALUE>
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
        <TAG>temp</TAG><VALUE>15</VALUE></SAMPLE_ATTRIBUTE>
      <SAMPLE_ATTRIBUTE>
        <TAG>texture</TAG><VALUE>64.6 sand, 17.6 silt, 17.8 clay</VALUE>
      </SAMPLE_ATTRIBUTE>
      <SAMPLE_ATTRIBUTE>
        <TAG>tot_nitro</TAG><VALUE>1.41</VALUE>
      </SAMPLE_ATTRIBUTE>
      <SAMPLE_ATTRIBUTE>
        <TAG>tot_org_carb</TAG><VALUE>5</VALUE>
      </SAMPLE_ATTRIBUTE>
      <SAMPLE_ATTRIBUTE>
        <TAG>water_content_soil</TAG><VALUE>0.164</VALUE>
      </SAMPLE_ATTRIBUTE>
    </SAMPLE_ATTRIBUTES>
  </SAMPLE>
  <SAMPLE accession="ERS000024" center_name="%(center_name)s">
    <TITLE>1.SKB3.640195</TITLE>
    <SAMPLE_NAME>
      <TAXON_ID>410658</TAXON_ID>
      <SCIENTIFIC_NAME>1118232</SCIENTIFIC_NAME>
    </SAMPLE_NAME>
    <DESCRIPTION>Cannabis Soil Microbiome</DESCRIPTION>
      <SAMPLE_ATTRIBUTES>
      <SAMPLE_ATTRIBUTE>
        <TAG>altitude</TAG><VALUE>0</VALUE>
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
        <TAG>dna_extracted</TAG><VALUE>true</VALUE>
      </SAMPLE_ATTRIBUTE>
      <SAMPLE_ATTRIBUTE>
        <TAG>elevation</TAG><VALUE>114</VALUE>
      </SAMPLE_ATTRIBUTE>
      <SAMPLE_ATTRIBUTE>
        <TAG>env_biome</TAG><VALUE>ENVO:Temperate grasslands, savannas, and \
shrubland biome</VALUE>
      </SAMPLE_ATTRIBUTE>
      <SAMPLE_ATTRIBUTE>
        <TAG>env_feature</TAG><VALUE>ENVO:plant-associated habitat</VALUE>
      </SAMPLE_ATTRIBUTE>
      <SAMPLE_ATTRIBUTE>
        <TAG>env_package</TAG><VALUE>soil</VALUE>
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
        <TAG>physical_specimen_remaining</TAG><VALUE>true</VALUE>
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
        <TAG>temp</TAG><VALUE>15</VALUE>
      </SAMPLE_ATTRIBUTE>
      <SAMPLE_ATTRIBUTE>
        <TAG>texture</TAG><VALUE>64.6 sand, 17.6 silt, 17.8 clay</VALUE>
      </SAMPLE_ATTRIBUTE>
      <SAMPLE_ATTRIBUTE>
        <TAG>tot_nitro</TAG><VALUE>1.41</VALUE>
      </SAMPLE_ATTRIBUTE>
      <SAMPLE_ATTRIBUTE>
        <TAG>tot_org_carb</TAG><VALUE>5</VALUE>
      </SAMPLE_ATTRIBUTE>
      <SAMPLE_ATTRIBUTE>
        <TAG>water_content_soil</TAG><VALUE>0.164</VALUE>
      </SAMPLE_ATTRIBUTE>
    </SAMPLE_ATTRIBUTES>
  </SAMPLE>
 </SAMPLE_SET>
 """ % {'center_name': qiita_config.ebi_center_name}

STUDYXML = """
<STUDY_SET xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noName\
spaceSchemaLocation="ftp://ftp.sra.ebi.ac.uk/meta/xsd/sra_1_3/SRA.study.xsd">
  <STUDY alias="%(organization_prefix)s_sid_1" center_name="%(center_name)s">
    <DESCRIPTOR>
      <STUDY_TITLE>
        Identification of the Microbiomes for Cannabis Soils
      </STUDY_TITLE>
      <STUDY_TYPE existing_study_type="Other" />
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
        <XREF_LINK><DB>DOI</DB><ID>10.100/123456</ID></XREF_LINK>
      </STUDY_LINK>
      <STUDY_LINK>
        <XREF_LINK><DB>PUBMED</DB><ID>123456</ID></XREF_LINK>
      </STUDY_LINK>
      <STUDY_LINK>
        <XREF_LINK><DB>DOI</DB><ID>10.100/7891011</ID></XREF_LINK>
      </STUDY_LINK>
      <STUDY_LINK>
       <XREF_LINK><DB>PUBMED</DB><ID>7891011</ID></XREF_LINK>
      </STUDY_LINK>
    </STUDY_LINKS>
  </STUDY>
</STUDY_SET>
""" % {'organization_prefix': qiita_config.ebi_organization_prefix,
       'center_name': qiita_config.ebi_center_name}

EXPERIMENTXML_NEWSTUDY = """
<EXPERIMENT_SET xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:no\
NamespaceSchemaLocation="ftp://ftp.sra.ebi.ac.uk/meta/xsd/sra_1_3/SRA.\
experiment.xsd">
  <EXPERIMENT alias="%(organization_prefix)s_ptid_%(pt_id)s:\
%(study_id)s.Sample1" center_name="%(center_name)s">
    <TITLE>%(organization_prefix)s_ptid_%(pt_id)s:%(study_id)s.Sample1</TITLE>
    <STUDY_REF refname="%(organization_prefix)s_sid_%(study_id)s" />
    <DESIGN>
      <DESIGN_DESCRIPTION>
        Random value 1
      </DESIGN_DESCRIPTION>
      <SAMPLE_DESCRIPTOR refname="%(organization_prefix)s_sid_%(study_id)s:\
%(study_id)s.Sample1" />
      <LIBRARY_DESCRIPTOR>
        <LIBRARY_NAME>%(study_id)s.Sample1</LIBRARY_NAME>
        <LIBRARY_STRATEGY>METAGENOMICS</LIBRARY_STRATEGY>
        <LIBRARY_SOURCE>METAGENOMIC</LIBRARY_SOURCE>
        <LIBRARY_SELECTION>PCR</LIBRARY_SELECTION>
        <LIBRARY_LAYOUT><SINGLE /></LIBRARY_LAYOUT>
        <LIBRARY_CONSTRUCTION_PROTOCOL>Protocol ABC
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
        <TAG>center_name</TAG><VALUE>KnightLab</VALUE>
      </EXPERIMENT_ATTRIBUTE>
      <EXPERIMENT_ATTRIBUTE>
        <TAG>primer</TAG><VALUE>GTGCCAGCMGCCGCGGTAA</VALUE>
      </EXPERIMENT_ATTRIBUTE>
    </EXPERIMENT_ATTRIBUTES>
  </EXPERIMENT>
  <EXPERIMENT alias="%(organization_prefix)s_ptid_%(pt_id)s:\
%(study_id)s.Sample2" center_name="%(center_name)s">
    <TITLE>%(organization_prefix)s_ptid_%(pt_id)s:%(study_id)s.Sample2</TITLE>
    <STUDY_REF refname="%(organization_prefix)s_sid_%(study_id)s" />
    <DESIGN>
      <DESIGN_DESCRIPTION>
        Random value 2
      </DESIGN_DESCRIPTION>
      <SAMPLE_DESCRIPTOR refname="%(organization_prefix)s_sid_%(study_id)s:\
%(study_id)s.Sample2" />
      <LIBRARY_DESCRIPTOR>
        <LIBRARY_NAME>%(study_id)s.Sample2</LIBRARY_NAME>
        <LIBRARY_STRATEGY>METAGENOMICS</LIBRARY_STRATEGY>
        <LIBRARY_SOURCE>METAGENOMIC</LIBRARY_SOURCE>
        <LIBRARY_SELECTION>PCR</LIBRARY_SELECTION>
        <LIBRARY_LAYOUT><SINGLE /></LIBRARY_LAYOUT>
        <LIBRARY_CONSTRUCTION_PROTOCOL>Protocol ABC
        </LIBRARY_CONSTRUCTION_PROTOCOL>
      </LIBRARY_DESCRIPTOR>
    </DESIGN>
    <PLATFORM>
      <ILLUMINA><INSTRUMENT_MODEL>Illumina MiSeq</INSTRUMENT_MODEL></ILLUMINA>
    </PLATFORM>
    <EXPERIMENT_ATTRIBUTES>
      <EXPERIMENT_ATTRIBUTE>
        <TAG>barcode</TAG><VALUE>CGTAGAGCTCTA</VALUE>
      </EXPERIMENT_ATTRIBUTE>
      <EXPERIMENT_ATTRIBUTE>
        <TAG>center_name</TAG><VALUE>KnightLab</VALUE>
      </EXPERIMENT_ATTRIBUTE>
      <EXPERIMENT_ATTRIBUTE>
        <TAG>primer</TAG><VALUE>GTGCCAGCMGCCGCGGTAA</VALUE>
      </EXPERIMENT_ATTRIBUTE>
    </EXPERIMENT_ATTRIBUTES>
  </EXPERIMENT>
  <EXPERIMENT alias="%(organization_prefix)s_ptid_%(pt_id)s:\
%(study_id)s.Sample3" center_name="%(center_name)s">
    <TITLE>%(organization_prefix)s_ptid_%(pt_id)s:%(study_id)s.Sample3</TITLE>
    <STUDY_REF refname="%(organization_prefix)s_sid_%(study_id)s" />
    <DESIGN>
      <DESIGN_DESCRIPTION>
        Random value 3
      </DESIGN_DESCRIPTION>
      <SAMPLE_DESCRIPTOR refname="%(organization_prefix)s_sid_%(study_id)s:\
%(study_id)s.Sample3" />
      <LIBRARY_DESCRIPTOR>
        <LIBRARY_NAME>%(study_id)s.Sample3</LIBRARY_NAME>
        <LIBRARY_STRATEGY>METAGENOMICS</LIBRARY_STRATEGY>
        <LIBRARY_SOURCE>METAGENOMIC</LIBRARY_SOURCE>
        <LIBRARY_SELECTION>PCR</LIBRARY_SELECTION>
        <LIBRARY_LAYOUT><SINGLE /></LIBRARY_LAYOUT>
        <LIBRARY_CONSTRUCTION_PROTOCOL>Protocol ABC
        </LIBRARY_CONSTRUCTION_PROTOCOL>
      </LIBRARY_DESCRIPTOR>
    </DESIGN>
    <PLATFORM>
      <ILLUMINA><INSTRUMENT_MODEL>Illumina MiSeq</INSTRUMENT_MODEL></ILLUMINA>
    </PLATFORM>
    <EXPERIMENT_ATTRIBUTES>
      <EXPERIMENT_ATTRIBUTE>
        <TAG>barcode</TAG><VALUE>CGTAGAGCTCTT</VALUE>
      </EXPERIMENT_ATTRIBUTE>
      <EXPERIMENT_ATTRIBUTE>
        <TAG>center_name</TAG><VALUE>KnightLab</VALUE>
      </EXPERIMENT_ATTRIBUTE>
      <EXPERIMENT_ATTRIBUTE>
        <TAG>primer</TAG><VALUE>GTGCCAGCMGCCGCGGTAA</VALUE>
      </EXPERIMENT_ATTRIBUTE>
    </EXPERIMENT_ATTRIBUTES>
  </EXPERIMENT>
</EXPERIMENT_SET>
"""

EXPERIMENTXML = """
<EXPERIMENT_SET xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:no\
NamespaceSchemaLocation="ftp://ftp.sra.ebi.ac.uk/meta/xsd/sra_1_3/SRA.\
experiment.xsd">
  <EXPERIMENT alias="%(organization_prefix)s_ptid_1:1.SKB2.640194" \
center_name="%(center_name)s">
    <TITLE>%(organization_prefix)s_ptid_1:1.SKB2.640194</TITLE>
    <STUDY_REF accession="EBI123456-BB" />
    <DESIGN>
      <DESIGN_DESCRIPTION>
        micro biome of soil and rhizosphere of cannabis plants from CA
      </DESIGN_DESCRIPTION>
      <SAMPLE_DESCRIPTOR accession="ERS000008" />
      <LIBRARY_DESCRIPTOR>
        <LIBRARY_NAME>1.SKB2.640194</LIBRARY_NAME>
        <LIBRARY_STRATEGY>METAGENOMICS</LIBRARY_STRATEGY>
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
        <TAG>center_project_name</TAG><VALUE>Unknown</VALUE>
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
    <STUDY_REF accession="EBI123456-BB" />
    <DESIGN>
      <DESIGN_DESCRIPTION>
        micro biome of soil and rhizosphere of cannabis plants from CA
      </DESIGN_DESCRIPTION>
      <SAMPLE_DESCRIPTOR accession="ERS000024" />
      <LIBRARY_DESCRIPTOR>
        <LIBRARY_NAME>1.SKB3.640195</LIBRARY_NAME>
        <LIBRARY_STRATEGY>METAGENOMICS</LIBRARY_STRATEGY>
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
        <TAG>center_project_name</TAG><VALUE>Unknown</VALUE>
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
  <RUN alias="%(organization_prefix)s_ppdid_%(artifact_id)s:1.SKB2.640194" \
center_name="%(center_name)s">
    <EXPERIMENT_REF accession="ERX0000008" />
    <DATA_BLOCK>
      <FILES>
        <FILE checksum="a32357beb845f5b598f1a712fb3b4c70" \
checksum_method="MD5" filename="%(ebi_dir)s/1.SKB2.640194.R1.fastq.gz" \
filetype="fastq" quality_scoring_system="phred" />
      </FILES>
    </DATA_BLOCK>
  </RUN>
  <RUN alias="%(organization_prefix)s_ppdid_%(artifact_id)s:1.SKB3.640195" \
center_name="%(center_name)s">
    <EXPERIMENT_REF accession="ERX0000024" />
    <DATA_BLOCK>
      <FILES>
        <FILE checksum="deb905ced92812a65a2158fdcfd0f84d" \
checksum_method="MD5" filename="%(ebi_dir)s/1.SKB3.640195.R1.fastq.gz" \
filetype="fastq" quality_scoring_system="phred" />
      </FILES>
    </DATA_BLOCK>
  </RUN>
  <RUN alias="%(organization_prefix)s_ppdid_%(artifact_id)s:1.SKB6.640176" \
center_name="%(center_name)s">
    <EXPERIMENT_REF accession="ERX0000025" />
    <DATA_BLOCK>
      <FILES>
        <FILE checksum="847ba142770397a2fae3a8acfbc70640" \
checksum_method="MD5" filename="%(ebi_dir)s/1.SKB6.640176.R1.fastq.gz" \
filetype="fastq" quality_scoring_system="phred" />
      </FILES>
    </DATA_BLOCK>
  </RUN>
  <RUN alias="%(organization_prefix)s_ppdid_%(artifact_id)s:1.SKM4.640180" \
center_name="%(center_name)s">
    <EXPERIMENT_REF accession="ERX0000004" />
    <DATA_BLOCK>
      <FILES>
        <FILE checksum="0dc19bc7ad4ab613c3f738cc9eb57e2c" \
checksum_method="MD5" filename="%(ebi_dir)s/1.SKM4.640180.R1.fastq.gz" \
filetype="fastq" quality_scoring_system="phred" />
      </FILES>
    </DATA_BLOCK>
  </RUN>
</RUN_SET>
"""

RUNXML_NEWSTUDY = """
<RUN_SET xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespace\
SchemaLocation="ftp://ftp.sra.ebi.ac.uk/meta/xsd/sra_1_3/SRA.run.xsd">
  <RUN alias="%(organization_prefix)s_ppdid_%(artifact_id)s:%(study_id)s.\
Sample1" center_name="%(center_name)s">
    <EXPERIMENT_REF refname="%(organization_prefix)s_ptid_%(pt_id)s:\
%(study_id)s.Sample1" />
    <DATA_BLOCK>
      <FILES>
        <FILE checksum="%(sample_1)s" \
checksum_method="MD5" filename="%(ebi_dir)s/%(study_id)s.Sample1.R1.fastq.gz" \
filetype="fastq" quality_scoring_system="phred" />
      </FILES>
    </DATA_BLOCK>
  </RUN>
  <RUN alias="%(organization_prefix)s_ppdid_%(artifact_id)s:%(study_id)s.\
Sample2" center_name="%(center_name)s">
    <EXPERIMENT_REF refname="%(organization_prefix)s_ptid_%(pt_id)s:\
%(study_id)s.Sample2" />
    <DATA_BLOCK>
      <FILES>
        <FILE checksum="%(sample_2)s" \
checksum_method="MD5" filename="%(ebi_dir)s/%(study_id)s.Sample2.R1.fastq.gz" \
filetype="fastq" quality_scoring_system="phred" />
      </FILES>
    </DATA_BLOCK>
  </RUN>
  <RUN alias="%(organization_prefix)s_ppdid_%(artifact_id)s:%(study_id)s.\
Sample3" center_name="%(center_name)s">
    <EXPERIMENT_REF refname="%(organization_prefix)s_ptid_%(pt_id)s:\
%(study_id)s.Sample3" />
    <DATA_BLOCK>
      <FILES>
        <FILE checksum="%(sample_3)s" \
checksum_method="MD5" filename="%(ebi_dir)s/%(study_id)s.Sample3.R1.fastq.gz" \
filetype="fastq" quality_scoring_system="phred" />
      </FILES>
    </DATA_BLOCK>
  </RUN>
</RUN_SET>
"""

SUBMISSIONXML_FULL = """
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

SUBMISSIONXML = """
<SUBMISSION_SET xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:no\
NamespaceSchemaLocation="ftp://ftp.sra.ebi.ac.uk/meta/xsd/sra_1_3/\
SRA.submission.xsd">
  <SUBMISSION alias="%(submission_alias)s" center_name="%(center_name)s">
    <ACTIONS>
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
        <TAG>none</TAG>
        <VALUE>Unknown</VALUE>
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

CURL_RESULT_FULL = """<?xml version="1.0" encoding="UTF-8"?>
<?xml-stylesheet type="text/xsl" href="receipt.xsl"?>
<RECEIPT receiptDate="2015-09-20T23:27:01.924+01:00" \
submissionFile="submission.xml" success="true">
  <EXPERIMENT accession="ERX0000000" alias="{0}_ptid_{3}:{2}.Sample1" \
status="PRIVATE"/>
  <EXPERIMENT accession="ERX0000001" alias="{0}_ptid_{3}:{2}.Sample2" \
status="PRIVATE"/>
  <EXPERIMENT accession="ERX0000002" alias="{0}_ptid_{3}:{2}.Sample3" \
status="PRIVATE"/>
  <RUN accession="ERR0000000" alias="{0}_ppdid_{1}:{2}.Sample1" \
status="PRIVATE"/>
  <RUN accession="ERR0000001" alias="{0}_ppdid_{1}:{2}.Sample2" \
status="PRIVATE"/>
  <RUN accession="ERR0000002" alias="{0}_ppdid_{1}:{2}.Sample3" \
status="PRIVATE"/>
  <SAMPLE accession="ERS000000" alias="{0}_sid_{2}:{2}.Sample1"
status="PRIVATE">
    <EXT_ID accession="SAMEA0000000" type="biosample"/>
  </SAMPLE>
  <SAMPLE accession="ERS000001" alias="{0}_sid_{2}:{2}.Sample2"
status="PRIVATE">
    <EXT_ID accession="SAMEA0000001" type="biosample"/>
  </SAMPLE>
  <SAMPLE accession="ERS000002" alias="{0}_sid_{2}:{2}.Sample3"
status="PRIVATE">
    <EXT_ID accession="SAMEA0000002" type="biosample"/>
  </SAMPLE>
  <STUDY accession="ERP000000" alias="{0}_sid_{2}" status="PRIVATE" \
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

CURL_RESULT = """<?xml version="1.0" encoding="UTF-8"?>
<?xml-stylesheet type="text/xsl" href="receipt.xsl"?>
<RECEIPT receiptDate="2015-09-20T23:27:01.924+01:00" \
submissionFile="submission.xml" success="true">
  <RUN accession="ERR0000000" alias="{0}_ppdid_{1}:1.SKB2.640194" \
status="PRIVATE"/>
  <RUN accession="ERR0000001" alias="{0}_ppdid_{1}:1.SKB6.640176" \
status="PRIVATE"/>
  <RUN accession="ERR0000002" alias="{0}_ppdid_{1}:1.SKM4.640180" \
status="PRIVATE"/>
  <SUBMISSION accession="ERA000000" alias="qiime_submission_570"/>
  <MESSAGES>
    <INFO> ADD action for the following XML: run.xml       </INFO>
  </MESSAGES>
  <ACTIONS>ADD</ACTIONS>
  <ACTIONS>HOLD</ACTIONS>
</RECEIPT>
"""

CURL_RESULT_2_STUDY = """<?xml version="1.0" encoding="UTF-8"?>
<?xml-stylesheet type="text/xsl" href="receipt.xsl"?>
<RECEIPT receiptDate="2015-09-20T23:27:01.924+01:00" \
submissionFile="submission.xml" success="true">
  <EXPERIMENT accession="ERX0000000" alias="{0}_ptid_1:1.SKB2.640194" \
status="PRIVATE"/>
  <RUN accession="ERR0000000" alias="{0}_ppdid_{1}:1.SKB2.640194" \
status="PRIVATE"/>
  <SAMPLE accession="ERS000000" alias="{0}_sid_1:1.SKB2.640194"
status="PRIVATE">
    <EXT_ID accession="SAMEA0000000" type="biosample"/>
  </SAMPLE>
  <STUDY accession="ERP000000" alias="{0}_sid_1" status="PRIVATE" \
holdUntilDate="2016-09-19+01:00"/>
  <STUDY accession="ERP000000" alias="{0}_sid_2" status="PRIVATE" \
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
