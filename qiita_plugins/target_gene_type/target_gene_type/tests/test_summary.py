# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import TestCase, main
from tempfile import mkdtemp
from os import remove
from os.path import exists, isdir, join, dirname
from shutil import rmtree
from json import dumps

from qiita_client import QiitaClient
from gzip import GzipFile
import httpretty

from target_gene_type.summary import generate_html_summary


class SummaryTestsNotDemux(TestCase):
    @httpretty.activate
    def setUp(self):
        # Registewr the URIs for the QiitaClient
        httpretty.register_uri(
            httpretty.POST,
            "https://test_server.com/qiita_db/authenticate/",
            body='{"access_token": "token", "token_type": "Bearer", '
                 '"expires_in": "3600"}')

        self.qclient = QiitaClient('https://test_server.com', 'client_id',
                                   'client_secret')
        # creating files
        self.out_dir = mkdtemp()
        gz_file = join(self.out_dir, "file1.fastq.gz")
        with GzipFile(gz_file, mode='w', mtime=1) as fh:
            fh.write(READS)
        fastq_file = join(self.out_dir, "file1.fastq")
        with open(fastq_file, mode='w') as fh:
            fh.write(READS)

        self.artifact_id = 4
        self.parameters = {'input_data': self.artifact_id}

        self.httpretty_body = {
            'name': 'Artifact name',
            'timestamp': '2012-10-01 09:30:27',
            'visibility': 'private',
            'type': 'FASTQ',
            'data_type': '16S',
            'can_be_submitted_to_ebi': False,
            'ebi_run_accessions': None,
            'can_be_submitted_to_vamps': False,
            'is_submitted_to_vamps': None,
            'prep_information': [1],
            'study': 1,
            'processing_parameters': None,
            'files': {"raw_forward_seqs": [gz_file],
                      "raw_barcodes": [fastq_file]}}

        self._clean_up_files = [self.out_dir, gz_file, fastq_file]

    def tearDown(self):
        for fp in self._clean_up_files:
            if exists(fp):
                if isdir(fp):
                    rmtree(fp)
                else:
                    remove(fp)

    @httpretty.activate
    def test_generate_html_summary(self):
        httpretty_url = ("https://test_server.com/qiita_db/artifacts/%s/"
                         % self.artifact_id)
        httpretty.register_uri(
            httpretty.GET, httpretty_url, body=dumps(self.httpretty_body))
        httpretty_url = ("https://test_server.com/qiita_db/artifacts/"
                         "%s/" % self.artifact_id)
        httpretty.register_uri(httpretty.PATCH, httpretty_url)

        obs_success, obs_ainfo, obs_error = generate_html_summary(
            self.qclient, 'job-id', self.parameters, self.out_dir)

        # asserting reply
        self.assertTrue(obs_success)
        self.assertIsNone(obs_ainfo)
        self.assertEqual(obs_error, "")

        # asserting content of html
        html_fp = join(self.out_dir, "artifact_%d.html" % self.artifact_id)
        with open(html_fp) as html_f:
            html = html_f.read()
        self.assertEqual(html, "\n".join(EXP_HTML))


class SummaryTestsDemux(TestCase):
    @httpretty.activate
    def setUp(self):
        # Registewr the URIs for the QiitaClient
        httpretty.register_uri(
            httpretty.POST,
            "https://test_server.com/qiita_db/authenticate/",
            body='{"access_token": "token", "token_type": "Bearer", '
                 '"expires_in": "3600"}')

        self.qclient = QiitaClient('https://test_server.com', 'client_id',
                                   'client_secret')
        # creating files
        self.out_dir = mkdtemp()
        self.artifact_id = 4
        self.parameters = {'input_data': self.artifact_id}

        self.httpretty_body = {
            'name': 'Artifact name',
            'timestamp': '2012-10-01 09:30:27',
            'visibility': 'private',
            'type': 'Demultiplexed',
            'data_type': '16S',
            'can_be_submitted_to_ebi': True,
            'ebi_run_accessions': None,
            'can_be_submitted_to_vamps': True,
            'is_submitted_to_vamps': False,
            'prep_information': [1],
            'study': 1,
            'processing_parameters': None,
            'files': {"raw_forward_seqs": ["test_file"],
                      "preprocessed_demux": ["%s/test_data/101_seqs.demux"
                                             % dirname(__file__)]}}

        self._clean_up_files = [self.out_dir]

    def tearDown(self):
        for fp in self._clean_up_files:
            if exists(fp):
                if isdir(fp):
                    rmtree(fp)
                else:
                    remove(fp)

    @httpretty.activate
    def test_generate_html_summary(self):
        httpretty_url = ("https://test_server.com/qiita_db/artifacts/%s/"
                         % self.artifact_id)
        httpretty.register_uri(
            httpretty.GET, httpretty_url, body=dumps(self.httpretty_body))
        httpretty_url = ("https://test_server.com/qiita_db/artifacts/"
                         "%s/" % self.artifact_id)
        httpretty.register_uri(httpretty.PATCH, httpretty_url)

        obs_success, obs_ainfo, obs_error = generate_html_summary(
            self.qclient, 'job-id', self.parameters, self.out_dir)

        # asserting reply
        self.assertTrue(obs_success)
        self.assertIsNone(obs_ainfo)
        self.assertEqual(obs_error, "")

        # asserting content of html
        html_fp = join(self.out_dir, "artifact_%d.html" % self.artifact_id)
        with open(html_fp) as html_f:
            html = html_f.read()
        self.assertEqual(html, "\n".join(EXP_HTML_DEMUX))

    @httpretty.activate
    def test_generate_html_summary_no_demux(self):
        self.httpretty_body['files'] = {"fps_type": ["fps"]}
        httpretty_url = ("https://test_server.com/qiita_db/artifacts/%s/"
                         % self.artifact_id)
        httpretty.register_uri(
            httpretty.GET, httpretty_url, body=dumps(self.httpretty_body))

        with self.assertRaises(ValueError):
            generate_html_summary(self.qclient, 'job-id', self.parameters,
                                  self.out_dir)


READS = """@MISEQ03:123:000000000-A40KM:1:1101:14149:1572 1:N:0:TCCACAGGAGT
GGGGGGTGCCAGCCGCCGCGGTAATACGGGGGGGGCAAGCGTTGTTCGGAATTACTGGGCGTAAAGGGCTCGTAGGCG\
GCCCACTAAGTCAGACGTGAAATCCCTCGGCTTAACCGGGGAACTGCGTCTGATACTGGATGGCTTGAGGTTGGGAGA\
GGGATGCGGAATTCCAGGTGTAGCGGTGAAATGCGTAGATATCTGGAGGAACACCGGTGGCGAAGGCGGCATCCTGGA\
CCAATTCTGACGCTGAG
+
CCCCCCCCCFFFGGGGGGGGGGGGHHHHGGGGGFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF\
FFF-.;FFFFFFFFF9@EFFFFFFFFFFFFFFFFFFF9CFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFBFFFFFFF\
FFFFFFECFFFEFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFBFFFFFFFFFFFFFFFFF;CDEA@FFFFFFFFF\
FFFFFFFFFFFFFFFFF
@MISEQ03:123:000000000-A40KM:1:1101:14170:1596 1:N:0:TCCACAGGAGT
ATGGCGTGCCAGCAGCCGCGGTAATACGGAGGGGGCTAGCGTTGTTCGGAATTACTGGGCGTAAAGCGCACGTAGGCG\
GCTTTGTAAGTTAGAGGTGAAAGCCCGGGGCTCAACTCCGGAACTGCCTTTAAGACTGCATCGCTAGAATTGTGGAGA\
GGTGAGTGGAATTCCGAGTGTAGAGGTGAAATTCGTAGATATTCGGAAGAACACCAGTGGCGAAGGCGACTCACTGGA\
CACATATTGACGCTGAG
+
CCCCCCCCCCFFGGGGGGGGGGGGGHHHGGGGGGGGGHHHGGGGGHHGGGGGHHHHHHHHGGGGHHHGGGGGHHHGHG\
GGGGHHHHHHHHGHGHHHHHHGHHHHGGGGGGHHHHHHHGGGGGHHHHHHHHHGGFGGGGGGGGGGGGGGGGGGGGGG\
GGFGGFFFFFFFFFFFFFFFFFF0BFFFFFFFFFFFFEFFFFFFFFFFFFFFFFFFFFFFFFFFFDFAFCFFFFFFFF\
FFFFFFFFFFBDFFFFF
@MISEQ03:123:000000000-A40KM:1:1101:14740:1607 1:N:0:TCCACAGGAGT
AGTGTGTGCCAGCAGCCGCGGTAATACGTAGGGTGCGAGCGTTAATCGGAATTACTGGGCGTAAAGCGTGCGCAGGCG\
GTTCGTTGTGTCTGCTGTGAAATCCCCGGGCTCAACCTGGGAATGGCAGTGGAAACTGGCGAGCTTGAGTGTGGCAGA\
GGGGGGGGGAATTCCGCGTGTAGCAGTGAAATGCGTAGAGATGCGGAGGAACACCGATGGCGAAGGCAACCCCCTGGG\
ATAATATTTACGCTCAT
+
AABCCFFFFFFFGGGGGGGGGGGGHHHHHHHEGGFG2EEGGGGGGHHGGGGGHGHHHHHHGGGGHHHGGGGGGGGGGG\
GEGGGGHEG?GBGGFHFGFFHHGHHHGGGGCCHHHHHFCGG01GGHGHGGGEFHH/DDHFCCGCGHGAF;B0;DGF9A\
EEGGGF-=C;.FFFF/.-@B9BFB/BB/;BFBB/..9=.9//:/:@---./.BBD-@CFD/=A-::.9AFFFFFCEFF\
./FBB############
@MISEQ03:123:000000000-A40KM:1:1101:14875:1613 1:N:0:TCCACAGGAGT
GGTGGGTGCCAGCCGCCGCGGTAATACAGAGGGTGCAAGCGTTAATCGGAATTACTGGGCGTAAAGCGCGCGTAGGTG\
GTTTGTTAAGTTGGATGTGAAATCCCCGGGCTCAACCTGGGAACTGCATTCAAAACTGACAAGCTAGAGTATGGTAGA\
GGGTGGTGGAATTTCCTGTGTAGCGGTGAAATGCGTAGATATAGGAAGGAACACCAGTGGCGAAGGCGACCACCTGGA\
CTGATACTGACACTGAG
+
CCCCCCCCCFFFGGGGGGGGGGGGGHHHHHHGGGGGHHHHGGGGGHHGGGGGHHHHHHHHGGGGHHHGGGGGGGGGHH\
GGGHGHHHHHHHHHHHHHHHHHGHHHGGGGGGHHHHHHHHGGHGGHHGHHHHHHHHHFHHHHHHHHHHHHHHHGHHHG\
HHGEGGDGGFFFGGGFGGGGGGGGGGGFFFFFFFDFFFAFFFFFFFFFFFFFFFFFFFFFFFFFFDFFFFFFFEFFFF\
FFFFFB:FFFFFFFFFF
"""

EXP_HTML = [
    '<h3>file1.fastq (raw_barcodes)</h3>',
    '<b>MD5:</b>: 97328e860ef506f7b029997b12bf9885</br>',
    '<p style="font-family:\'Courier New\', Courier, monospace;font-size:10;"'
    '>@MISEQ03:123:000000000-A40KM:1:1101:14149:1572 1:N:0:TCCACAGGAGT\n<br/>'
    'GGGGGGTGCCAGCCGCCGCGGTAATACGGGGGGGGCAAGCGTTGTTCGGAATTACTGGGCGTAAAGGGCTCG'
    'TAGGCGGCCCACTAAGTCAGACGTGAAATCCCTCGGCTTAACCGGGGAACTGCGTCTGATACTGGATGGCTT'
    'GAGGTTGGGAGAGGGATGCGGAATTCCAGGTGTAGCGGTGAAATGCGTAGATATCTGGAGGAACACCGGTGG'
    'CGAAGGCGGCATCCTGGACCAATTCTGACGCTGAG\n<br/>+\n<br/>CCCCCCCCCFFFGGGGGGGGGG'
    'GGHHHHGGGGGFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF-.;FFFFFFFFF9'
    '@EFFFFFFFFFFFFFFFFFFF9CFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFBFFFFFFFFFFFFFECFF'
    'FEFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFBFFFFFFFFFFFFFFFFF;CDEA@FFFFFFFFFFFFF'
    'FFFFFFFFFFFFF\n<br/>@MISEQ03:123:000000000-A40KM:1:1101:14170:1596 1:N:0'
    ':TCCACAGGAGT\n<br/>ATGGCGTGCCAGCAGCCGCGGTAATACGGAGGGGGCTAGCGTTGTTCGGAATT'
    'ACTGGGCGTAAAGCGCACGTAGGCGGCTTTGTAAGTTAGAGGTGAAAGCCCGGGGCTCAACTCCGGAACTGC'
    'CTTTAAGACTGCATCGCTAGAATTGTGGAGAGGTGAGTGGAATTCCGAGTGTAGAGGTGAAATTCGTAGATA'
    'TTCGGAAGAACACCAGTGGCGAAGGCGACTCACTGGACACATATTGACGCTGAG\n<br/>+\n<br/>CCC'
    'CCCCCCCFFGGGGGGGGGGGGGHHHGGGGGGGGGHHHGGGGGHHGGGGGHHHHHHHHGGGGHHHGGGGGHHH'
    'GHGGGGGHHHHHHHHGHGHHHHHHGHHHHGGGGGGHHHHHHHGGGGGHHHHHHHHHGGFGGGGGGGGGGGGG'
    'GGGGGGGGGGGFGGFFFFFFFFFFFFFFFFFF0BFFFFFFFFFFFFEFFFFFFFFFFFFFFFFFFFFFFFFF'
    'FFDFAFCFFFFFFFFFFFFFFFFFFBDFFFFF\n<br/>@MISEQ03:123:000000000-A40KM:1:11'
    '01:14740:1607 1:N:0:TCCACAGGAGT\n<br/>AGTGTGTGCCAGCAGCCGCGGTAATACGTAGGGT'
    'GCGAGCGTTAATCGGAATTACTGGGCGTAAAGCGTGCGCAGGCGGTTCGTTGTGTCTGCTGTGAAATCCCCG'
    'GGCTCAACCTGGGAATGGCAGTGGAAACTGGCGAGCTTGAGTGTGGCAGAGGGGGGGGGAATTCCGCGTGTA'
    'GCAGTGAAATGCGTAGAGATGCGGAGGAACACCGATGGCGAAGGCAACCCCCTGGGATAATATTTACGCTCA'
    'T\n</p><hr/>',
    '<h3>file1.fastq.gz (raw_forward_seqs)</h3>',
    '<b>MD5:</b>: eb3203ab33442b168c274b32c5624961</br>',
    '<p style="font-family:\'Courier New\', Courier, monospace;font-size:10;"'
    '>@MISEQ03:123:000000000-A40KM:1:1101:14149:1572 1:N:0:TCCACAGGAGT\n<br/>'
    'GGGGGGTGCCAGCCGCCGCGGTAATACGGGGGGGGCAAGCGTTGTTCGGAATTACTGGGCGTAAAGGGCTCG'
    'TAGGCGGCCCACTAAGTCAGACGTGAAATCCCTCGGCTTAACCGGGGAACTGCGTCTGATACTGGATGGCTT'
    'GAGGTTGGGAGAGGGATGCGGAATTCCAGGTGTAGCGGTGAAATGCGTAGATATCTGGAGGAACACCGGTGG'
    'CGAAGGCGGCATCCTGGACCAATTCTGACGCTGAG\n<br/>+\n<br/>CCCCCCCCCFFFGGGGGGGGGG'
    'GGHHHHGGGGGFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF-.;FFFFFFFFF9'
    '@EFFFFFFFFFFFFFFFFFFF9CFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFBFFFFFFFFFFFFFECFF'
    'FEFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFBFFFFFFFFFFFFFFFFF;CDEA@FFFFFFFFFFFFF'
    'FFFFFFFFFFFFF\n<br/>@MISEQ03:123:000000000-A40KM:1:1101:14170:1596 1:N:0'
    ':TCCACAGGAGT\n<br/>ATGGCGTGCCAGCAGCCGCGGTAATACGGAGGGGGCTAGCGTTGTTCGGAATT'
    'ACTGGGCGTAAAGCGCACGTAGGCGGCTTTGTAAGTTAGAGGTGAAAGCCCGGGGCTCAACTCCGGAACTGC'
    'CTTTAAGACTGCATCGCTAGAATTGTGGAGAGGTGAGTGGAATTCCGAGTGTAGAGGTGAAATTCGTAGATA'
    'TTCGGAAGAACACCAGTGGCGAAGGCGACTCACTGGACACATATTGACGCTGAG\n<br/>+\n<br/>CCC'
    'CCCCCCCFFGGGGGGGGGGGGGHHHGGGGGGGGGHHHGGGGGHHGGGGGHHHHHHHHGGGGHHHGGGGGHHH'
    'GHGGGGGHHHHHHHHGHGHHHHHHGHHHHGGGGGGHHHHHHHGGGGGHHHHHHHHHGGFGGGGGGGGGGGGG'
    'GGGGGGGGGGGFGGFFFFFFFFFFFFFFFFFF0BFFFFFFFFFFFFEFFFFFFFFFFFFFFFFFFFFFFFFF'
    'FFDFAFCFFFFFFFFFFFFFFFFFFBDFFFFF\n<br/>@MISEQ03:123:000000000-A40KM:1:11'
    '01:14740:1607 1:N:0:TCCACAGGAGT\n<br/>AGTGTGTGCCAGCAGCCGCGGTAATACGTAGGGT'
    'GCGAGCGTTAATCGGAATTACTGGGCGTAAAGCGTGCGCAGGCGGTTCGTTGTGTCTGCTGTGAAATCCCCG'
    'GGCTCAACCTGGGAATGGCAGTGGAAACTGGCGAGCTTGAGTGTGGCAGAGGGGGGGGGAATTCCGCGTGTA'
    'GCAGTGAAATGCGTAGAGATGCGGAGGAACACCGATGGCGAAGGCAACCCCCTGGGATAATATTTACGCTCA'
    'T\n</p><hr/>']

EXP_HTML_DEMUX = [
    '<h3>Features</h3>',
    '<b>Total</b>: 49', '<br/>',
    '<b>Max</b>: 151', '<br/>',
    '<b>Mean</b>: 151', '<br/>',
    '<b>Standard deviation</b>: 151', '<br/>',
    '<b>Median</b>: 0', '<br/>',
    ('<img src = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAyAAAAJYCAYAAA'
     'CadoJwAAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAPYQAAD2EBqD%2BnaQAAIABJREFUeJzs'
     '3Xm81gP%2B///nyVIpVEdMZEkjZJDI2D/T%2BESo8SU0kWhmMIPIMoPsXzNlHY1P37EOxRhj'
     '33fZx1JD4kdoxtKUEyVL2rSc3x90Po5TKPW%2B6jr3%2B%2B123cZ5v9/Xdb0u72p6eC9XRX'
     'V1dXUAAAAK0KDUAwAAAPWHAAEAAAojQAAAgMIIEAAAoDACBAAAKIwAAQAACiNAAACAwggQAA'
     'CgMAIEAAAojAABAAAKI0AAAIDCCBAAAKAwAgQAACiMAAEAAAojQAAAgMIIEAAAoDACBAAAKI'
     'wAAQAACiNAAACAwggQAACgMAIEAAAojAABAAAKI0AAAIDCCBAAAKAwAgQAACiMAAEAAAojQA'
     'AAgMIIEAAAoDACBAAAKIwAAQAACiNAAACAwggQAACgMAIEAAAojAABAAAKI0AAAIDCCBAAAK'
     'AwAgQAACiMAAEAAAojQAAAgMIIEAAAoDACBAAAKIwAAQAACiNAAACAwggQAACgMAIEAAAojA'
     'ABAAAKI0AAAIDCCBAAAKAwAgQAACiMAAEAAAojQAAAgMIIEAAAoDACZBE8/vjjadCgwQIfI0'
     'aMqLXtmDFj0rVr16y66qqprKxMnz59Mnny5BJNDgAAy4YVSz3A8ujYY49Np06dai1r27ZtzT'
     '%2BPHz8%2Bu%2ByyS5o3b55BgwZl6tSpufDCC/PKK69kxIgRWWmllYoeGQAAlgkCZDHsvPPO'
     '2XfffRe6fuDAgZkxY0ZGjRqV1q1bJ0m23XbbdOnSJUOHDs1hhx1W1KgAALBMcQrWYqiurs7U'
     'qVMzZ86cBa6/9dZb061bt5r4SJJdd9017dq1y0033VTUmAAAsMwRIIuhb9%2B%2BWX311dO4'
     'ceP89Kc/zQsvvFCzbsKECZk0aVK22WabOs/r1KlTRo0aVeSoAACwTHEK1iJo2LBh9ttvv%2B'
     'y5555ZY4018uqrr%2BbCCy/MzjvvnGeeeSYdOnRIVVVVkqRVq1Z1nt%2BqVatMmTIls2fPdh'
     '0IAAD1kgBZBNtvv3223377mp%2B7deuW/fbbL1tssUVOOeWU3H///ZkxY0aSL2Ll6xo1apQk'
     'mTFjxgIDZPLkyXnwwQezwQYbpHHjxkvpUwAAsLhmzJiRd955J7vvvnvWWGONUo%2BzXBIg31'
     'Pbtm3zs5/9LLfffnuqq6trwmHWrFl1tp05c2aSLDQuHnzwwfTu3XvpDQsAwBLx17/%2BNQcd'
     'dFCpx1guCZAlYN11183nn3%2BeadOm1Zx6Nf9UrK%2BqqqpKZWXlQk%2B/atOmTZIvfkFvuu'
     'mmS2/gZVD//v0zePDgUo9BQezv%2BsX%2Brl/s7/qlPu7vMWPGpHfv3jV/b2PRCZAl4K233k'
     'rjxo3TtGnTNG3aNC1btszIkSPrbDdixIh06NBhoa8z/xStTTfdNB07dlxq8y6LmjVrVu8%2B'
     'c31mf9cv9nf9Yn/XL/V5f8//exuLzl2wFsGkSZPqLBs9enTuuuuu7LbbbjXLevTokXvuuSfj'
     'x4%2BvWTZ8%2BPCMHTs2%2B%2B%2B/fyGzAgDAssgRkEXQs2fPrLLKKtl%2B%2B%2B2z5ppr'
     '5rXXXssVV1yRpk2b5txzz63ZbsCAAbn55pvTuXPnHHvssZk6dWouuOCCbLHFFunbt28JPwEA'
     'AJSWIyCLYJ999snkyZNz8cUX56ijjsrNN9%2Bc/fbbL//85z%2Bz8cYb12zXunXrPPHEE2nb'
     'tm1OPvnkXHjhhenWrVsefvhht98FAKBecwRkEfTr1y/9%2BvX7Ttu2b98%2BDzzwwFKeqHz0'
     '6tWr1CNQIPu7frG/6xf7u36xv1kcFdXV1dWlHoIvvPjii9l6663zwgsv1NsLugAAlmX%2Bvv'
     'b9OQULAAAojFOwAFiqxo4dm6lTp5Z6DIAlYsyYMaUeYbknQABYasaOHZt27dqVegwAliECBI'
     'Cl5n%2BPfPw1yaalHAVgCRmTpHeph1iuCRAACrBpEhdrAuAidAAAoEACBAAAKIwAAQAACiNA'
     'AACAwggQAACgMAIEAAAojAABAAAKI0AAAIDCCBAAAKAwAgQAACiMAAEAAAojQAAAgMIIEAAA'
     'oDACBAAAKIwAAQAACiNAAACAwggQAACgMAIEAAAojAABAAAKI0AAAIDCCBAAAKAwAgQAACiM'
     'AAEAAAojQAAAgMIIEAAAoDACBAAAKIwAAQAACiNAAACAwggQAACgMAIEAAAojAABAAAKI0AA'
     'AIDCCBAAAKAwAgQAACiMAAEAAAojQAAAgMIIEAAAoDACBAAAKIwAAQAACiNAAACAwggQAACg'
     'MAIEAAAojAABAAAKI0AAAIDCCBAAAKAwAgQAACiMAAEAAAojQAAAgMIIEAAAoDACBAAAKIwA'
     'AQAACiNAAACAwggQAACgMAIEAAAojAABAAAKI0AAAIDCCBAAAKAwAgQAACiMAAEAAAojQAAA'
     'gMIIEAAAoDACBAAAKIwAAQAACiNAAACAwggQAACgMAIEAAAojAABAAAKI0AAAIDCCBAAAKAw'
     'AgQAACiMAAEAAAojQAAAgMIIEAAAoDACBAAAKIwAAQAACiNAAACAwgiQ7%2BkPf/hDGjRokM'
     '0337zOujFjxqRr165ZddVVU1lZmT59%2BmTy5MklmBIAAJYNK5Z6gOXZ%2BPHjM3DgwDRp0i'
     'QVFRV11u2yyy5p3rx5Bg0alKlTp%2BbCCy/MK6%2B8khEjRmSllVYq0dQAAFA6AuR7OPHEE7'
     'PDDjtkzpw5dY5sDBw4MDNmzMioUaPSunXrJMm2226bLl26ZOjQoTnssMNKMTIAAJSUU7AW05'
     'NPPplbb701gwcPTnV1dZ0jILfeemu6detWEx9Jsuuuu6Zdu3a56aabih4XAACWCQJkMcydOz'
     'f9%2BvXLYYcdls0226zO%2BgkTJmTSpEnZZptt6qzr1KlTRo0aVcSYAACwzHEK1mK47LLLMm'
     '7cuDz66KMLXF9VVZUkadWqVZ11rVq1ypQpUzJ79mzXgQAAUO84ArKIPvzww5xxxhk544wzUl'
     'lZucBtZsyYkSRp2LBhnXWNGjWqtQ0AANQnjoAsotNOOy1rrLFG%2BvXrt9BtGjdunCSZNWtW'
     'nXUzZ86stc2C9O/fP82aNau1rFevXunVq9fijAwAwGK54cvHV31cikHKigBZBGPHjs2VV16Z'
     'wYMHZ/z48TXLZ86cmc8//zzvvvtuVltttZpTr%2BafivVVVVVVqays/MbTrwYPHpyOHTsu%2'
     'BQ8AAMAi6PXl46teTLJ1CWYpHwJkEUyYMCHz5s3LMccck2OOOabO%2BjZt2qR///754x//mJ'
     'YtW2bkyJF1thkxYkQ6dOhQxLgAALDMESCLYPPNN8/tt99e65a71dXVOe200/LZZ5/lT3/6U9'
     'q2bZsk6dGjR4YNG5bx48fX3Ip3%2BPDhGTt2bE444YSSzA8AAKUmQBZBZWVl9t577zrLL774'
     '4iTJz372s5plAwYMyM0335zOnTvn2GOPzdSpU3PBBRdkiy22SN%2B%2BfQubGQAAliXugrUE'
     'VFRU1PkiwtatW%2BeJJ55I27Ztc/LJJ%2BfCCy9Mt27d8vDDD7v9LgAA9ZYjIEvAY489tsDl'
     '7du3zwMPPFDwNAAAsOxyBAQAACiMAAEAAAojQAAAgMIIEAAAoDACBAAAKIwAAQAACiNAAACA'
     'wggQAACgMAIEAAAojAABAAAKI0AAAIDCCBAAAKAwAgQAACiMAAEAAAojQAAAgMIIEAAAoDAC'
     'BAAAKIwAAQAACiNAAACAwggQAACgMAIEAAAojAABAAAKI0AAAIDCCBAAAKAwAgQAACiMAAEA'
     'AAojQAAAgMIIEAAAoDACBAAAKIwAAQAACiNAAACAwggQAACgMAIEAAAojAABAAAKI0AAAIDC'
     'CBAAAKAwAgQAACiMAAEAAAojQAAAgMIIEAAAoDACBAAAKIwAAQAACiNAAACAwggQAACgMAIE'
     'AAAojAABAAAKs2KpByjKvHnz8thjj%2BXzzz/PTjvtlFVXXbXUIwEAQL1TlkdATj311HTu3L'
     'nm5%2Brq6uy2227p0qVL9tprr/zoRz/Kv//97xJOCAAA9VNZBsitt96aTp061fx8yy235NFH'
     'H80f/vCH3HPPPZk7d27OPPPMEk4IAAD1U1megjVhwoRstNFGNT/fdttt2XTTTXPKKackSY48'
     '8shceumlpRoPAADqrbI8ArLiiitm1qxZSb649mP48OHp2rVrzfo111wzkyZNKtV4AABQb5Vl'
     'gGy22Wa57rrrMmXKlAwdOjSTJ0/OXnvtVbN%2B3LhxWWONNUo4IQAA1E9leQrWmWeemW7dut'
     'VExo477ljrovR777231jUiAABAMcoyQLp06ZIXX3wxDz/8cJo3b56ePXumoqIiSfLRRx9l55'
     '13zt57713iKQEAoP4pywBJvjgNa7PNNquzvHnz5hk8eHAJJgIAAMo2QJLk2WefzeOPP54PPv'
     'ggRx55ZDbaaKNMnz49r7/%2BejbaaCNfRggAAAUry4vQP//88%2Byzzz7Zcccdc%2Bqpp%2B'
     'aSSy7Jf/7znyRJRUVFdtttt/zpT38q8ZQAAFD/lGWAnH766bn33ntz2WWX5Y033kh1dXXNus'
     'aNG2f//ffPXXfdVcIJAQCgfirLALnhhhvy61//OocffniaN29eZ/0mm2ySf//73yWYDAAA6r'
     'eyDJAPPvggW2yxxULXr7DCCpk%2BfXqBEwEAAEmZBkjr1q0zZsyYha5/5pln8sMf/rDAiQAA'
     'gKRMA%2BSggw7K5Zdfnmeeeabm%2Bz/mu/LKK3PjjTemT58%2BJZoOAADqr7K8De%2BAAQPy'
     '3HPPZZdddsmmm26aJDn%2B%2BOPz4YcfZsKECdlzzz1z3HHHlXhKAACof8ryCEjDhg1z//33'
     'Z%2BjQodlwww2zySabZObMmdlyyy0zdOjQ3H333VlxxbJsLwAAWKaV7d/CGzRokN69e6d379'
     '6lHgUAAPhSWR4B%2BfDDD/Pyyy8vdP3LL7%2BcKVOmFDgRAACQlGmAHH/88Tn88MMXuv7Xv/'
     '51TjzxxAInAgAAkjINkEcffTTdu3df6Pru3btn%2BPDhBU4EAAAkZRogkyZNSsuWLRe6vkWL'
     'Fnn//fcLnAgAAEjKNEB%2B8IMf5MUXX1zo%2BhdffPEbAwUAAFg6yjJA9tlnn/zlL3/JnXfe'
     'WWfdHXfckauvvjr77LNPCSYDAID6rSxvw3vmmWfmkUceyT777JMOHTrkRz/6UZLklVdeyejR'
     'o9O%2BffucffbZJZ4SAADqn7I8AtKsWbM8%2B%2ByzOf300/P555/n5ptvzi233JI5c%2Bbk'
     'jDPOyPPPP5/mzZuXekwAAKh3yvIISJI0bdo0Z599tiMdAACwDCnLIyAAAMCyqWyPgLz22mu5'
     '5ppr8vbbb%2Bejjz5KdXV1zbrq6upUVFTk0UcfLeGEAABQ/5RlgFx33XU59NBDs/LKK2fjjT'
     'dOs2bNSj0SAACQMg2Qs846K1tttVUeeOCBrLHGGqUeBwAA%2BFJZXgPy3nvv5Ze//KX4AACA'
     'ZUxZBsjmm2%2Be9957r9RjAAAAX1OWAfLHP/4xV111Vf7xj3%2BUehQAAOAryvIakPPOOy/N'
     'mjXLzjvvnM022yzrrbdeVlhhhTrb3XXXXSWYDgAA6q%2ByPALyyiuvZObMmVlvvfUyderUvP'
     'rqq3n55ZdrPV555ZVFft1XX301%2B%2B%2B/f9q2bZsmTZqksrIyO%2BywQ66//vo6244ZMy'
     'Zdu3bNqquumsrKyvTp0yeTJ09eEh8PAACWW2V5BOSdd95ZKq87bty4fPbZZzn00EOz9tprZ/'
     'r06bnlllty8MEH55133smpp56aJBk/fnx22WWXNG/ePIMGDcrUqVNz4YUX5pVXXsmIESOy0k'
     'orLZX5AABgWVeWAbK07LHHHtljjz1qLTvqqKOy9dZb54orrqgJkIEDB2bGjBkZNWpUWrdunS'
     'TZdttt06VLlwwdOjSHHXZY4bMDAMCyoCxPwUqSOXPm5IYbbsjhhx%2BeffbZp%2BaUq08%2B'
     '%2BSS33XZb3n///SXyPg0aNEjr1q1rHdW49dZb061bt5r4SJJdd9017dq1y0033bRE3hcAAJ'
     'ZHZXkE5OOPP87uu%2B%2BekSNHpkmTJpk2bVr69euXJGnSpEmOOeaYHHzwwRk0aNBivf706d'
     'Mzffr0fPLJJ7nrrrvy4IMPZsiQIUmSCRMmZNKkSdlmm23qPK9Tp065//77F/%2BDAQDAcq4s'
     'j4CcfPLJee211/LAAw/k7bffrrVuxRVXzH777fe9QuD444/PmmuumY022ignnXRSLrnkkhx%'
     '2B%2BOFJkqqqqiRJq1at6jyvVatWmTJlSmbPnr3Y7w0AAMuzsgyQO%2B64I0cffXR22223Ba'
     '7faKON6oTJojjuuOPyyCOP5Nprr82uu%2B6ao48%2BOsOGDUuSzJgxI0nSsGHDOs9r1KhRrW'
     '0AAKC%2BKctTsD755JNsuOGGC10/e/bszJkzZ7Fff%2BONN87GG2%2BcJOndu3d233339O/f'
     'Pz179kzjxo2TJLNmzarzvJkzZyZJzTYL079//zRr1qzWsl69eqVXr16LPTMAAIvqhi8fX/Vx'
     'KQYpK2UZIBtuuGFeeOGFhd5t6uGHH0779u2X2Pv16NEjDz/8cF5//fWaU6/mn4r1VVVVVams'
     'rPzW2/AOHjw4HTt2XGLzAQCwOHp9%2BfiqF5NsXYJZykdZnoJ12GGH5eqrr86NN95Ya/nMmT'
     'Nz6qmn5v77788RRxyxxN5v/ilVDRo0yDrrrJOWLVtm5MiRdbYbMWJEOnTosMTeFwAAljdleQ'
     'TkmGOOyauvvppevXpl9dVXT5IceOCB%2BfDDDzN37twcccQR%2BdWvfrXIrztp0qS0bNmy1r'
     'LZs2fn2muvTWVlZTbbbLMkXxwRGTZsWMaPH19zK97hw4dn7NixOeGEE77npwMAgOVXWQZIgw'
     'YNcuWVV%2BaQQw7JzTffnLFjx2bevHlp27ZtevbsmV122WWxXvfwww/P1KlTs8suu2TttdfO'
     'xIkTc/311%2BfNN9/MNddckxVWWCFJMmDAgNx8883p3Llzjj322EydOjUXXHBBtthii/Tt23'
     'dJflQAAFiulGWAzLfTTjtlp512WmKv9/Of/zx/%2Bctfcumll%2BbDDz/Maqutlh//%2BMcZ'
     'MmRIdt1115rtWrdunSeeeCLHH398Tj755DRs2DDdunXLRRdd9K3XfwAAQDkr6wBZ0nr27Jme'
     'PXt%2Bp23bt2%2BfBx54YClPBAAAy5eyDJA2bdqkoqIi1dXVtZZXVFQkSaqrq1NRUZG33nqr'
     'FOMBAEC9VZYB8l//9V91ls2dOzfvvvtu/vGPf%2BRHP/qR29wCAEAJlGWADB06dKHrRo8end'
     '133z0HHXRQcQMBAABJyvR7QL7JlltumSOOOCInnXRSqUcBAIB6p94FSJKsueaaefXVV0s9Bg'
     'AA1Dv1LkAmT56cq6%2B%2BuuYLAgEAgOKU5TUgnTt3rrnj1Vd99NFHef3112u%2BvRwAAChW'
     'WQbI/NvvfvU2vBUVFWnTpk26dOmSX/ziF9lkk01KNR4AANRbZRkgjz/%2BeKlHAAAAFqDeXQ'
     'MCAACUTlkeARk2bNgCrwH5Nn369FkK0wAAAPOVZYD07dt3sZ4nQAAAYOkqywB58cUXc8ghh6'
     'RZs2bp169f2rVrlyR544038j//8z/59NNPM2zYsKy%2B%2BuolnhQAAOqXsgyQwYMHp2XLln'
     'nooYfSoMH/XuayxRZbZN99981uu%2B2Wiy%2B%2BOEOHDi3dkAAAUA%2BV5UXod955Z/bdd9'
     '9a8THfCiuskH333Td33nlnCSYDAID6rSwDZN68eRkzZsxC148ZM6bWd4QAAADFKMsA2WeffX'
     'LppZfmoosuyvTp02uWT5s2LRdeeGEuu%2Byy7L333iWcEAAA6qeyvQbk7bffzm9/%2B9sMGD'
     'AgrVq1SnV1daqqqjJnzpzsuOOOGTx4cKnHBACAeqcsA6RZs2Z5/PHHc9ddd%2BW%2B%2B%2B'
     '7Lu%2B%2B%2BmyTp2rVr9tprr3Tv3n2xvicEAAD4fsoyQJKkoqIie%2B%2B9t1OtAABgGVK2'
     'AZIk48ePz1NPPZUPPvggPXr0SOvWrTN37tx88sknWW211bLiimX98QEAYJlTlhehV1dX57jj'
     'jkubNm1y0EEH5fjjj8%2Bbb76ZJJk6dWrWX3/9/M///E%2BJpwQAgPqnLAPkggsuyCWXXJLf'
     '/va3efjhh2vdcrdZs2bp0aNHbrvtthJOCAAA9VNZBsiVV16Zgw8%2BOAMHDsyWW25ZZ/3mm2'
     '%2BeN954owSTAQBA/VaWAfKf//wnO%2B6440LXN2nSJJ9%2B%2BmmBEwEAAEmZBkjLli0zbt'
     'y4ha5/8cUXs9566xU4EQAAkJRpgPTo0SOXX355/v3vf9f5vo%2BHHnooQ4cOzf7771%2Bi6Q'
     'AAoP4qywA566yz0qpVq3To0CF9%2BvRJkpx//vnZcccd07Vr12yxxRYZMGBAiacEAID6pywD'
     'pFmzZnn22Wdz0kknZfz48WnUqFGeeOKJfPLJJznrrLPy1FNPpUmTJqUeEwAA6p2y/Sa%2BVV'
     'ZZJaeddlpOO%2B20Uo8CAAB8qSyPgCzMW2%2B9lTFjxpR6DAAAqLfKMkAuueSS/PznP6%2B1'
     '7NBDD80Pf/jDbLbZZtl6663zwQcflGg6AACov8oyQK666qqsueaaNT8/%2BOCDufbaa3PEEU'
     'dkyJAheeutt3LWWWeVbkAAAKinyvIakHfffTft27ev%2Bfmmm27KBhtskD//%2Bc%2BpqKjI'
     'xIkTc91115VwQgAAqJ/K8ghIdXV1rZ8feuih7LHHHjXfCbL%2B%2BuunqqqqFKMBAEC9VpYB'
     'stFGG%2BW2225LdXV1HnzwwUyYMCF77LFHzfoJEyakWbNmJZwQAADqp7I8Beu3v/1tDjzwwL'
     'Ro0SKfffZZNt100%2By%2B%2B%2B416x999NF06NChhBMCAED9VJYB8vOf/zyVlZW5995707'
     'x58xx55JFZaaWVkiRTpkxJ8%2BbNc/DBB5d4SgAAqH/KMkCSpEuXLunSpUud5S1atMjtt99e'
     'gokAAICyvAYEAABYNgkQAACgMAIEAAAojAABAAAKUxYBcskll%2BTNN98s9RgAAMC3KIsA6d'
     '%2B/f/75z3/W/NygQYP87W9/K%2BFEAADAgpRFgDRv3jwTJ04s9RgAAMC3KIvvAencuXPOOu'
     'usvPTSS1l99dWTJNdee22ee%2B65b3zeJZdcUsR4AADAl8oiQP7f//t/Oe644/LQQw9l0qRJ'
     'SZKHHnooDz300Dc%2BT4AAAECxyuIUrLXWWit/%2B9vfMnHixMydOzdJct1112XevHnf%2BA'
     'AAAIpVFgHydVdffXV22GGHUo8BAAB8TVmcgvV1hx56aJKkuro6r732WsaNG5ckWX/99dO%2B'
     'ffsSTgYAAPVbWQZIktxxxx05/vjj884779Ra3qZNm/zxj3/M3nvvXZrBAACgHivLU7Duu%2B'
     '%2B%2B7LfffqmoqMigQYNy%2B%2B235/bbb8%2BgQYOSJD169Mj9999f4ikBAKD%2BKcsjIO'
     'ecc04233zzPP3002nSpEnN8r333jtHH310dtppp/zf//t/s8cee5RwSgAAqH/K8gjIyy%2B/'
     'nEMPPbRWfMzXpEmTHHLIIRk9enQJJgMAgPqtLAOkYcOG%2BfDDDxe6/qOPPkqjRo0KnAgAAE'
     'jKNEB23XXXXHLJJXnmmWfqrHvuuedyySWX5L//%2B79LMBkAANRvZXkNyHnnnZennnoqO%2B'
     '20U3784x9n4403TpK8/vrrGTFiRNZaa62cd955JZ4SAADqn7I8ArLhhhtm9OjROfbYYzNlyp'
     'T8/e9/z4033piPP/44/fv3z%2BjRo9OmTZtSjwkAAPVOWR4BSZK11lorF198cS6%2B%2BOJS'
     'jwIAAHypLI%2BAAAAAyyYBAgAAFEaAAAAAhREgAABAYQQIAABQmLILkGnTpqVjx4657LLLSj'
     '0KAADwNWUXIE2aNMk777yTioqKUo8CAAB8TdkFSJJ07do1Dz74YKnHAAAAvqYsA%2BT000/P'
     'm2%2B%2Bmd69e%2Bfpp5/OhAkTMmXKlDoPAACgWGX5TeibbbZZkuS1117L3/72twVuU1FRkb'
     'lz5xY5FgAA1HtlGSBnnHHGt27jGhEAACheWQbIWWedVeoRAACABSjLa0C%2B7pNPPsmcOXNK'
     'PQYAANR7ZRsgI0eOzO67757GjRunRYsWefLJJ5MkkyZNys9%2B9rM8/vjjpR0QAADqobIMkG'
     'eeeSY777xz/vWvf6V3796prq6uWdeyZct88sknufzyy0s4IQAA1E9lGSADBgzIJptskldffT'
     'WDBg2qs75z5855/vnnSzAZAADUb2UZICNHjkzfvn3TqFGjBa5fZ511UlVVVfBUAABAWQbISi'
     'utVOu0q69777330rRp0wInAgAAkjINkO222y633HLLAtdNmzYt11xzTf7rv/6r4KkAAICyDJ'
     'Czzz47I0eOzJ577pn7778/SfLSSy/lyiuvTMeOHfPBBx/k9NNPL/GUAABQ/5TlFxH%2B%2BM'
     'c/zv33359f//rXOeSQQ5IkJ554YpKkbdu2uf/%2B%2B7PllluWckQAAKiXyjJAkuSnP/1p3n'
     'jjjbz00ksZO3Zs5s2bl7Zt22abbbZJRUVFqccDAIB6qSxPwZqvoqIiW221VQ444ID8/Oc/T6'
     'dOnb5XfIwcOTJHH310NttsszRt2jTrr79%2BevbsmbFjx9bZdsyYMenatWtWXXXVVFZWpk%2'
     'BfPpk8efL3%2BTgAALDcK9sjIDNnzsyVV16Z%2B%2B67L%2B%2B%2B%2B26SZIMNNsgee%2B'
     'yRww47bKG36P0m5513Xp599tnsv//%2B2WKLLVJVVZUhQ4akY8eOee6557LZZpslScaPH59d'
     'dtklzZs3z6BBgzJ16tRceOGFeeWVVzJixIistNJKS/SzAgDA8qIsA2T8%2BPH57//%2B77z5'
     '5ptp1apV2rZtm%2BSLC9EfeOCBDBkyJMOHD0/r1q0X6XVPOOGEdOrUKSuu%2BL//2nr27JnN'
     'N9885557bq677rokycCBAzNjxoyMGjWq5j223XbbdOnSJUOHDs1hhx22hD4pAAAsX8ryFKyj'
     'jjoq48aNy0033ZQJEybkySefzJNPPpkJEybkxhtvzLhx43LkkUcu8utuv/32teIjSX74wx%2'
     'Bmffv2ef3112uW3XrrrenWrVutwNmJ/dRyAAAgAElEQVR1113Trl273HTTTYv/wQAAYDlXlg'
     'EyfPjw9O/fP/vtt1%2Bt5RUVFdl///3Tv3//PProo0vkvaqrq/P%2B%2B%2B9njTXWSJJMmD'
     'AhkyZNyjbbbFNn206dOmXUqFFL5H0BAGB5VJYB0rRp06y11loLXf%2BDH/xgiX0T%2BvXXX5'
     '/33nsvPXv2TJJUVVUlSVq1alVn21atWmXKlCmZPXv2EnlvAABY3pRlgPziF7/I0KFDM23atD'
     'rrPvvss1xzzTX55S9/%2Bb3f5/XXX89RRx2VHXbYoeb7RmbMmJEkadiwYZ3t51/4Pn8bAACo'
     'b8riIvTbbrut1s8dOnTIvffem0033TR9%2BvTJRhttlCR58803c%2B2116ZFixbf%2B4sIJ0'
     '6cmL322ivNmzfPLbfcUnN738aNGydJZs2aVec5M2fOrLXNwvTv3z/NmjWrtaxXr17p1avX95'
     'oZAIBFccOXj6/6uBSDlJWyCJCvX%2BvxVQMHDqyzbMKECenVq1cOOOCAxXq/Tz75JHvssUc%'
     '2B/fTTPPXUU/nBD35Qs27%2BqVfzT8X6qqqqqlRWVn7rbXgHDx6cjh07LtZsAAAsKb2%2BfH'
     'zVi0m2LsEs5aMsAmRJXVD%2BXcycOTPdu3fPv/71rzzyyCPZZJNNaq1fZ5110rJly4wcObLO'
     'c0eMGJEOHToUNSoAACxzyiJAfvKTnxTyPnPnzk3Pnj3z/PPP584778yPf/zjBW7Xo0ePDBs2'
     'LOPHj6%2B5Fe/w4cMzduzYnHDCCYXMCgAAy6KyCJCinHDCCbn77rvTvXv3TJ48OX/9619rre'
     '/du3eSZMCAAbn55pvTuXPnHHvssZk6dWouuOCCbLHFFunbt28pRgcAgGVC2QbIU089lauvvj'
     'pvv/12Pvroo1RXV9esq66uTkVFRV5%2B%2BeVFes3Ro0enoqIid999d%2B6%2B%2B%2B5a6y'
     'oqKmoCpHXr1nniiSdy/PHH5%2BSTT07Dhg3TrVu3XHTRRd96/QcAAJSzsgyQiy%2B%2BOCec'
     'cEIaN26cjTfeOM2bN6%2Bzzfy7Vi2Kxx577Dtv2759%2BzzwwAOL/B4AAFDOyjJAzj///Oy4'
     '44655557svrqq5d6HAAA4Etl%2BUWE06ZNS%2B/evcUHAAAsY8oyQH7yk5/klVdeKfUYAADA'
     '15RlgAwZMiQPPvhgLrjggkyZMqXU4wAAAF8qywBZb731csQRR%2BSkk05Ky5Yt06RJk6y66q'
     'pZddVVs9pqq9X8LwAAUKyyvAj99NNPzx/%2B8Ie0bt06W2%2B99QKvBVmcu2ABAADfT1kGyO'
     'WXX5699tord955Zxo0KMuDPAAAsFwqy7%2Bdf/755%2BnWrZv4AACAZUxZ/g19zz33zFNPPV'
     'XqMQAAgK8pywA566yz8uqrr%2BY3v/lNXnjhhUyaNClTpkyp8wAAAIpVlteAbLLJJkmS0aNH'
     '5/LLL1/gNhUVFZk7d26RYwEAQL1XlgFyxhlnfOs27oIFAADFK8sAOeuss0o9AgAAsABleQ0I'
     'AACwbCrLIyBnn332dzrF6rucqgUAACw5ZRsg34UAAQCAYpXlKVjz5s2r85g9e3b%2B9a9/5f'
     'jjj8/WW2%2BdDz74oNRjAgBAvVOWAbIgK6ywQjbccMNceOGF2WijjdKvX79SjwQAAPVOvQmQ'
     'r9pll11y3333lXoMAACod%2BplgLzwwgtp0KBefnQAACipsrwIfdiwYQu8C9bHH3%2BcJ554'
     'Irfffnt%2B%2BctflmAyAACo38oyQPr27bvQdWussUZOPvlkd8ACAIASKMsAeeutt%2Bosq6'
     'ioSPPmzbPaaquVYCIAACAp0wDZYIMNSj0CAACwAK7EBgAAClM2R0A233zzBV54viDV1dWpqK'
     'jIyy%2B/vJSnAgAAvqpsAqSysvJbt6moqMjEiRPzxhtvFDARAADwdWUTII8//vg3rp84cWLO'
     'O%2B%2B8XH755VlhhRXSu3fvYgYDAABqlE2ALMzEiRNz7rnn5oorrsicOXPSu3fvnHrqqWnb'
     'tm2pRwMAgHqnbAOkqqoq5513Xq3wOO2007LhhhuWejQAAKi3yi5Aqqqqcu655%2BbKK6/MnD'
     'lzcvDBB%2Be0005LmzZtSj0aAADUe2UTIO%2B9915NeMydOzd9%2BvTJqaeeKjwAAGAZUjYB'
     '0rZt28yaNSsdOnTIgAED0qZNm3z00Uf56KOPFvqcjh07FjghAABQNgEya9asJMlLL72UAw44'
     '4Fu3r6ioyNy5c5f2WAAAwFeUTYBcffXVpR4BAAD4FmUTIIceemipRwAAAL5Fg1IPAAAA1B8C'
     'BAAAKIwAAQAACiNAAACAwggQAACgMAIEAAAojAABAAAKI0AAAIDCCBAAAKAwAgQAACiMAAEA'
     'AAojQAAAgMIIEAAAoDACBAAAKIwAAQAACiNAAACAwggQAACgMAIEAAAojAABAAAKI0AAAIDC'
     'CBAAAKAwAgQAACiMAAEAAAojQAAAgMIIEAAAoDACBAAAKIwAAQAACiNAAACAwggQAACgMAIE'
     'AAAojAABAAAKI0AAAIDCCBAAAKAwAgQAACiMAAEAAAojQAAAgMIIEAAAoDACBAAAKIwAAQAA'
     'CiNAAACAwggQAACgMAIEAAAojAABAAAKI0AAAIDCCBAAAKAwAgQAACiMAFlE06ZNy5lnnpmu'
     'XbumRYsWadCgQYYNG7bAbceMGZOuXbtm1VVXTWVlZfr06ZPJkycXPDEAACw7BMgimjRpUs45'
     '55y88cYb6dChQ5KkoqKiznbjx4/PLrvskrfeeiuDBg3KiSeemHvvvTddunTJ7Nmzix4bAACW'
     'CSuWeoDlzdprr52JEydmzTXXzAsvvJBOnTotcLuBAwdmxowZGTVqVFq3bp0k2XbbbdOlS5cM'
     'HTo0hx12WJFjAwDAMsERkEW08sorZ80110ySVFdXL3S7W2%2B9Nd26dauJjyTZdddd065du9'
     'x0001LfU4AAFgWCZClYMKECZk0aVK22WabOus6deqUUaNGlWAqAAAoPQGyFFRVVSVJWrVqVW'
     'ddq1atMmXKFNeBAABQLwmQpWDGjBlJkoYNG9ZZ16hRo1rbAABAfeIi9KWgcePGSZJZs2bVWT'
     'dz5sxa2yxI//7906xZs1rLevXqlV69ei3BKQEA%2BGY3fPn4qo9LMUhZESBLwfxTr%2Bafiv'
     'VVVVVVqayszEorrbTQ5w8ePDgdO3ZcavMBAPBd9Pry8VUvJtm6BLOUD6dgLQXrrLNOWrZsmZ'
     'EjR9ZZN2LEiJrvDwEAgPpGgCwlPXr0yD333JPx48fXLBs%2BfHjGjh2b/fffv4STAQBA6TgF'
     'azEMGTIkH3/8cd57770kyV133ZVx48YlSY455pisttpqGTBgQG6%2B%2BeZ07tw5xx57bKZO'
     'nZoLLrggW2yxRfr27VvK8QEAoGQEyGK46KKL8u677yZJKioqcvvtt%2Be2225LRUVF%2BvTp'
     'k9VWWy2tW7fOE088keOPPz4nn3xyGjZsmG7duuWiiy76xus/AACgnAmQxfD2229/p%2B3at2'
     '%2BfBx54YClPAwAAyw/XgAAAAIURIAAAQGEECAAAUBgBAgAAFEaAAAAAhREgAABAYQQIAABQ'
     'GAECAAAURoAAAACFESAAAEBhBAgAAFAYAQIAABRGgAAAAIURIAAAQGEECAAAUBgBAgAAFEaA'
     'AAAAhREgAABAYQQIAABQGAECAAAURoAAAACFESAAAEBhBAgAAFAYAQIAABRGgAAAAIURIAAA'
     'QGEECAAAUBgBAgAAFEaAAAAAhREgAABAYQQIAABQGAECAAAURoAAAACFESAAAEBhBAgAAFAY'
     'AQIAABRGgAAAAIURIAAAQGEECAAAUBgBAgAAFEaAAAAAhREgAABAYQQIAABQGAECAAAURoAA'
     'AACFESAAAEBhBAgAAFAYAQIAABRGgAAAAIURIAAAQGEECAAAUBgBAgAAFEaAAAAAhREgAABA'
     'YQQIAABQGAECAAAURoAAAACFESAAAEBhBAgAAFAYAQIAABRGgAAAAIURIAAAQGEECAAAUBgB'
     'AgAAFEaAAAAAhREgAABAYQQIAABQGAECAAAURoAAAACFESAAAEBhBAgAAFAYAQIAABRGgAAA'
     'AIURIAAAQGEECAAAUBgBAgAAFEaAAAAAhREgAABAYQQIAABQGAECAAAURoAAAACFESAAAEBh'
     'BMhSNGvWrJx00klZe%2B21s8oqq2S77bbLI488UuqxAACgZATIUnTooYfm4osvzsEHH5xLLr'
     'kkK6ywQvbcc8/84x//KPVoy5wbbrih1CNQIPsbypnf3/WL/c2iEyBLyYgRI3LjjTfm3HPPzX'
     'nnnZdf/epXefTRR7P%2B%2Buvnd7/7XanHW%2Bb4C2n9Yn9DOfP7u36xv1l0AmQpueWWW7Li'
     'iivm8MMPr1nWsGHD/PKXv8yzzz6bCRMmlHA6AAAoDQGylIwaNSrt2rVL06ZNay3v1KlTkuSl'
     'l14qxVgAAFBSAmQpqaqqSqtWreosn7/svffeK3okAAAouRVLPUC5mjFjRho2bFhneaNGjWrW'
     'f93MmTOTJPfdd1/GjBmzdAdchsyaNStvvvlmfv/735d6lELNnj07kyZNKvUYhZs9e3ZGjhyZ'
     '/fffv9SjFGrOnDmZOnVqqcco3KeffvrlP92XpP78uZbMSlIf/0PT7CQvJzmy1IMUbHaSj0s9'
     'RAnMSfJskv8u9SAF%2B%2BLPtQX9XY7vRoAsJY0bN86sWbPqLJ8fGY0bN66z7u23306SnH76'
     '6Ut3uGVUff3c9dUtt9xS6hEolN/f9culpR6AQg0v9QAl8c4772THHXcs9RjLJQGylLRq1WqB'
     'p1lVVVUlSdZee%2B0663bffff89a9/zQYbbLDAQAEAoLRmzpyZt99%2BO7vvvnupR1luCZCl'
     'ZKuttsrjjz%2BeqVOnZtVVV61Z/vzzzydJOnToUOc5a6yxRg466KDCZgQAYNHtsMMOpR5hue'
     'Yi9KVkv/32y9y5c3PFFVfULJs1a1auueaabLfddllnnXVKOB0AAJSGIyBLybbbbpv9998/p5'
     'xySj744IO0bds2w4YNy7hx43LNNdeUejwAACgJR0CWomuvvTb9%2B/fPddddl2OPPTZz587N'
     'Pffck5122qnUoy2WadOm5cwzz0zXrl3TokWLNGjQIMOGDauz3aGHHpoGDRrUeWy66aYLfN2/'
     '/OUv2XTTTdO4ceO0a9cuQ4YMWaS5/v3vf%2BfAAw/MWmutlVVWWSXt2rXLaaedtlifkf%2B1'
     'LO7vN998MwcddFDWXXfdrLLKKvnhD3%2BYE044IVOmTFnsz8kXlsb%2BvvTSS7P//vtnvfXW'
     'S4MGDdK3b99Fmqm6ujrnn39%2B2rRpk8aNG2fLLbfM3//%2B98X%2BjPyvZW1/v/766/nd73'
     '6XDh06ZLXVVsvaa6%2Bdbt265YUXXvhen5MvLGv7%2B%2Buuv/76NGjQoNYp65Q3R0CWooYN'
     'G%2Bb888/P%2BeefX%2BpRlohJkyblnHPOyfrrr58OHTrk8ccfT0VFxQK3bdiwYf7yl7/UWr'
     'b66qvX2e7yyy/Pb37zm%2By333458cQT8%2BSTT%2BaYY47J9OnT87vf/e5bZ3rppZfyk5/8'
     'JOuuu25OPPHEVFZW5t1338348eMX70NSY1nb3xMnTsx2222XlVZaKUceeWTWXXfdvPTSSxky'
     'ZEgee%2ByxvPDCCwudj2%2B3NPb3%2Beefn88%2B%2ByzbbrttJk6cuMj7Z8CAATnvvPNy%2'
     'BOGHp1OnTrnjjjty4IEHpqKiIj179lyk16K2ZW1/X3XVVbn66quz33775eijj87HH3%2Bcyy'
     '%2B/PNttt10eeOCB7Lrrrov2AallWdvfX/XZZ5/ld7/7XZo0aeLP8PqkGr6jWbNmVb///vvV'
     '1dXV1f/85z%2BrKyoqqocNG1Znu0MOOaR61VVX/dbXmz59enVlZWV19%2B7day3v3bt3ddOm'
     'Tas/%2Buijb3z%2B3Llzq3/0ox9Vb7/99tUzZ85chE/Cd7Gs7e8rrriiuqKiovq%2B%2B%2B'
     '6rtfzMM8%2BsrqioqH7ppZe%2BdQYWbknv7%2Brq6upx48bV/HPTpk2r%2B/bt%2B53nGT9%'
     '2BfPVKK61U3a9fv1rLd9lll%2Bp11123eu7cud/5tahrWdvfL7zwQvW0adNqLfvwww%2Br11'
     'xzzeqddtrpO78OC7as7e%2BvOumkk6o32WSTmv8voH5wChbf2corr5w111wzyRenRnyT6urq'
     'zJs37ytfQlbXY489lilTpuTII2t/YdVRRx2VadOm5d577/3G93jooYfy6quv5swzz0zDhg0z'
     'ffr0zJ079zt%2BGr7Nsra/53%2BJ5/yZ5vvBD36QZMHfrcN3t6T3d5Ksu%2B66iz3PnXfemT'
     'lz5tT59fKb3/wm48ePz7PPPrvYr82yt787duyYVVZZpdayFi1aZKeddqpXX8y7tCxr%2B3u%'
     '2BsWPHZvDgwbn44ouzwgorfO/XY/khQFgqpk%2BfntVWWy3NmjVLZWVljj766EybNq3WNqNG'
     'jUqSbLPNNrWWd%2BzYMQ0aNMhLL730je/xyCOPJPniD9ZtttkmTZs2TZMmTdKrV6989NFHS/'
     'DT8G2K2N89evTIxhtvnGOPPTbPP/98xo8fn/vuuy8DBw7MPvvsk3bt2i3ZD8VCfZf9/X2NGj'
     'UqTZs2zSabbFJreadOnZLkW3%2B9sOQUsb8XZuLEiWnZsmUh78UXitzf/fv3z09/%2BtN07d'
     'p1qbw%2Byy7XgLDErb322jnppJPSsWPHzJs3L/fff3/%2B/Oc/Z/To0Xn88cdr/itHVVVVVl'
     'hhhayxxhq1nr/yyiunsrJygV/k%2BFVjx45NkhxwwAHZY489cuqpp%2Ball17KoEGD8p///C'
     'dPP/300vmA1FLU/l5llVXy9NNPp3v37tl%2B%2B%2B1rlh966KG58sorl/wHY4G%2B6/7%2B'
     'vqqqqrLWWmvVWd6qVask%2BdZfLywZRe3vBXnqqafy3HPP5fTTT19q70FtRe7ve%2B%2B9Nw'
     '8//HBefvnlJfaaLD8ECEvcwIEDa/18wAEHpF27djn11FNzyy231Fw8OmPGjKy88soLfI2GDR'
     'tmxowZ3/g%2Bn332WZIvbnl87bXXJkn22WefrLLKKjnllFMyfPhwFy4WoKj9PW3atHTv3j3v'
     'vPNO/vSnP2X99dfPk08%2BmUsuuSSVlZW54IILlswH4ht91/39fc2YMSMNGzass3z%2BqXjf'
     '9uuFJaOo/f11H3zwQQ488MBsuOGG3%2BmGJCwZRe3vzz//PMcdd1x%2B85vf1DnKSf3gFCwK'
     'cdxxx6VBgwYZPnx4zbLGjRvn888/X%2BD2M2fO/NZz%2Buev79WrV63lBx54YJI4R7yElsb%'
     '2BvvTSS/Pcc8/lnnvuSb9%2B/fKzn/0sF154YU477bT88Y9/dJ54CS1of39fjRs3zsyZM%2B'
     'ssn7/MNT%2BlszT291dNmzYt3bp1y7Rp03LnnXfWuTaEYi2N/X3xxRdnypQpOfvss5fYa7J8'
     'ESAUolGjRmnRokWt72to1apV5s6dm8mTJ9fa9vPPP8%2BUKVOy9tprf%2BNrzl//9dM05p8v'
     '7DqQ0lka%2B/vpp5/OOuusk44dO9Za3r1791RXVwvOElrQ/v6%2BWrVqlYkTJ9ZZXlVVlSTf'
     '%2BuuFpWdp7O/5Pv/88%2By77775//6//y933nln2rdvv8Tfg0WzpPf3J598kt///vf51a9%'
     '2BlY8//jjvvPNO3nnnnXz22Weprq7Ou%2B%2B%2Bmw8%2B%2BGCJvBfLLgFCIaZOnZrJkyfX'
     'uphwq622SpKMHDmy1rb//Oc/M2/evHTo0OEbX3P%2Bxcxf/86P%2BeeGu3CxdJbG/p49e3bm'
     'zJmzwOVJFriOYixof39fW221VaZPn17nyNbzzz%2BfJN/664WlZ2ns7ySZN29e%2BvTpk8ce'
     'eyx/%2B9vfsvPOOy/R12fxLOn9/dFHH2XatGk5//zzs%2BGGG9Y8brvttkyfPj1t2rTJr3/9'
     '6yXyXiy7BAhL1KxZszJ16tQ6y88555wkqXWni5/%2B9Kdp0aJFLr300lrbXnrppWnSpEn22m'
     'uvmmWffvppXn/99Vq3Bdx7773TsGHDXHPNNbVuK3jVVVclSbp06bJkPhQLVeT%2B7tixY95/'
     '//088cQTtZ5/ww03JPnfwGHpWZT9vSgW9vt7pZVWyp///OeaZdXV1bnsssvSunXr7LDDDov1'
     'Xnx3Re7vJOnXr19uuumm/PnPf87/%2BT//Z7Fem8VX1P5ea621cvvtt%2BeOO%2B6o9ejcuX'
     'MaNWqUO%2B64I6eccsrifxCWCy5CZ5EMGTIkH3/8cc1Rhrvuuivjxo1LkhxzzDGZMmVKttpq'
     'qxx44IHZeOONkyQPPvhg7r///uyxxx7Ze%2B%2B9a16rUaNGOeecc3LUUUflgAMOyG677Zan'
     'nnoq119/fQYOHJhmzZrVbHvbbbflF7/4Ra655poccsghSb74Q%2BzUU0/NGWecka5du2bvvf'
     'fO6NGjc9VVV%2BXAAw/M1ltvXdS/lrK1LO3vI488Mpdddlm6d%2B%2Befv36Zb311ssTTzyR'
     'v//979ltt91qbs/K4luS%2BztJ7r777owePTrJF0eqRo8end///vdJvgiMzTffPMmC9/c666'
     'yT/v3///buPybq%2Bo8D%2BPPz8ezu5A4BAQNT%2BeFBgizDi3ICAhnqZhoHQ/1DPc3U/nA5'
     'N9moNFAkJpCVOlzaYMVY5i%2BiLNMUKNOVzjFRV6ECRraGP2BCbIK8vn98x%2BXHO1QMD83n'
     'Y7uNe39e936/P%2B/PP7zufe/3ewXy8/PR2dkJq9WK8vJyHDlyBGVlZTwxuR88TM/7/fffR1'
     'FRESZOnAij0YjS0lJN3TabjWtB/qWH5XkbjUanunrifv75Z8ycOfPBDAA9XAbi9EN6dAUFBY'
     'miKKIoiqiqKqqqOv5ubGyUlpYWmTdvnlgsFvHw8BCDwSBRUVGSl5cnXV1dLuvctm2bPP3006'
     'LX68ViscgHH3zgFFNSUiKqqro8uXXz5s0SHh4uTzzxhIwePVrWrFnTa1vUNw/b8/71118lLS'
     '1NfHx8ZPDgwRIcHCwZGRnS0dHxQO7/cdPfz9tut/da363Ptrfn3d3dLe%2B%2B%2B64EBQWJ'
     'Xq%2BXqKgoKSsre%2BDj8Lh4mJ633W7XfObWV09/6N95mJ63K3a7/Z5PYadHnyJylyMxiYiI'
     'iIiI%2BgnXgBARERERkdswASEiIiIiIrdhAkJERERERG7DBISIiIiIiNyGCQgREREREbkNEx'
     'AiIiIiInIbJiBEREQPiN1uh9lsHuhuEBE9VJiAEBH1k9raWqSlpSEoKAhGoxFPPfUUkpOTsX'
     'nz5oHu2iOtqqoKqqpiz549A90Vlzo6OpCVlYXq6mqX13lqOxGRFhMQIqJ%2BcPToUVitVtTW'
     '1mLJkiXYsmULXnvtNaiqig8//HCgu0cPUHt7O9auXdtrAsLzfomItHQD3QEiov%2BC9evXw9'
     'vbG8ePH4enp6fm2uXLlweoV%2BROTDSIiO4NZ0CIiPrB%2BfPnERkZ6ZR8AICvr69TWWlpKS'
     'ZMmIAhQ4Zg2LBhmDt3LpqampziPvroI4SGhmLIkCF4/vnn8cMPPyAhIQGJiYmOmJKSEqiqio'
     'sXL2o%2B2/PTpe%2B//15T/tNPP2HatGnw8vKCh4cHEhIScPToUU1MVlYWVFXF%2BfPnYbfb'
     '4e3tDS8vLyxatAgdHR0u7ycmJgYeHh7w8fHB5MmTcfDgQU3MN998g7i4OJhMJnh6emLGjBk4'
     'e/asi9G8Py0tLVixYgVGjhwJg8EAi8WCDRs2aBKDhoYGqKqKwsJCx9gaDAbExMTgxIkTTnXu'
     '3LkTERERMBqNiIqKwt69e2G32xEcHOyoz9/fHwCQnZ0NVVWhqirWrl3rqENRFFy6dAmvvPIK'
     'zGYz/P39sWrVKnR3d/fbvRMRPUqYgBAR9YOgoCCcOHECZ86cuWvs%2BvXrsWDBAoSHh2Pjxo'
     '1YsWIFDh06hPj4eLS2tjriPv74YyxbtgyBgYHIz8/HpEmTMGvWLDQ1Nd33uoLDhw8jPj4ebW'
     '1tyMrKQm5uLlpaWpCUlITjx487xaenp6O9vR15eXlIT09HSUkJsrOzNTHZ2dmYP38%2B9Ho9'
     '1q1bh7Vr12LkyJGorKx0xHz66aeYMWMGPD09sWHDBqxevRpnz55FbGwsGhsb7%2BtebvX333'
     '9j8uTJKCsrg91ux6ZNmzBp0iRkZmZi5cqVTvFlZWUoKCjA66%2B/jpycHDQ0NMBms6Grq8sR'
     's2/fPsyePRt6vR55eXmw2WxYvHgxTp486Rh/f39/FBUVAQBsNhtKS0tRWloKm83mqKerqwtT'
     'p06Fn58fCgsLMXnyZEcCRET0WBIiIvrXDh48KDqdTnQ6nUycOFEyMjLkwIED0tnZqYlraGiQ'
     'QYMGSV5enqb89OnTMnjwYMnNzRURkRs3boi/v79ER0dr6ti2bZsoiiKJiYmOsuLiYlEURRob'
     'GzV1VlZWiqIoUl1dLSIi3d3dYrFYZPr06Zq4jo4OCQkJkeTkZEfZO%2B%2B8I4qiyOLFizWx'
     'NptNfH19He/r6upEVVVJTU3tdWyuX78uXl5esnTpUk35X3/9JV5eXrJkyZJeP3vrfezevbvX'
     'mHXr1onJZJJz585pyjMzM0Wn08nvv/8uIiL19fWiKIr4%2BflJS0uLI66iokIURZGvvvrKUR'
     'YVFSWjRo2S9vZ2R1l1dbUoiiLBwcGOsubmZlEURbKzs536tWDBAlEURXJycjTl0dHRYrVa73'
     'jfRET/VZwBISLqB1OmTMGxY8cwc%2BZMnDp1Cvn5%2BZg6dSpGjBiBL7/80hG3Z88eiAjS0t'
     'Jw%2BfJlx2v48OEYM2aMY9bgxIkTaG5uxrJly6DT/bNcz263Y%2BjQoffVx5qaGpw7dw5z58'
     '7VtN3W1oakpCSnn2oBwLJlyzTvY2NjceXKFbS1tQEAysvLISJYs2ZNr%2B0ePHgQra2tmDNn'
     'jqZdVVURExOjmSm5Xzt37kR8fDy8vLw0bbz44ou4efOm073Nnj1bM46xsbEAgPr6egDApUuX'
     'cPr0acyfPx9DhgxxxMXHxyMqKqrP/XM1jhcuXOhzPURE/wVchE5E1E%2BsVit2796Nrq4u1N'
     'TUYO/evdi4cSPS0tJQU1ODsWPHoq6uDiICi8Xisg69Xg8Ajp8l3R6n0%2BkQEhJyX/2rq6sD'
     'ACUhOtIAAAX9SURBVCxYsMDldUVR0NraqvnHfNSoUZoYb29vAMC1a9dgMplw/vx5qKqKiIiI'
     'u7ablJTk8vr9JlS3t1FbWws/Pz%2Bna4qioLm5WVN2p/sC/hn/MWPGONUXGhqKmpqae%2B6b'
     '0WjEsGHDnNrraYuI6HHDBISIqJ/pdDpYrVZYrVaEhYVh4cKF2LVrF1avXo3u7m4oioL9%2B/'
     'dj0KBBTp81mUx3rV9u222pt/UgN2/e1LzvWfRcUFCA8ePHu/yMh4eH5r2rPrrqw530tFtaWo'
     'onn3zS6fqtMzz3S0SQnJyMjIwMl9dvT%2BT6477ularyxwZERLdiAkJE9ABNmDABAPDnn38C'
     '%2BP%2B35yKCoKCgXmdBAGD06NEAgN9%2B%2Bw0JCQmO8s7OTtTX1%2BPZZ591lPV8e9/S0q'
     'L5Zv/2xd2hoaEAALPZ3OtsRF%2BFhoaiu7sbZ86cwTPPPOMypmcWwc/Pr9/addWP69ev91v9'
     'PePfM3tzq3Pnzmne86BBIqK%2B4dcyRET9oLd1DF9//TUAIDw8HACQmpqKQYMGOe0kBfz/2/'
     'erV68CAJ577jn4%2Bflh69at6OzsdMSUlJRodsoC/kksbj0I7%2BbNm067LFmtVoSGhqKgoA'
     'Dt7e1O7d/%2BM6V7kZKS4th2trfZg6lTp8LT0xO5ubmaXaZ69Mc5Kenp6Th27BgOHDjgdK2l'
     'pcVpNuhuAgMDMW7cOHzyySeasaqursbp06c1sT1rRHr7SRUTFCIiLc6AEBH1g%2BXLl6Ojow'
     'MpKSkIDw/HjRs3cPToUXz%2B%2BecIDg7GwoULAQAhISHIyclBZmYmGhoaMGvWLJjNZtTX16'
     'O8vBxLly7FypUrodPpkJOTg6VLlyIpKQnp6emor69HSUmJ0xqQyMhIvPDCC8jMzMTVq1fh7e'
     '2Nzz77zOmfbkVRsH37dkyfPh2RkZFYuHAhAgMD8ccff6CyshJDhw5FRUVFn%2B47NDQUb731'
     'FtatW4e4uDikpKRAr9fj%2BPHjGDFiBHJzc2E2m1FUVIR58%2BYhOjoac%2BbMga%2BvLy5e'
     'vIh9%2B/YhNjYWmzZtumtbu3btcnluiN1ux6pVq1BRUYEZM2bAbrcjOjoa7e3tqK2txe7du9'
     'HY2AgfH58%2B3Vtubi5mzZqFSZMmwW6349q1a9iyZQvGjRunSUqMRiMiIiKwY8cOhIWFwdvb'
     'G1FRUYiMjATAAwqJiJwM0O5bRET/Kfv375dXX31Vxo4dK2azWfR6vYSFhckbb7whzc3NTvF7'
     '9uyRuLg4MZlMYjKZJCIiQpYvXy51dXWauKKiIgkJCRGDwSAxMTFy5MgRSUhI0GzDKyJy4cIF'
     'eemll8RgMEhAQIC8/fbb8t1334mqqo5teHvU1NRIamqq%2BPr6isFgkODgYJkzZ45UVlY6Yr'
     'KyskRVVbly5Yrms8XFxaKqqtOWv8XFxRIdHS0Gg0F8fHwkMTFRDh06pImpqqqSadOmiZeXlx'
     'iNRrFYLLJo0SI5efLkHce2qqpKFEURVVVFURTNS1VV%2BfHHH0VEpK2tTd58802xWCyi1%2B'
     'vFz89PYmNj5b333nNsZdyzDW9hYaFTO6620t2xY4eMHTtW9Hq9jBs3Tr744gtJTU2ViIgITd'
     'yxY8fEarWKXq8XVVUd9djtdjGbzU5t9YwvEdHjSBHhVzNERI%2BShIQEqKqKw4cPD3RXHkvj'
     'x4/H8OHD8e233w50V4iIHklcA0JERORCV1eX05qVqqoqnDp1SrMxABER9Q3XgBARPYI4ef3g'
     'NTU1YcqUKZg3bx4CAgLwyy%2B/YOvWrQgICHA6WJCIiO4dExAiokeMoijcWckNfHx8YLVasX'
     '37djQ3N8NkMuHll19GXl6eY%2BtjIiLqO64BISIiIiIit%2BEaECIiIiIichsmIERERERE5D'
     'ZMQIiIiIiIyG2YgBARERERkdswASEiIiIiIrdhAkJERERERG7DBISIiIiIiNyGCQgREREREb'
     'kNExAiIiIiInIbJiBEREREROQ2TECIiIiIiMhtmIAQEREREZHbMAEhIiIiIiK3YQJCRERERE'
     'RuwwSEiIiIiIjchgkIERERERG5zf8AsP74gAK9NuMAAAAASUVORK5CYII%3D'
     '"/>')]

if __name__ == '__main__':
    main()
