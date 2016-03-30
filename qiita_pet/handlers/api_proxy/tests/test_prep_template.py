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
from time import sleep
from json import loads

import pandas as pd
import numpy.testing as npt
from moi import r_client

from qiita_core.util import qiita_test_checker
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
    prep_template_ajax_get_req, _get_ENA_ontology)


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
                           'Proteomic'],
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
               'download_prep': 18,
               'download_qiime': 19,
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
        exp = {'status': 'success',
               'message': '',
               'filepaths': [
                   (19, join(get_mountpoint('templates')[0][1],
                             '1_prep_1_qiime_19700101-000000.txt')),
                   (18, join(get_mountpoint('templates')[0][1],
                             '1_prep_1_19700101-000000.txt'))]}
        self.assertEqual(obs, exp)

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
        exp = {'summary': {
            'experiment_center': [('ANL', 27)],
            'center_name': [('ANL', 27)],
            'run_center': [('ANL', 27)],
            'run_prefix': [('s_G1_L001_sequences', 27)],
            'primer': [('GTGCCAGCMGCCGCGGTAA', 27)],
            'target_gene': [('16S rRNA', 27)],
            'sequencing_meth': [('Sequencing by synthesis', 27)],
            'run_date': [('8/1/12', 27)],
            'platform': [('Illumina', 27)],
            'pcr_primers': [('FWD:GTGCCAGCMGCCGCGGTAA; '
                             'REV:GGACTACHVGGGTWTCTAAT', 27)],
            'library_construction_protocol': [(
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
                'regions.', 27)],
            'experiment_design_description': [(
                'micro biome of soil and rhizosphere of cannabis plants from '
                'CA', 27)],
            'study_center': [('CCME', 27)],
            'center_project_name': [],
            'sample_center': [('ANL', 27)],
            'samp_size': [('.25,g', 27)],
            'barcode': [
                ('AACTCCTGTGGA', 1), ('ACCTCAGTCAAG', 1), ('ACGCACATACAA', 1),
                ('AGCAGGCACGAA', 1), ('AGCGCTCACATC', 1), ('ATATCGCGATGA', 1),
                ('ATGGCCTGACTA', 1), ('CATACACGCACC', 1), ('CCACCCAGTAAC', 1),
                ('CCGATGCCTTGA', 1), ('CCTCGATGCAGT', 1), ('CCTCTGAGAGCT', 1),
                ('CGAGGTTCTGAT', 1), ('CGCCGGTAATCT', 1), ('CGGCCTAAGTTC', 1),
                ('CGTAGAGCTCTC', 1), ('CGTGCACAATTG', 1), ('GATAGCACTCGT', 1),
                ('GCGGACTATTCA', 1), ('GTCCGCAAGTTA', 1), ('TAATGGTCGTAG', 1),
                ('TAGCGCGAACTT', 1), ('TCGACCAAACAC', 1), ('TGAGTGGTCTGT', 1),
                ('TGCTACAGACGT', 1), ('TGGTTATGGCAC', 1), ('TTGCACCGTCGA', 1)],
            'emp_status': [('EMP', 27)],
            'illumina_technology': [('MiSeq', 27)],
            'experiment_title': [('Cannabis Soil Microbiome', 27)],
            'target_subfragment': [('V4', 27)],
            'instrument_model': [('Illumina MiSeq', 27)]},
            'num_samples': 27,
            'status': 'success',
            'message': ''}
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

    def test_prep_template_graph_get_req(self):
        obs = prep_template_graph_get_req(1, 'test@foo.bar')
        exp = {'edge_list': [(1, 3), (1, 2), (2, 4), (2, 5), (2, 6)],
               'node_labels': [(1, 'Raw data 1 - FASTQ'),
                               (2, 'Demultiplexed 1 - Demultiplexed'),
                               (3, 'Demultiplexed 2 - Demultiplexed'),
                               (4, 'BIOM - BIOM'),
                               (5, 'BIOM - BIOM'),
                               (6, 'BIOM - BIOM')],
               'status': 'success',
               'message': ''}
        self.assertItemsEqual(obs['edge_list'], exp['edge_list'])
        self.assertItemsEqual(obs['node_labels'], exp['node_labels'])
        self.assertEqual(obs['status'], exp['status'])
        self.assertEqual(obs['message'], exp['message'])

        Artifact(4).visibility = "public"
        obs = prep_template_graph_get_req(1, 'demo@microbio.me')
        exp = {'edge_list': [(1, 2), (2, 4)],
               'node_labels': [(1, 'Raw data 1 - FASTQ'),
                               (2, 'Demultiplexed 1 - Demultiplexed'),
                               (4, 'BIOM - BIOM')],
               'status': 'success',
               'message': ''}
        self.assertItemsEqual(obs['edge_list'], exp['edge_list'])
        self.assertItemsEqual(obs['node_labels'], exp['node_labels'])
        self.assertEqual(obs['status'], exp['status'])
        self.assertEqual(obs['message'], exp['message'])

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
        new_id = get_count('qiita.prep_template') + 1
        obs = prep_template_post_req(1, 'test@foo.bar', 'update.txt',
                                     '16S')
        exp = {'status': 'warning',
               'message': 'Sample names were already prefixed with the study '
                          'id.\nSome functionality will be disabled due to '
                          'missing columns:\n\tDemultiplexing with multiple '
                          'input files disabled. If your raw data includes '
                          'multiple raw input files, you will not be able to '
                          'preprocess your raw data: barcode, primer, '
                          'run_prefix;\n\tDemultiplexing disabled. You will '
                          'not be able to preprocess your raw data: barcode, '
                          'primer;\n\tEBI submission disabled: center_name, '
                          'experiment_design_description, instrument_model, '
                          'library_construction_protocol, platform, primer.'
                          '\nSee the Templates tutorial for a description of '
                          'these fields.\nSome columns required to generate a '
                          'QIIME-compliant mapping file are not present in the'
                          ' template. A placeholder value (XXQIITAXX) has been'
                          ' used to populate these columns. Missing columns: '
                          'BarcodeSequence, LinkerPrimerSequence',
               'file': 'update.txt',
               'id': new_id}
        self.assertItemsEqual(obs['message'].split('\n'),
                              exp['message'].split('\n'))
        self.assertEqual(obs['status'], exp['status'])
        self.assertEqual(obs['file'], exp['file'])
        self.assertEqual(obs['id'], exp['id'])

        # Make sure new prep template added
        prep = PrepTemplate(new_id)
        self.assertEqual(prep.data_type(), '16S')
        self.assertEqual([x for x in prep.keys()], ['1.SKD6.640190'])
        self.assertEqual([x._to_dict() for x in prep.values()],
                         [{'new_col': 'new_value'}])

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
        pt = PrepTemplate(1)
        # Update investigation type
        obs = prep_template_patch_req(
            'test@foo.bar', 'replace', '/1/investigation_type',
            'Cancer Genomics')
        exp = {'status': 'success', 'message': ''}
        self.assertEqual(obs, exp)
        self.assertEqual(pt.investigation_type, 'Cancer Genomics')
        # Update prep template data
        obs = prep_template_patch_req(
            'test@foo.bar', 'replace', '/1/data', 'update.txt')
        self.assertEqual(obs, exp)
        obs = r_client.get('prep_template_1')
        self.assertIsNotNone(obs)

        # This is needed so the clean up works - this is a distributed system
        # so we need to make sure that all processes are done before we reset
        # the test database
        redis_info = loads(r_client.get(obs))
        while redis_info['status_msg'] == 'Running':
            sleep(0.05)
            redis_info = loads(r_client.get(obs))

    def test_prep_template_patch_req_errors(self):
        # Operation not supported
        obs = prep_template_patch_req(
            'test@foo.bar', 'add', '/1/investigation_type',
            'Cancer Genomics')
        exp = {'status': 'error',
               'message': 'Operation "add" not supported. '
                          'Current supported operations: replace'}
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
            'demo@microbio.me', 'replace', '/1/investigation_type',
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
               'message': "Couldn't remove prep template: Cannot remove prep "
                          "template 1 because it has an artifact associated "
                          "with it"}
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
