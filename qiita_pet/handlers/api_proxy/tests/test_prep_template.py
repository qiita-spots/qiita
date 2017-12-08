# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from unittest import TestCase, main
from os import remove
from os.path import join, exists
from string import ascii_letters
from random import choice
from json import loads

import pandas as pd
import numpy.testing as npt

from qiita_core.util import qiita_test_checker
from qiita_core.qiita_settings import r_client
from qiita_core.testing import wait_for_processing_job
from qiita_db.artifact import Artifact
from qiita_db.metadata_template.prep_template import PrepTemplate
from qiita_db.ontology import Ontology
from qiita_db.study import Study
from qiita_db.util import get_count, get_mountpoint
from qiita_db.exceptions import QiitaDBWarning
from qiita_pet.handlers.api_proxy.prep_template import (
    prep_template_summary_get_req, prep_template_post_req,
    prep_template_delete_req, prep_template_get_req,
    prep_template_graph_get_req, prep_template_filepaths_get_req,
    _process_investigation_type, prep_template_patch_req,
    _check_prep_template_exists, new_prep_template_get_req,
    prep_template_ajax_get_req, _get_ENA_ontology,
    prep_template_jobs_get_req)


class TestPrepAPIReadOnly(TestCase):
    def test_get_ENA_ontology(self):
        obs = _get_ENA_ontology()
        exp = {
            'ENA': ['Cancer Genomics', 'Epigenetics', 'Exome Sequencing',
                    'Forensic or Paleo-genomics', 'Gene Regulation Study',
                    'Metagenomics', 'Pooled Clone Sequencing',
                    'Population Genomics', 'RNASeq', 'Resequencing',
                    'Synthetic Genomics', 'Transcriptome Analysis',
                    'Whole Genome Sequencing', 'Other'],
            'User': []}
        self.assertEqual(obs, exp)

    def test_new_prep_template_get_req(self):
        obs = new_prep_template_get_req(1)
        exp = {
            'status': 'success',
            'prep_files': ['uploaded_file.txt'],
            'data_types': ['16S', '18S', 'ITS', 'Metabolomic', 'Metagenomic',
                           'Multiomic', 'Proteomic'],
            'ontology': {
                'ENA': ['Cancer Genomics', 'Epigenetics', 'Exome Sequencing',
                        'Forensic or Paleo-genomics', 'Gene Regulation Study',
                        'Metagenomics', 'Pooled Clone Sequencing',
                        'Population Genomics', 'RNASeq', 'Resequencing',
                        'Synthetic Genomics', 'Transcriptome Analysis',
                        'Whole Genome Sequencing', 'Other'],
                'User': []}}

        self.assertEqual(obs, exp)

    def test_prep_template_ajax_get_req(self):
        obs = prep_template_ajax_get_req('test@foo.bar', 1)
        exp = {'status': 'success',
               'message': '',
               'name': "Prep information 1",
               'files': ["uploaded_file.txt"],
               'download_prep_id': 23,
               'download_qiime_id': 24,
               'other_filepaths': ['1_prep_1_19700101-000000.txt',
                                   '1_prep_1_19700101-000000.txt'],
               'num_samples': 27,
               'num_columns': 22,
               'investigation_type': 'Metagenomics',
               'ontology': {
                   'ENA': ['Cancer Genomics', 'Epigenetics',
                           'Exome Sequencing', 'Forensic or Paleo-genomics',
                           'Gene Regulation Study', 'Metagenomics',
                           'Pooled Clone Sequencing', 'Population Genomics',
                           'RNASeq', 'Resequencing', 'Synthetic Genomics',
                           'Transcriptome Analysis', 'Whole Genome Sequencing',
                           'Other'],
                   'User': []},
               'artifact_attached': True,
               'study_id': 1,
               'editable': True,
               'data_type': '18S',
               'alert_type': '',
               'is_submitted_to_ebi': True,
               'alert_message': ''}
        self.assertEqual(obs, exp)

        obs = prep_template_ajax_get_req('admin@foo.bar', 1)
        self.assertEqual(obs, exp)

        obs = prep_template_ajax_get_req('demo@microbio.me', 1)
        exp['editable'] = False
        self.assertEqual(obs, exp)

    def test_check_prep_template_exists(self):
        obs = _check_prep_template_exists(1)
        self.assertEqual(obs, {'status': 'success', 'message': ''})

    def test_check_prep_template_exists_no_template(self):
        obs = _check_prep_template_exists(3100)
        self.assertEqual(obs, {'status': 'error',
                               'message': 'Prep template 3100 does not exist'})

    def test_prep_template_get_req(self):
        obs = prep_template_get_req(1, 'test@foo.bar')
        self.assertItemsEqual(obs.keys(), ['status', 'message', 'template'])
        self.assertEqual(obs['status'], 'success')
        self.assertEqual(obs['message'], '')
        self.assertEqual(obs['template'].keys(), [
            '1.SKB2.640194', '1.SKM4.640180', '1.SKB3.640195', '1.SKB6.640176',
            '1.SKD6.640190', '1.SKM6.640187', '1.SKD9.640182', '1.SKM8.640201',
            '1.SKM2.640199', '1.SKD2.640178', '1.SKB7.640196', '1.SKD4.640185',
            '1.SKB8.640193', '1.SKM3.640197', '1.SKD5.640186', '1.SKB1.640202',
            '1.SKM1.640183', '1.SKD1.640179', '1.SKD3.640198', '1.SKB5.640181',
            '1.SKB4.640189', '1.SKB9.640200', '1.SKM9.640192', '1.SKD8.640184',
            '1.SKM5.640177', '1.SKM7.640188', '1.SKD7.640191'])
        self.assertEqual(obs['template']['1.SKD7.640191'], {
            'experiment_center': 'ANL',
            'center_name': 'ANL',
            'run_center': 'ANL',
            'run_prefix': 's_G1_L001_sequences',
            'primer': 'GTGCCAGCMGCCGCGGTAA',
            'target_gene': '16S rRNA',
            'sequencing_meth': 'Sequencing by synthesis',
            'run_date': '8/1/12',
            'platform': 'Illumina',
            'pcr_primers': 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT',
            'library_construction_protocol':
                'This analysis was done as in Caporaso et al 2011 Genome '
                'research. The PCR primers (F515/R806) were developed against '
                'the V4 region of the 16S rRNA (both bacteria and archaea), '
                'which we determined would yield optimal community clustering '
                'with reads of this length using a procedure similar to that '
                'of ref. 15. [For reference, this primer pair amplifies the '
                'region 533_786 in the Escherichia coli strain 83972 sequence '
                '(greengenes accession no. prokMSA_id:470367).] The reverse '
                'PCR primer is barcoded with a 12-base error-correcting Golay '
                'code to facilitate multiplexing of up to 1,500 samples per '
                'lane, and both PCR primers contain sequencer adapter '
                'regions.',
                'experiment_design_description':
                    'micro biome of soil and rhizosphere of cannabis plants '
                    'from CA',
            'study_center': 'CCME',
            'center_project_name': None,
            'sample_center': 'ANL',
            'samp_size': '.25,g',
            'barcode': 'ACGCACATACAA',
            'qiita_prep_id': '1',
            'emp_status': 'EMP',
            'illumina_technology': 'MiSeq',
            'experiment_title': 'Cannabis Soil Microbiome',
            'target_subfragment': 'V4',
            'instrument_model': 'Illumina MiSeq'})

    def test_prep_template_get_req_no_access(self):
        obs = prep_template_get_req(1, 'demo@microbio.me')
        exp = {'status': 'error',
               'message': 'User does not have access to study'}
        self.assertEqual(obs, exp)

    def test_prep_template_get_req_no_exists(self):
        obs = prep_template_get_req(3100, 'test@foo.bar')
        self.assertEqual(obs, {'status': 'error',
                               'message': 'Prep template 3100 does not exist'})

    def test_prep_template_filepaths_get_req(self):
        obs = prep_template_filepaths_get_req(1, 'test@foo.bar')
        # have to check each key individually as the filepaths will change
        self.assertEqual(obs['status'], 'success')
        self.assertEqual(obs['message'], '')
        # [0] the fp_id is the first element, that should change
        fp_ids = [fp[0] for fp in obs['filepaths']]
        self.assertItemsEqual(fp_ids, [18, 19, 20, 21, 23, 24])

    def test_prep_template_filepaths_get_req_no_access(self):
        obs = prep_template_filepaths_get_req(1, 'demo@microbio.me')
        exp = {'status': 'error',
               'message': 'User does not have access to study'}
        self.assertEqual(obs, exp)

    def test_prep_template_graph_get_req_no_access(self):
        obs = prep_template_graph_get_req(1, 'demo@microbio.me')
        exp = {'status': 'error',
               'message': 'User does not have access to study'}
        self.assertEqual(obs, exp)

    def test_prep_template_graph_get_req_no_exists(self):
        obs = prep_template_graph_get_req(3100, 'test@foo.bar')
        self.assertEqual(obs, {'status': 'error',
                               'message': 'Prep template 3100 does not exist'})

    def test_prep_template_summary_get_req(self):
        obs = prep_template_summary_get_req(1, 'test@foo.bar')
        exp = {
            'status': 'success', 'message': '',
            'summary': [('barcode', [
                ('AACTCCTGTGGA', 1), ('ACCTCAGTCAAG', 1), ('ACGCACATACAA', 1),
                ('AGCAGGCACGAA', 1), ('AGCGCTCACATC', 1), ('ATATCGCGATGA', 1),
                ('ATGGCCTGACTA', 1), ('CATACACGCACC', 1), ('CCACCCAGTAAC', 1),
                ('CCGATGCCTTGA', 1), ('CCTCGATGCAGT', 1), ('CCTCTGAGAGCT', 1),
                ('CGAGGTTCTGAT', 1), ('CGCCGGTAATCT', 1), ('CGGCCTAAGTTC', 1),
                ('CGTAGAGCTCTC', 1), ('CGTGCACAATTG', 1), ('GATAGCACTCGT', 1),
                ('GCGGACTATTCA', 1), ('GTCCGCAAGTTA', 1), ('TAATGGTCGTAG', 1),
                ('TAGCGCGAACTT', 1), ('TCGACCAAACAC', 1), ('TGAGTGGTCTGT', 1),
                ('TGCTACAGACGT', 1), ('TGGTTATGGCAC', 1), ('TTGCACCGTCGA', 1)
            ]), ('center_name', [('ANL', 27)]), ('center_project_name', []),
                ('emp_status', [('EMP', 27)]),
                ('experiment_center', [('ANL', 27)]),
                ('experiment_design_description', [
                    ('micro biome of soil and rhizosphere of cannabis plants '
                     'from CA', 27)]),
                ('experiment_title', [('Cannabis Soil Microbiome', 27)]),
                ('illumina_technology', [('MiSeq', 27)]),
                ('instrument_model', [('Illumina MiSeq', 27)]),
                ('library_construction_protocol', [
                    ('This analysis was done as in Caporaso et al 2011 Genome '
                     'research. The PCR primers (F515/R806) were developed '
                     'against the V4 region of the 16S rRNA (both bacteria '
                     'and archaea), which we determined would yield optimal '
                     'community clustering with reads of this length using a '
                     'procedure similar to that of ref. 15. [For reference, '
                     'this primer pair amplifies the region 533_786 in the '
                     'Escherichia coli strain 83972 sequence (greengenes '
                     'accession no. prokMSA_id:470367).] The reverse PCR '
                     'primer is barcoded with a 12-base error-correcting '
                     'Golay code to facilitate multiplexing of up to 1,500 '
                     'samples per lane, and both PCR primers contain '
                     'sequencer adapter regions.', 27)]),
                ('pcr_primers', [(
                    'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 27)]),
                ('platform', [('Illumina', 27)]),
                ('primer', [('GTGCCAGCMGCCGCGGTAA', 27)]),
                ('qiita_prep_id', [('1', 27)]), ('run_center', [('ANL', 27)]),
                ('run_date', [('8/1/12', 27)]),
                ('run_prefix', [('s_G1_L001_sequences', 27)]),
                ('samp_size', [('.25,g', 27)]),
                ('sample_center', [('ANL', 27)]),
                ('sequencing_meth', [('Sequencing by synthesis', 27)]),
                ('study_center', [('CCME', 27)]),
                ('target_gene', [('16S rRNA', 27)]),
                ('target_subfragment', [('V4', 27)])],
            'editable': True, 'num_samples': 27}
        self.assertEqual(obs, exp)

    def test_prep_template_summary_get_req_no_access(self):
        obs = prep_template_summary_get_req(1, 'demo@microbio.me')
        exp = {'status': 'error',
               'message': 'User does not have access to study'}
        self.assertEqual(obs, exp)

    def test_prep_template_summary_get_req_no_exists(self):
        obs = prep_template_summary_get_req(3100, 'test@foo.bar')
        self.assertEqual(obs, {'status': 'error',
                               'message': 'Prep template 3100 does not exist'})


@qiita_test_checker()
class TestPrepAPI(TestCase):
    def setUp(self):
        # Create test file to point update tests at
        self.update_fp = join(get_mountpoint("uploads")[0][1], '1',
                              'update.txt')
        with open(self.update_fp, 'w') as f:
            f.write("""sample_name\tnew_col\n1.SKD6.640190\tnew_value\n""")

    def tearDown(self):
        if exists(self.update_fp):
            remove(self.update_fp)

        fp = join(get_mountpoint("uploads")[0][1], '1', 'uploaded_file.txt')
        if not exists(fp):
            with open(fp, 'w') as f:
                f.write('')

        r_client.flushdb()

    def _wait_for_parallel_job(self, key):
        # This is needed so the clean up works - this is a distributed system
        # so we need to make sure that all processes are done before we reset
        # the test database
        obs = r_client.get(key)
        wait_for_processing_job(loads(obs)['job_id'])

    def test_prep_template_graph_get_req(self):
        obs = prep_template_graph_get_req(1, 'test@foo.bar')

        # jobs are randomly generated then testing composition
        self.assertEqual(obs['message'], '')
        self.assertEqual(obs['status'], 'success')
        self.assertEqual(11, len(obs['nodes']))
        self.assertIn(
            ('artifact', 'FASTQ', 1, 'Raw data 1\n(FASTQ)', 'artifact'),
            obs['nodes'])
        self.assertIn(
            ('artifact', 'Demultiplexed', 2,
             'Demultiplexed 1\n(Demultiplexed)', 'artifact'),
            obs['nodes'])
        self.assertIn(
            ('artifact', 'Demultiplexed', 3,
             'Demultiplexed 2\n(Demultiplexed)', 'artifact'),
            obs['nodes'])
        self.assertIn(('artifact', 'BIOM', 4, 'BIOM\n(BIOM)', 'artifact'),
                      obs['nodes'])
        self.assertIn(('artifact', 'BIOM', 5, 'BIOM\n(BIOM)', 'artifact'),
                      obs['nodes'])
        self.assertIn(('artifact', 'BIOM', 6, 'BIOM\n(BIOM)', 'artifact'),
                      obs['nodes'])
        self.assertEqual(3, len([n for dt, _, _, n, _ in obs['nodes']
                                 if n == 'Pick closed-reference OTUs' and
                                 dt == 'job']))
        self.assertEqual(2, len([n for dt, _, _, n, _ in obs['nodes']
                                 if n == 'Split libraries FASTQ' and
                                 dt == 'job']))

        self.assertEqual(10, len(obs['edges']))
        self.assertEqual(2, len([x for x, y in obs['edges'] if x == 1]))
        self.assertEqual(3, len([x for x, y in obs['edges'] if x == 2]))
        self.assertEqual(1, len([x for x, y in obs['edges'] if y == 2]))
        self.assertEqual(1, len([x for x, y in obs['edges'] if y == 3]))
        self.assertEqual(1, len([x for x, y in obs['edges'] if y == 4]))
        self.assertEqual(1, len([x for x, y in obs['edges'] if y == 5]))
        self.assertEqual(1, len([x for x, y in obs['edges'] if y == 6]))

        self.assertIsNone(obs['workflow'])

        Artifact(4).visibility = "public"
        obs = prep_template_graph_get_req(1, 'demo@microbio.me')
        self.assertEqual(obs['message'], '')
        self.assertEqual(obs['status'], 'success')
        self.assertEqual(11, len(obs['nodes']))
        self.assertIn(
            ('artifact', 'FASTQ', 1, 'Raw data 1\n(FASTQ)', 'artifact'),
            obs['nodes'])
        self.assertIn(
            ('artifact', 'Demultiplexed', 2,
             'Demultiplexed 1\n(Demultiplexed)', 'artifact'),
            obs['nodes'])
        self.assertIn(('artifact', 'BIOM', 4, 'BIOM\n(BIOM)', 'artifact'),
                      obs['nodes'])
        self.assertEqual(3, len([n for dt, _, _, n, _ in obs['nodes']
                                 if n == 'Pick closed-reference OTUs' and
                                 dt == 'job']))
        self.assertEqual(2, len([n for dt, _, _, n, _ in obs['nodes']
                                 if n == 'Split libraries FASTQ' and
                                 dt == 'job']))

        self.assertEqual(10, len(obs['edges']))
        self.assertEqual(2, len([x for x, y in obs['edges'] if x == 1]))
        self.assertEqual(3, len([x for x, y in obs['edges'] if x == 2]))
        self.assertEqual(1, len([x for x, y in obs['edges'] if y == 2]))
        self.assertEqual(1, len([x for x, y in obs['edges'] if y == 3]))
        self.assertEqual(1, len([x for x, y in obs['edges'] if y == 4]))
        self.assertEqual(1, len([x for x, y in obs['edges'] if y == 5]))
        self.assertEqual(1, len([x for x, y in obs['edges'] if y == 6]))

        self.assertIsNone(obs['workflow'])

        # Reset visibility of the artifacts
        for i in range(4, 0, -1):
            Artifact(i).visibility = "private"

    def test_prep_template_jobs_get_req(self):
        # Create a new template:
        metadata = pd.DataFrame.from_dict(
            {'SKD6.640190': {'center_name': 'ANL',
                             'target_subfragment': 'V4',
                             'center_project_name': 'Test Project',
                             'ebi_submission_accession': None,
                             'EMP_status': 'EMP',
                             'str_column': 'Value for sample 1',
                             'primer': 'GTGCCAGCMGCCGCGGTAA',
                             'barcode': 'GTCCGCAAGTTA',
                             'run_prefix': "s_G1_L001_sequences",
                             'platform': 'ILLUMINA',
                             'instrument_model': 'Illumina MiSeq',
                             'library_construction_protocol': 'AAAA',
                             'experiment_design_description': 'BBBB'}},
            orient='index', dtype=str)
        pt = PrepTemplate.create(metadata, Study(1), '16S')

        # Check that it returns an empty dictionary when there are no jobs
        # attached to the prep template
        self.assertEqual(prep_template_jobs_get_req(pt.id, 'test@foo.bar'), {})

        # Create a job on the template
        prep_template_patch_req(
            'test@foo.bar', 'remove',
            '/%s/10/columns/target_subfragment/' % pt.id)
        # To ensure a deterministic result, wait until the job is completed
        self._wait_for_parallel_job('prep_template_%s' % pt.id)
        obs = prep_template_jobs_get_req(pt.id, 'test@foo.bar')
        self.assertEqual(len(obs), 1)
        self.assertEqual(obs.values(),
                         [{'error': '', 'status': 'success', 'step': None}])

        obs = prep_template_jobs_get_req(pt.id, 'demo@microbio.me')
        exp = {'status': 'error',
               'message': 'User does not have access to study'}
        self.assertEqual(obs, exp)

    def test_process_investigation_type(self):
        obs = _process_investigation_type('Metagenomics', '', '')
        self.assertEqual(obs, 'Metagenomics')

    def test_process_investigation_type_user_term(self):
        _process_investigation_type('Other', 'New Type', 'userterm')
        obs = _process_investigation_type('Other', 'userterm', '')
        self.assertEqual(obs, 'userterm')

    def test_process_investigation_type_new_term(self):
        randstr = ''.join([choice(ascii_letters) for x in range(30)])
        obs = _process_investigation_type('Other', 'New Type', randstr)
        self.assertEqual(obs, randstr)

        # Make sure New Type added
        ontology = Ontology(999999999)
        self.assertIn(randstr, ontology.user_defined_terms)

    def test_prep_template_post_req(self):
        obs = prep_template_post_req(1, 'test@foo.bar', 'update.txt',
                                     '16S', name="  ")
        exp = {'status': 'warning',
               'message': [
                    ('Some columns required to generate a QIIME-compliant '
                     'mapping file are not present in the template. A '
                     'placeholder value (XXQIITAXX) has been used to populate '
                     'these columns. Missing columns: BarcodeSequence, '
                     'LinkerPrimerSequence'),
                    ('Some functionality will be disabled due to missing '
                     'columns:'),
                    ('\tDemultiplexing with multiple input files disabled.: '
                     'barcode, primer, run_prefix;'),
                    '\tDemultiplexing disabled.: barcode;',
                    ('\tEBI submission disabled: center_name, '
                     'experiment_design_description, instrument_model, '
                     'library_construction_protocol, platform.'),
                    ('See the Templates tutorial for a description of these '
                     'fields.')],
               'file': 'update.txt',
               'id': 'ignored in test'}

        self.assertItemsEqual(obs['message'].split('\n'), exp['message'])
        self.assertEqual(obs['status'], exp['status'])
        self.assertEqual(obs['file'], exp['file'])
        self.assertIsInstance(obs['id'], int)

        # Make sure new prep template added
        prep = PrepTemplate(obs['id'])
        self.assertEqual(prep.data_type(), '16S')
        self.assertEqual([x for x in prep.keys()], ['1.SKD6.640190'])
        self.assertEqual([x._to_dict() for x in prep.values()],
                         [{'new_col': 'new_value'}])
        self.assertEqual(prep.name, "Prep information %s" % prep.id)

    def test_prep_template_post_req_errors(self):
        # User doesn't have access
        obs = prep_template_post_req(1, 'demo@microbio.me', 'filepath', '16S')
        exp = {'status': 'error',
               'message': 'User does not have access to study'}
        self.assertEqual(obs, exp)

        # The file does not exist
        obs = prep_template_post_req(1, 'test@foo.bar', 'badfilepath', '16S')
        exp = {'status': 'error',
               'message': 'file does not exist',
               'file': 'badfilepath'}
        self.assertEqual(obs, exp)

        # Prep template does not exist
        obs = prep_template_post_req(3100, 'test@foo.bar', 'update.txt',
                                     '16S')
        self.assertEqual(obs, {'status': 'error',
                               'message': 'Study does not exist'})

    def test_prep_template_patch_req(self):
        metadata = pd.DataFrame.from_dict(
            {'SKD6.640190': {'center_name': 'ANL',
                             'target_subfragment': 'V4',
                             'center_project_name': 'Test Project',
                             'ebi_submission_accession': None,
                             'EMP_status': 'EMP',
                             'str_column': 'Value for sample 1',
                             'primer': 'GTGCCAGCMGCCGCGGTAA',
                             'barcode': 'GTCCGCAAGTTA',
                             'run_prefix': "s_G1_L001_sequences",
                             'platform': 'ILLUMINA',
                             'instrument_model': 'Illumina MiSeq',
                             'library_construction_protocol': 'AAAA',
                             'experiment_design_description': 'BBBB'}},
            orient='index', dtype=str)
        pt = PrepTemplate.create(metadata, Study(1), '16S')
        # Update investigation type
        obs = prep_template_patch_req(
            'test@foo.bar', 'replace', '/%s/investigation_type' % pt.id,
            'Cancer Genomics')
        exp = {'status': 'success', 'message': ''}
        self.assertEqual(obs, exp)
        self.assertEqual(pt.investigation_type, 'Cancer Genomics')
        # Update prep template data
        obs = prep_template_patch_req(
            'test@foo.bar', 'replace', '/%s/data' % pt.id, 'update.txt')
        self.assertEqual(obs, exp)
        obs = r_client.get('prep_template_%s' % pt.id)
        self.assertIsNotNone(obs)

        self._wait_for_parallel_job('prep_template_%s' % pt.id)

        # Delete a prep template column
        obs = prep_template_patch_req(
            'test@foo.bar', 'remove',
            '/%s/10/columns/target_subfragment/' % pt.id)
        exp = {'status': 'success', 'message': '', 'row_id': '10'}
        self.assertEqual(obs, exp)
        self._wait_for_parallel_job('prep_template_%s' % pt.id)
        self.assertNotIn('target_subfragment', pt.categories())

        # Change the name of the prep template
        obs = prep_template_patch_req(
            'test@foo.bar', 'replace', '/%s/name' % pt.id, ' My New Name ')
        exp = {'status': 'success', 'message': ''}
        self.assertEqual(obs, exp)
        self.assertEqual(pt.name, 'My New Name')

        # Test all the errors
        # Operation not supported
        obs = prep_template_patch_req(
            'test@foo.bar', 'add', '/1/investigation_type',
            'Cancer Genomics')
        exp = {'status': 'error',
               'message': 'Operation "add" not supported. '
                          'Current supported operations: replace, remove',
               'row_id': '0'}
        self.assertEqual(obs, exp)
        # Incorrect path parameter
        obs = prep_template_patch_req(
            'test@foo.bar', 'replace', '/investigation_type',
            'Cancer Genomics')
        exp = {'status': 'error',
               'message': 'Incorrect path parameter'}
        self.assertEqual(obs, exp)
        # Incorrect attribute
        obs = prep_template_patch_req(
            'test@foo.bar', 'replace', '/1/other_attribute',
            'Cancer Genomics')
        exp = {'status': 'error',
               'message': 'Attribute "other_attribute" not found. '
                          'Please, check the path parameter'}
        self.assertEqual(obs, exp)
        # User doesn't have access
        obs = prep_template_patch_req(
            'demo@microbio.me', 'replace', '/%s/investigation_type' % pt.id,
            'Cancer Genomics')
        exp = {'status': 'error',
               'message': 'User does not have access to study'}
        self.assertEqual(obs, exp)
        # File does not exists
        obs = prep_template_patch_req(
            'test@foo.bar', 'replace', '/1/data', 'unknown_file.txt')
        exp = {'status': 'error',
               'message': 'file does not exist',
               'file': 'unknown_file.txt'}
        self.assertEqual(obs, exp)

    def test_prep_template_delete_req(self):
        template = pd.read_csv(self.update_fp, sep='\t', index_col=0)
        new_id = get_count('qiita.prep_template') + 1
        npt.assert_warns(QiitaDBWarning, PrepTemplate.create,
                         template, Study(1), '16S')
        obs = prep_template_delete_req(new_id, 'test@foo.bar')
        exp = {'status': 'success',
               'message': ''}
        self.assertEqual(obs, exp)

    def test_prep_template_delete_req_attached_artifact(self):
        obs = prep_template_delete_req(1, 'test@foo.bar')
        exp = {'status': 'error',
               'message': "Cannot remove prep template 1 because it has an "
                          "artifact associated with it"}
        self.assertEqual(obs, exp)

    def test_prep_template_delete_req_no_access(self):
        obs = prep_template_delete_req(1, 'demo@microbio.me')
        exp = {'status': 'error',
               'message': 'User does not have access to study'}
        self.assertEqual(obs, exp)

    def test_prep_template_delete_req_no_prep(self):
        obs = prep_template_delete_req(3100, 'test@foo.bar')
        exp = {'status': 'error',
               'message': 'Prep template 3100 does not exist'}
        self.assertEqual(obs, exp)


if __name__ == '__main__':
    main()
