from unittest import TestCase, main
from os.path import join, exists

from qiita_core.util import qiita_test_checker
from qiita_core.qiita_settings import qiita_config
from qiita_pet.handlers.api_proxy.prep_template import (
    prep_template_summary_get_req, prep_template_post_req,
    prep_template_put_req, prep_template_delete_req, prep_template_get_req,
    prep_template_graph_get_req, prep_template_filepaths_get_req)


@qiita_test_checker()
class TestPrepAPI(TestCase):
    def setUp(self):
        fp = join(qiita_config.base_data_dir, 'uploads/1', 'uploaded_file.txt')
        if not exists(fp):
            with open(fp, 'w') as f:
                f.write('')

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
        obs = prep_template_post_req(1, 'demo@microbio.me', '16S',
                                     'filepath')
        exp = {'status': 'error',
               'message': 'User does not have access to study'}
        self.assertEqual(obs, exp)

    def test_prep_template_put_req(self):
        obs = prep_template_put_req(1, 'test@foo.bar',
                                    'uploaded_file.txt')
        exp = {'status': 'error',
               'message': 'Empty file passed!',
               'file': 'uploaded_file.txt'}
        self.assertEqual(obs, exp)

    def test_prep_template_put_req_no_access(self):
        obs = prep_template_put_req(1, 'demo@microbio.me', 'filepath')
        exp = {'status': 'error',
               'message': 'User does not have access to study'}
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
        exp = [(15, join(qiita_config.base_data_dir,
                         'templates/1_prep_1_19700101-000000.txt')),
               (16, join(qiita_config.base_data_dir,
                         'templates/1_prep_1_qiime_19700101-000000.txt'))]
        self.assertItemsEqual(obs, exp)

    def test_prep_template_filepaths_get_req_no_access(self):
        obs = prep_template_filepaths_get_req(1, 'demo@microbio.me')
        exp = {'status': 'error',
               'message': 'User does not have access to study'}
        self.assertEqual(obs, exp)

    def test_prep_template_graph_get_req(self):
        obs = prep_template_graph_get_req(1, 'test@foo.bar')
        exp = {'edge_list': [(1, 3), (1, 2), (2, 4)],
               'node_labels': [(1, 'Artifact Name for 1 - FASTQ'),
                               (2, 'Artifact Name for 2 - Demultiplexed'),
                               (3, 'Artifact Name for 3 - Demultiplexed'),
                               (4, 'Artifact Name for 4 - BIOM')]}

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
            'num_samples': 27}
        self.assertEqual(obs, exp)

    def test_prep_template_summary_get_req_no_access(self):
        obs = prep_template_summary_get_req(1, 'demo@microbio.me')
        exp = {'status': 'error',
               'message': 'User does not have access to study'}
        self.assertEqual(obs, exp)

if __name__ == '__main__':
    main()
