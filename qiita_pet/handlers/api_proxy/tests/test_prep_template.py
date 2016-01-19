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

from qiita_core.qiita_settings import qiita_config
from qiita_core.util import qiita_test_checker
from qiita_db.ontology import Ontology
from qiita_pet.handlers.api_proxy.prep_template import (
    prep_template_summary_get_req, prep_template_post_req,
    prep_template_put_req, prep_template_delete_req, prep_template_get_req,
    prep_template_graph_get_req, prep_template_filepaths_get_req,
    prep_ontology_get_req, _process_investigation_type)


@qiita_test_checker()
class TestPrepAPI(TestCase):
    def setUp(self):
        fp = join(qiita_config.base_data_dir, 'uploads', '1',
                  'uploaded_file.txt')
        if not exists(fp):
            with open(fp, 'w') as f:
                f.write('')

        # Create test file to point update tests at
        self.update_fp = join(qiita_config.base_data_dir, 'uploads', '1',
                              'update.txt')
        with open(self.update_fp, 'w') as f:
            f.write("""sample_name\tnew_col\n1.SKD6.640190\tnew_value\n""")

        def tear_down(self):
            remove(self.update_fp)

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

    def test_prep_ontology_get_req(self):
        obs = prep_ontology_get_req()
        exp = {'ENA': ['Cancer Genomics', 'Epigenetics', 'Exome Sequencing',
                       'Forensic or Paleo-genomics', 'Gene Regulation Study',
                       'Metagenomics', 'Pooled Clone Sequencing',
                       'Population Genomics', 'RNASeq', 'Resequencing',
                       'Synthetic Genomics', 'Transcriptome Analysis',
                       'Whole Genome Sequencing', 'Other'],
               'User': [],
               'status': 'success',
               'message': ''}
        self.assertEqual(obs, exp)

    def test_prep_template_get_req(self):
        obs = prep_template_get_req(1, 'test@foo.bar')
        self.assertItemsEqual(obs.keys(), ['status', 'message', 'template'])
        self.assertEqual(obs['status'], 'success')
        self.assertEqual(obs['message'], '')
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

    def test_prep_template_post_req(self):
        obs = prep_template_post_req(1, 'test@foo.bar', 'uploaded_file.txt',
                                     '16S')
        exp = {'status': 'error',
               'message': 'Empty file passed!',
               'file': 'uploaded_file.txt'}
        self.assertEqual(obs, exp)

    def test_prep_template_post_req_no_access(self):
        obs = prep_template_post_req(1, 'demo@microbio.me', 'filepath', '16S')
        exp = {'status': 'error',
               'message': 'User does not have access to study'}
        self.assertEqual(obs, exp)

    def test_prep_template_post_req_bad_filepath(self):
        obs = prep_template_post_req(1, 'test@foo.bar', 'badfilepath', '16S')
        exp = {'status': 'error',
               'message': 'file does not exist',
               'file': 'badfilepath'}
        self.assertEqual(obs, exp)

    def test_prep_template_put_req(self):
        obs = prep_template_put_req(1, 'test@foo.bar',
                                    'uploaded_file.txt')
        exp = {'status': 'error',
               'message': 'Empty file passed!',
               'file': 'uploaded_file.txt'}
        self.assertEqual(obs, exp)

    def test_prep_template_put_req_warning(self):
        obs = prep_template_put_req(1, 'test@foo.bar', 'update.txt')
        exp = {'status': 'warning',
               'message': 'Sample names were already prefixed with the study '
                          'id.\nThe following columns have been added to the '
                          'existing template: new_col\nThere are no '
                          'differences between the data stored in the DB and '
                          'the new data provided',
               'file': 'update.txt'}
        self.assertEqual(obs, exp)

    def test_prep_put_req_inv_type(self):
        randstr = ''.join([choice(ascii_letters) for x in range(30)])
        obs = prep_template_put_req(1, 'test@foo.bar',
                                    investigation_type='Other',
                                    user_defined_investigation_type='New Type',
                                    new_investigation_type=randstr)
        exp = {'status': 'success',
               'message': '',
               'file': None}
        self.assertEqual(obs, exp)

        # Make sure New Type added
        ontology = Ontology(999999999)
        self.assertIn(randstr, ontology.user_defined_terms)

    def test_prep_template_put_req_no_access(self):
        obs = prep_template_put_req(1, 'demo@microbio.me', 'filepath')
        exp = {'status': 'error',
               'message': 'User does not have access to study'}
        self.assertEqual(obs, exp)

    def test_prep_template_put_req_bad_filepath(self):
        obs = prep_template_put_req(1, 'test@foo.bar', 'badfilepath')
        exp = {'status': 'error',
               'message': 'file does not exist',
               'file': 'badfilepath'}
        self.assertEqual(obs, exp)

    def test_prep_template_delete_req(self):
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

    def test_prep_template_filepaths_get_req(self):
        obs = prep_template_filepaths_get_req(1, 'test@foo.bar')
        exp = {'status': 'success',
               'message': '',
               'filepaths': [
                   (15, join(qiita_config.base_data_dir,
                             'templates/1_prep_1_19700101-000000.txt')),
                   (16, join(qiita_config.base_data_dir,
                             'templates/1_prep_1_qiime_19700101-000000.txt'))]}
        self.assertItemsEqual(obs, exp)

    def test_prep_template_filepaths_get_req_no_access(self):
        obs = prep_template_filepaths_get_req(1, 'demo@microbio.me')
        exp = {'status': 'error',
               'message': 'User does not have access to study'}
        self.assertEqual(obs, exp)

    def test_prep_template_graph_get_req(self):
        obs = prep_template_graph_get_req(1, 'test@foo.bar')
        exp = {'edge_list': [(1, 3), (1, 2), (2, 4)],
               'node_labels': [(1, 'Raw data 1 - FASTQ'),
                               (2, 'Demultiplexed 1 - Demultiplexed'),
                               (3, 'Demultiplexed 2 - Demultiplexed'),
                               (4, 'BIOM - BIOM')],
               'status': 'success',
               'message': ''}

        self.assertItemsEqual(obs.keys(), exp.keys())
        self.assertItemsEqual(obs['edge_list'], exp['edge_list'])
        self.assertItemsEqual(obs['node_labels'], exp['node_labels'])

    def test_prep_template_graph_get_req_no_access(self):
        obs = prep_template_graph_get_req(1, 'demo@microbio.me')
        exp = {'status': 'error',
               'message': 'User does not have access to study'}
        self.assertEqual(obs, exp)

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

if __name__ == '__main__':
    main()
