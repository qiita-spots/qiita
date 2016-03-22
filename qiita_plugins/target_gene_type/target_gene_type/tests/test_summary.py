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

        self.qclient = QiitaClient('https://test_server.com/', 'client_id',
                                   'client_secret')
        # creating files
        self.out_dir = mkdtemp()
        gz_file = join(self.out_dir, "file1.fastq.gz")
        with GzipFile(gz_file, mode='w', mtime=1) as fh:
            fh.write(READS)
        fastq_file = join(self.out_dir, "file1.fastq")
        with open(fastq_file, mode='w') as fh:
            fh.write(READS)
        self.filepaths = (
            '[["%s", "raw_forward_seqs"], ["%s", "raw_barcodes"]]' % (
                gz_file, fastq_file))
        self.artifact_id = 4
        self.parameters = {'input_data': self.artifact_id}

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
        httpretty_url = ("https://test_server.com/qiita_db/artifacts/"
                         "%s/filepaths/" % self.artifact_id)
        httpretty.register_uri(
            httpretty.GET, httpretty_url,
            body=('{"success": true, "error": "", '
                  '"filepaths": %s}' % self.filepaths))
        httpretty_url = ("https://test_server.com/qiita_db/artifacts/"
                         "%s/type/" % self.artifact_id)
        httpretty.register_uri(
            httpretty.GET, httpretty_url,
            body=('{"success": true, "error": "", "type": "FASTQ"}'))
        httpretty_url = ("https://test_server.com/qiita_db/artifacts/"
                         "%s/filepaths/" % self.artifact_id)
        httpretty.register_uri(
            httpretty.PATCH, httpretty_url,
            body='{"success": true, "error": ""}')
        obs, html = generate_html_summary(self.qclient, 'job-id',
                                          self.parameters,
                                          self.out_dir, True)

        # asserting reply
        self.assertItemsEqual(obs, {"success": True, "error": ""})

        # asserting content of html
        self.assertItemsEqual(html, EXP_HTML)

    @httpretty.activate
    def test_generate_html_summary_error(self):
        httpretty_url = ("https://test_server.com/qiita_db/artifacts/"
                         "%s/filepaths/" % self.artifact_id)
        httpretty.register_uri(
            httpretty.GET, httpretty_url,
            body=('{"success": true, "error": "", '
                  '"filepaths": %s}' % self.filepaths))
        httpretty_url = ("https://test_server.com/qiita_db/artifacts/"
                         "%s/type/" % self.artifact_id)
        httpretty.register_uri(
            httpretty.GET, httpretty_url,
            body=('{"success": true, "error": "", "type": "FASTQ"}'))
        with self.assertRaises(ValueError):
            generate_html_summary(self.qclient, 'job-id', self.parameters,
                                  self.out_dir, True)


class SummaryTestsDemux(TestCase):
    @httpretty.activate
    def setUp(self):
        # Registewr the URIs for the QiitaClient
        httpretty.register_uri(
            httpretty.POST,
            "https://test_server.com/qiita_db/authenticate/",
            body='{"access_token": "token", "token_type": "Bearer", '
                 '"expires_in": "3600"}')

        self.qclient = QiitaClient('https://test_server.com/', 'client_id',
                                   'client_secret')
        # creating files
        self.out_dir = mkdtemp()
        self.filepaths = (
            '[["test_file", "raw_forward_seqs"], '
            '["%s/test_data/101_seqs.demux", "preprocessed_demux"]]' %
            dirname(__file__))
        self.artifact_id = 4
        self.parameters = {'input_data': self.artifact_id}

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
        httpretty_url = ("https://test_server.com/qiita_db/artifacts/"
                         "%s/filepaths/" % self.artifact_id)
        httpretty.register_uri(
            httpretty.GET, httpretty_url,
            body=('{"success": true, "error": "", '
                  '"filepaths": %s}' % self.filepaths))
        httpretty_url = ("https://test_server.com/qiita_db/artifacts/"
                         "%s/type/" % self.artifact_id)
        httpretty.register_uri(
            httpretty.GET, httpretty_url,
            body=('{"success": true, "error": "", "type": "Demultiplexed"}'))
        httpretty_url = ("https://test_server.com/qiita_db/artifacts/"
                         "%s/filepaths/" % self.artifact_id)
        httpretty.register_uri(
            httpretty.PATCH, httpretty_url,
            body='{"success": true, "error": ""}')
        obs, html = generate_html_summary(self.qclient, 'job-id',
                                          self.parameters,
                                          self.out_dir, True)

        # asserting reply
        self.assertItemsEqual(obs, {"success": True, "error": ""})

        # asserting content of html
        self.assertItemsEqual(html, EXP_HTML_DEMUX)

    @httpretty.activate
    def test_generate_html_summary_no_demux(self):
        httpretty_url = ("https://test_server.com/qiita_db/artifacts/"
                         "%s/filepaths/" % self.artifact_id)
        httpretty.register_uri(
            httpretty.GET, httpretty_url,
            body=('{"success": true, "error": "", '
                  '"filepaths": [["fps", "fps_type"]]}'))
        httpretty_url = ("https://test_server.com/qiita_db/artifacts/"
                         "%s/type/" % self.artifact_id)
        httpretty.register_uri(
            httpretty.GET, httpretty_url,
            body=('{"success": true, "error": "", "type": "Demultiplexed"}'))
        httpretty_url = ("https://test_server.com/qiita_db/artifacts/"
                         "%s/filepaths/" % self.artifact_id)
        with self.assertRaises(ValueError):
            generate_html_summary(self.qclient, 'job-id', self.parameters,
                                  self.out_dir, True)


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
    '<h3>file1.fastq.gz (raw_forward_seqs)</h3>',
    '<b>MD5:</b>: eb3203ab33442b168c274b32c5624961</br>',
    '<p style="font-family:\'Courier New\', Courier, monospace;font-size:10;'
    '">@MISEQ03:123:000000000-A40KM:1:1101:14149:1572 1:N:0:TCCACAGGAGT\n<br'
    '/>GGGGGGTGCCAGCCGCCGCGGTAATACGGGGGGGGCAAGCGTTGTTCGGAATTACTGGGCGTAAAGGGC'
    'TCGTAGGCGGCCCACTAAGTCAGACGTGAAATCCCTCGGCTTAACCGGGGAACTGCGTCTGATACTGGATG'
    'GCTTGAGGTTGGGAGAGGGATGCGGAATTCCAGGTGTAGCGGTGAAATGCGTAGATATCTGGAGGAACACC'
    'GGTGGCGAAGGCGGCATCCTGGACCAATTCTGACGCTGAG\n<br/>+\n<br/>CCCCCCCCCFFFGGGG'
    'GGGGGGGGHHHHGGGGGFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF-.;FFF'
    'FFFFFF9@EFFFFFFFFFFFFFFFFFFF9CFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFBFFFFFFFFF'
    'FFFFECFFFEFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFBFFFFFFFFFFFFFFFFF;CDEA@FFFF'
    'FFFFFFFFFFFFFFFFFFFFFF\n<br/>@MISEQ03:123:000000000-A40KM:1:1101:14170:'
    '1596 1:N:0:TCCACAGGAGT\n<br/>ATGGCGTGCCAGCAGCCGCGGTAATACGGAGGGGGCTAGCGT'
    'TGTTCGGAATTACTGGGCGTAAAGCGCACGTAGGCGGCTTTGTAAGTTAGAGGTGAAAGCCCGGGGCTCAA'
    'CTCCGGAACTGCCTTTAAGACTGCATCGCTAGAATTGTGGAGAGGTGAGTGGAATTCCGAGTGTAGAGGTG'
    'AAATTCGTAGATATTCGGAAGAACACCAGTGGCGAAGGCGACTCACTGGACACATATTGACGCTGAG\n<b'
    'r/>+\n<br/>CCCCCCCCCCFFGGGGGGGGGGGGGHHHGGGGGGGGGHHHGGGGGHHGGGGGHHHHHHHH'
    'GGGGHHHGGGGGHHHGHGGGGGHHHHHHHHGHGHHHHHHGHHHHGGGGGGHHHHHHHGGGGGHHHHHHHHH'
    'GGFGGGGGGGGGGGGGGGGGGGGGGGGFGGFFFFFFFFFFFFFFFFFF0BFFFFFFFFFFFFEFFFFFFFF'
    'FFFFFFFFFFFFFFFFFFFDFAFCFFFFFFFFFFFFFFFFFFBDFFFFF\n<br/>@MISEQ03:123:00'
    '0000000-A40KM:1:1101:14740:1607 1:N:0:TCCACAGGAGT\n<br/>AGTGTGTGCCAGCAG'
    'CCGCGGTAATACGTAGGGTGCGAGCGTTAATCGGAATTACTGGGCGTAAAGCGTGCGCAGGCGGTTCGTTG'
    'TGTCTGCTGTGAAATCCCCGGGCTCAACCTGGGAATGGCAGTGGAAACTGGCGAGCTTGAGTGTGGCAGAG'
    'GGGGGGGGAATTCCGCGTGTAGCAGTGAAATGCGTAGAGATGCGGAGGAACACCGATGGCGAAGGCAACCC'
    'CCTGGGATAATATTTACGCTCAT\n<br/>+\n</p><hr/>',
    '<h3>file1.fastq (raw_barcodes)</h3>',
    '<b>MD5:</b>: 97328e860ef506f7b029997b12bf9885</br>',
    '<p style="font-family:\'Courier New\', Courier, monospace;font-size:10;'
    '">@MISEQ03:123:000000000-A40KM:1:1101:14149:1572 1:N:0:TCCACAGGAGT\n<br'
    '/>GGGGGGTGCCAGCCGCCGCGGTAATACGGGGGGGGCAAGCGTTGTTCGGAATTACTGGGCGTAAAGGGC'
    'TCGTAGGCGGCCCACTAAGTCAGACGTGAAATCCCTCGGCTTAACCGGGGAACTGCGTCTGATACTGGATG'
    'GCTTGAGGTTGGGAGAGGGATGCGGAATTCCAGGTGTAGCGGTGAAATGCGTAGATATCTGGAGGAACACC'
    'GGTGGCGAAGGCGGCATCCTGGACCAATTCTGACGCTGAG\n<br/>+\n<br/>CCCCCCCCCFFFGGGG'
    'GGGGGGGGHHHHGGGGGFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF-.;FFF'
    'FFFFFF9@EFFFFFFFFFFFFFFFFFFF9CFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFBFFFFFFFFF'
    'FFFFECFFFEFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFBFFFFFFFFFFFFFFFFF;CDEA@FFFF'
    'FFFFFFFFFFFFFFFFFFFFFF\n<br/>@MISEQ03:123:000000000-A40KM:1:1101:14170:'
    '1596 1:N:0:TCCACAGGAGT\n<br/>ATGGCGTGCCAGCAGCCGCGGTAATACGGAGGGGGCTAGCGT'
    'TGTTCGGAATTACTGGGCGTAAAGCGCACGTAGGCGGCTTTGTAAGTTAGAGGTGAAAGCCCGGGGCTCAA'
    'CTCCGGAACTGCCTTTAAGACTGCATCGCTAGAATTGTGGAGAGGTGAGTGGAATTCCGAGTGTAGAGGTG'
    'AAATTCGTAGATATTCGGAAGAACACCAGTGGCGAAGGCGACTCACTGGACACATATTGACGCTGAG\n<b'
    'r/>+\n<br/>CCCCCCCCCCFFGGGGGGGGGGGGGHHHGGGGGGGGGHHHGGGGGHHGGGGGHHHHHHHH'
    'GGGGHHHGGGGGHHHGHGGGGGHHHHHHHHGHGHHHHHHGHHHHGGGGGGHHHHHHHGGGGGHHHHHHHHH'
    'GGFGGGGGGGGGGGGGGGGGGGGGGGGFGGFFFFFFFFFFFFFFFFFF0BFFFFFFFFFFFFEFFFFFFFF'
    'FFFFFFFFFFFFFFFFFFFDFAFCFFFFFFFFFFFFFFFFFFBDFFFFF\n<br/>@MISEQ03:123:00'
    '0000000-A40KM:1:1101:14740:1607 1:N:0:TCCACAGGAGT\n<br/>AGTGTGTGCCAGCAG'
    'CCGCGGTAATACGTAGGGTGCGAGCGTTAATCGGAATTACTGGGCGTAAAGCGTGCGCAGGCGGTTCGTTG'
    'TGTCTGCTGTGAAATCCCCGGGCTCAACCTGGGAATGGCAGTGGAAACTGGCGAGCTTGAGTGTGGCAGAG'
    'GGGGGGGGAATTCCGCGTGTAGCAGTGAAATGCGTAGAGATGCGGAGGAACACCGATGGCGAAGGCAACCC'
    'CCTGGGATAATATTTACGCTCAT\n<br/>+\n</p><hr/>']

EXP_HTML_DEMUX = [
    '<h3>Features</h3>',
    '<b>Total</b>: 49', '<br/>',
    '<b>Max</b>: 151', '<br/>',
    '<b>Mean</b>: 151', '<br/>',
    '<b>Standard deviation</b>: 151', '<br/>',
    '<b>Median</b>: 0', '<br/>',
    ('<img src = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAyAAAAJYCAYAAA'
     'CadoJwAAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAPYQAAD2EBqD%2BnaQAAIABJREFUeJzt'
     '3X%2BUlnWd//HXjOIwCIaOWIOYGYWISYhA4inOKl9aLNAtRRbXEHbTs6kIqcf8lZ49tmCBSR'
     '1OltWqrWYrmqamtoZKuZWQoWstFLul7uBQEJojDIh6f/8wZ50G0cGZzz3K43HOfQ5e13Xf9/'
     'vmM04%2Bu6/rvmsqlUolAAAABdRWewAAAGDnIUAAAIBiBAgAAFCMAAEAAIoRIAAAQDECBAAA'
     'KEaAAAAAxQgQAACgGAECAAAUI0AAAIBiBAgAAFCMAAEAAIoRIAAAQDECBAAAKEaAAAAAxQgQ'
     'AACgGAECAAAUI0AAAIBiBAgAAFCMAAEAAIoRIAAAQDECBAAAKEaAAAAAxQgQAACgGAECAAAU'
     'I0AAAIBiBAgAAFCMAAEAAIoRIAAAQDECBAAAKEaAAAAAxQgQAACgGAECAAAUI0AAAIBiBAgA'
     'AFCMAAEAAIoRIAAAQDECBAAAKEaAAAAAxQgQAACgGAECAAAUI0AAAIBiBAgAAFCMAAEAAIoR'
     'IAAAQDECBAAAKEaAAAAAxQgQAACgGAECAAAUI0AAAIBiBAgAAFCMAOmk%2B%2B%2B/P7W1td'
     'u8LVu2rN2xK1euzMSJE9OvX780NDRk%2BvTpWb9%2BfZUmBwCA6tu12gO8Wc2ePTujR49ut2'
     '3w4MFtf25qasq4ceOy5557Zt68eWlpacmCBQvy6KOPZtmyZenVq1fpkQEAoOoEyA760Ic%2B'
     'lI9//OOvun/u3LlpbW3NihUrMmjQoCTJmDFjMmHChFxzzTU55ZRTSo0KAAA9hlOwdlClUklL'
     'S0uef/75be6/%2BeabM2nSpLb4SJLx48dnyJAhufHGG0uNCQAAPYoA2UEzZ87M2972ttTX1%'
     '2Beoo47KQw891LZvzZo1WbduXUaNGtXhfqNHj86KFStKjgoAAD2GU7A6qa6uLscff3w%2B8p'
     'GPZO%2B9986vfvWrLFiwIB/60Ifyk5/8JCNGjEhzc3OSpLGxscP9Gxsbs2HDhmzdutV1IAAA'
     '7HQESCeNHTs2Y8eObfvnSZMm5fjjj8/w4cNz/vnn56677kpra2uSl2LlL/Xu3TtJ0traKkAA'
     'ANjpCJAuMHjw4BxzzDG55ZZbUqlUUl9fnyTZsmVLh2M3b96cJG3H/KXm5ua2d1AAAOh5Ghsb'
     't3mmC6%2BPAOki%2B%2B23X5577rls3Lix7QdyWyHR3NychoaGbb770dzcnKOOOiqrVq3q9n'
     'kBANgxQ4cOzb333itCdpAA6SK//e1vU19fn759%2B6Zv374ZMGBAli9f3uG4ZcuWZcSIEdt8'
     'jObm5qxatSrXXXddDjrooO4euUeZM2dOFi5cWO0xKMR671ys987Feu9cdsb1XrlyZU466aQ0'
     'NzcLkB0kQDpp3bp1GTBgQLttjzzySG677bZ89KMfbdt23HHH5dprr01TU1PbR/EuWbIkq1ev'
     'ztlnn73d5zjooIMycuTIrh%2B%2BB%2Bvfv/9O95p3ZtZ752K9dy7We%2BdivdkRAqSTpk6d'
     'mj59%2BmTs2LHZZ5998l//9V%2B56qqr0rdv31x22WVtx11wwQVZvHhxjjzyyMyePTstLS2Z'
     'P39%2Bhg8fnpkzZ1bxFQAAQPX4HpBO%2BtjHPpb169fniiuuyOmnn57Fixfn%2BOOPz89//v'
     'MceOCBbccNGjQoS5cuzeDBg3PeeedlwYIFmTRpUu655x6ffgUAwE7LOyCdNGvWrMyaNet1HT'
     'ts2LDcfffd3TwRAAC8eXgHhB5h2rRp1R6Bgqz3zsV671ys987FerMjaiqVSqXaQ/CSX/ziFz'
     'nssMPy0EMPuaALAKAH8t9rb5x3QAAAgGJcAwJAt1q9enVaWlqqPQZAl1i5cmW1R3jTEyAAdJ'
     'vVq1dnyJAh1R4DgB5EgADQbf7vnY/rkhxUzVEAusjKJCdVe4g3NQECQAEHJXGxJgAuQgcAAA'
     'oSIAAAQDECBAAAKEaAAAAAxQgQAACgGAECAAAUI0AAAIBiBAgAAFCMAAEAAIoRIAAAQDECBA'
     'AAKEaAAAAAxQgQAACgGAECAAAUI0AAAIBiBAgAAFCMAAEAAIoRIAAAQDECBAAAKEaAAAAAxQ'
     'gQAACgGAECAAAUI0AAAIBiBAgAAFCMAAEAAIoRIAAAQDECBAAAKEaAAAAAxQgQAACgGAECAA'
     'AUI0AAAIBiBAgAAFCMAAEAAIoRIAAAQDECBAAAKEaAAAAAxQgQAACgGAECAAAUI0AAAIBiBA'
     'gAAFCMAAEAAIoRIAAAQDECBAAAKEaAAAAAxQgQAACgGAECAAAUI0AAAIBiBAgAAFCMAAEAAI'
     'oRIAAAQDECBAAAKEaAAAAAxQgQAACgGAECAAAUI0AAAIBiBAgAAFCMAAEAAIoRIAAAQDECBA'
     'AAKEaAAAAAxQgQAACgGAECAAAUI0AAAIBiBAgAAFCMAAEAAIoRIAAAQDECBAAAKEaAAAAAxQ'
     'gQAACgGAECAAAUI0AAAIBiBAgAAFCMAAEAAIoRIAAAQDECBAAAKEaAvEH//M//nNra2hxyyC'
     'Ed9q1cuTITJ05Mv3790tDQkOnTp2f9%2BvVVmBIAAHqGXas9wJtZU1NT5s6dm9133z01NTUd'
     '9o0bNy577rln5s2bl5aWlixYsCCPPvpoli1bll69elVpagAAqB4B8gacc845OeKII/L88893'
     'eGdj7ty5aW1tzYoVKzJo0KAkyZgxYzJhwoRcc801OeWUU6oxMgAAVJVTsHbQj370o9x8881Z'
     'uHBhKpVKh3dAbr755kyaNKktPpJk/PjxGTJkSG688cbS4wIAQI8gQHbACy%2B8kFmzZuWUU0'
     '7JwQcf3GH/mjVrsm7duowaNarDvtGjR2fFihUlxgQAgB7HKVg74Ktf/WqeeOKJ3Hvvvdvc39'
     'zcnCRpbGzssK%2BxsTEbNmzI1q1bXQcCAMBOxzsgnfTHP/4xF198cS6%2B%2BOI0NDRs85jW'
     '1tYkSV1dXYd9vXv3bncMAADsTARIJ1100UXZe%2B%2B9M2vWrFc9pr6%2BPkmyZcuWDvs2b9'
     '7c7hgAANiZOAWrE1avXp2vf/3rWbhwYZqamtq2b968Oc8991wef/zx7LHHHm2nXr18KtYrNT'
     'c3p6GhYbunX82ZMyf9%2B/dvt23atGmZNm1aF70SAABe2w1/vr3S09UY5C1FgHTCmjVr8uKL'
     'L%2BbMM8/MmWee2WH/AQcckDlz5uSLX/xiBgwYkOXLl3c4ZtmyZRkxYsR2n2fhwoUZOXJkl8'
     '0NAMCOmPbn2yv9IslhVZjlrUOAdMIhhxySW265pd1H7lYqlVx00UV59tln86UvfSmDBw9Okh'
     'x33HG59tpr09TU1PZRvEuWLMnq1atz9tlnV2V%2BAACoNgHSCQ0NDTn22GM7bL/iiiuSJMcc'
     'c0zbtgsuuCCLFy/OkUcemdmzZ6elpSXz58/P8OHDM3PmzGIzAwBAT%2BIi9C5QU1PT4YsIBw'
     '0alKVLl2bw4ME577zzsmDBgkyaNCn33HOPj98FAGCn5R2QLnDfffdtc/uwYcNy9913F54GAA'
     'B6Lu%2BAAAAAxQgQAACgGAECAAAUI0AAAIBiBAgAAFCMAAEAAIoRIAAAQDECBAAAKEaAAAAA'
     'xQgQAACgGAECAAAUI0AAAIBiBAgAAFCMAAEAAIoRIAAAQDECBAAAKEaAAAAAxQgQAACgGAEC'
     'AAAUI0AAAIBiBAgAAFCMAAEAAIoRIAAAQDECBAAAKEaAAAAAxQgQAACgGAECAAAUI0AAAIBi'
     'BAgAAFCMAAEAAIoRIAAAQDECBAAAKEaAAAAAxQgQAACgGAECAAAUI0AAAIBiBAgAAFCMAAEA'
     'AIoRIAAAQDECBAAAKEaAAAAAxQgQAACgGAECAAAUI0AAAIBiBAgAAFCMAAEAAIoRIAAAQDEC'
     'BAAAKEaAAAAAxQgQAACgGAECAAAUI0AAAIBiBAgAAFCMAAEAAIoRIAAAQDECBAAAKEaAAAAA'
     'xQgQAACgGAECAAAUI0AAAIBiBAgAAFCMAAEAAIoRIAAAQDECBAAAKEaAAAAAxQgQAACgGAEC'
     'AAAUI0AAAIBiBAgAAFCMAAEAAIoRIAAAQDECBAAAKEaAAAAAxQgQAACgGAECAAAUI0AAAIBi'
     'BAgAAFCMAAEAAIoRIAAAQDECBAAAKEaAAAAAxQgQAACgGAHSSb/61a8yZcqUDB48OLvvvnsa'
     'GhpyxBFH5Prrr%2B9w7MqVKzNx4sT069cvDQ0NmT59etavX1%2BFqQEAoGfYtdoDvNk88cQT'
     'efbZZzNjxowMHDgwmzZtyk033ZRPfOITeeyxx3LhhRcmSZqamjJu3LjsueeemTdvXlpaWrJg'
     'wYI8%2BuijWbZsWXr16lXlVwIAAOUJkE46%2Buijc/TRR7fbdvrpp%2Bewww7LVVdd1RYgc%'
     '2BfOTWtra1asWJFBgwYlScaMGZMJEybkmmuuySmnnFJ8dgAAqDanYHWB2traDBo0qN27Gjff'
     'fHMmTZrUFh9JMn78%2BAwZMiQ33nhjNcYEAICq8w7IDtq0aVM2bdqUP/3pT7ntttvygx/8II'
     'sWLUqSrFmzJuvWrcuoUaM63G/06NG56667So8LAAA9ggDZQWeddVauuuqqJMmuu%2B6aL3/5'
     'yzn11FOTJM3NzUmSxsbGDvdrbGzMhg0bsnXrVteBAACw0xEgO%2BjTn/50TjjhhDz55JO5/v'
     'rrc8YZZ6S%2Bvj4nn3xyWltbkyR1dXUd7te7d%2B8kSWtrqwABAGCnI0B20IEHHpgDDzwwSX'
     'LSSSflr//6rzNnzpxMnTo19fX1SZItW7Z0uN/mzZuTpO0YAADYmQiQLnLcccflnnvuyapVq9'
     'pOvXr5VKxXam5uTkNDw3bf/ZgzZ0769%2B/fbtu0adMybdq0rh0aAIDtuOHPt1d6uhqDvKUI'
     'kC7y8mlXtbW12XfffTNgwIAsX768w3HLli3LiBEjtvtYCxcuzMiRI7tlTgAAXq9pf7690i%2'
     'BSHFaFWd46fAxvJ61bt67Dtq1bt%2BZb3/pWGhoacvDBByd56R2RO%2B64I01NTW3HLVmyJK'
     'tXr86UKVOKzQsAAD2Jd0A66dRTT01LS0vGjRuXgQMHZu3atbn%2B%2Buvzm9/8JldffXV22W'
     'WXJMkFF1yQxYsX58gjj8zs2bPT0tKS%2BfPnZ/jw4Zk5c2aVXwUAAFSHAOmkv/3bv803v/nN'
     'XHnllfnjH/%2BYPfbYIx/4wAeyaNGijB8/vu24QYMGZenSpTnrrLNy3nnnpa6uLpMmTcrll1'
     '/u068AANhpCZBOmjp1aqZOnfq6jh02bFjuvvvubp4IAADePFwDAgAAFCNAAACAYgQIAABQjA'
     'ABAACKESAAAEAxAgQAAChGgAAAAMUIEAAAoBgBAgAAFCNAAACAYgQIAABQjAABAACKESAAAE'
     'AxAgQAAChGgAAAAMUIEAAAoBgBAgAAFCNAAACAYgQIAABQjAABAACKESAAAEAxAgQAAChGgA'
     'AAAMUIEAAAoBgBAgAAFCNAAACAYgQIAABQjAABAACKESAAAEAxAgQAAChGgAAAAMUIEAAAoB'
     'gBAgAAFCNAAACAYgQIAABQjAABAACKESAAAEAxAgQAAChGgAAAAMUIEAAAoBgBAgAAFCNAAA'
     'CAYgQIAABQjAABAACKESAAAEAxAgQAAChGgAAAAMUIEAAAoBgBAgAAFCNAAACAYgQIAABQjA'
     'ABAACKESAAAEAxAgQAAChGgAAAAMUIEAAAoBgBAgAAFCNAAACAYgQIAABQjAABAACKESAAAE'
     'AxAgQAAChGgAAAAMUIEAAAoBgBAgAAFCNAAACAYgQIAABQjAABAACKESAAAEAxAgQAAChGgA'
     'AAAMUIEAAAoBgBAgAAFCNAAACAYgQIAABQjAABAACKESAAAEAxAgQAAChGgAAAAMUIEAAAoB'
     'gBAgAAFCNAAACAYgRIJy1fvjxnnHFGDj744PTt2zf7779/pk6dmtWrV3c4duXKlZk4cWL69e'
     'uXhoaGTJ8%2BPevXr6/C1AAA0DPsWu0B3mw%2B//nP56c//WmmTJmS4cOHp7m5OYsWLcrIkS'
     'Pzs5/9LAcffHCSpKmpKePGjcuee%2B6ZefPmpaWlJQsWLMijjz6aZcuWpVevXlV%2BJQAAUJ'
     '4A6aSzzz47o0ePzq67/t9f3dSpU3PIIYfksssuy7/%2B678mSebOnZvW1tasWLEigwYNSpKM'
     'GTMmEyZMyDXXXJNTTjmlKvMDAEA1OQWrk8aOHdsuPpLkPe95T4YNG5ZVq1a1bbv55pszadKk'
     'tvhIkvHjx2fIkCG58cYbi80LAAA9iQDpApVKJb///e%2Bz9957J0nWrFmTdevWZdSoUR2OHT'
     '16dFasWFF6RAAA6BEESBe4/vrr8%2BSTT2bq1KlJkubm5iRJY2Njh2MbGxuzYcOGbN26teiM'
     'AADQEwiQN2jVqlU5/fTTc8QRR%2BTkk09OkrS2tiZJ6urqOhzfu3fvdscAAMDORIC8AWvXrs'
     '1HP/rR7LnnnrnppptSU1OTJKmvr0%2BSbNmypcN9Nm/e3O4YAADYmfgUrB30pz/9KUcffXSe'
     'eeaZ/PjHP8473vGOtn0vn3r18qlYr9Tc3JyGhobtfgzvnDlz0r9//3bbpk2blmnTpnXR9AAA'
     'vLYb/nx7paerMchbigDZAZs3b87kyZPz3//93/nhD3%2BYoUOHttu/7777ZsCAAVm%2BfHmH'
     '%2By5btiwjRozY7uMvXLgwI0eO7NKZAQDorGl/vr3SL5IcVoVZ3jqcgtVJL7zwQqZOnZoHH3'
     'wwixcvzgc%2B8IFtHnfcccfljjvuSFNTU9u2JUuWZPXq1ZkyZUqpcQEAoEfxDkgnnX322bn9'
     '9tszefLkrF%2B/Ptddd127/SeddFKS5IILLsjixYtz5JFHZvbs2Wlpacn8%2BfMzfPjwzJw5'
     'sxqjAwBA1QmQTnrkkUdSU1OT22%2B/Pbfffnu7fTU1NW0BMmjQoCxdujRnnXVWzjvvvNTV1W'
     'XSpEm5/PLLt3v9BwAAvJUJkE667777Xvexw4YNy913392N0wAAwJuLa0AAAIBiBAgAAFCMAA'
     'EAAIoRIAAAQDECBAAAKEaAAAAAxQgQAACgGAECAAAUI0AAAIBiBAgAAFCMAAEAAIoRIAAAQD'
     'ECBAAAKEaAAAAAxQgQAACgGAECAAAUI0AAAIBiBAgAAFCMAAEAAIoRIAAAQDECBAAAKEaAAA'
     'AAxQgQAACgGAECAAAUI0AAAIBiBAgAAFCMAAEAAIoRIAAAQDECBAAAKEaAAAAAxQgQAACgGA'
     'ECAAAUI0AAAIBiBAgAAFCMAAEAAIoRIAAAQDECBAAAKEaAAAAAxQgQAACgGAECAAAUI0AAAI'
     'BiBAgAAFCMAAEAAIoRIAAAQDECBAAAKEaAAAAAxQgQAACgGAECAAAUI0AAAIBiBAgAAFCMAA'
     'EAAIoRIAAAQDECBAAAKEaAAAAAxQgQAACgGAECAAAUI0AAAIBiBAgAAFCMAAEAAIoRIAAAQD'
     'ECBAAAKEaAAAAAxQgQAACgGAECAAAUI0AAAIBiBAgAAFCMAAEAAIoRIAAAQDECBAAAKEaAAA'
     'AAxQgQAACgGAECAAAUI0AAAIBiBAgAAFCMAAEAAIoRIAAAQDECBAAAKEaAAAAAxQgQAACgGA'
     'ECAAAUI0AAAIBiBAgAAFCMAOmkjRs35pJLLsnEiROz1157pba2Ntdee%2B02j125cmUmTpyY'
     'fv36paGhIdOnT8/69esLTwwAAD2HAOmkdevW5dJLL82vf/3rjBgxIklSU1PT4bimpqaMGzcu'
     'v/3tbzNv3rycc845%2Bf73v58JEyZk69atpccGAIAeYddqD/BmM3DgwKxduzb77LNPHnrooY'
     'wePXqbx82dOzetra1ZsWJFBg0alCQZM2ZMJkyYkGuuuSannHJKybEBAKBH8A5IJ%2B22227Z'
     'Z599kiSVSuVVj7v55pszadKktvhIkvHjx2fIkCG58cYbu31OAADoiQRIN1izZk3WrVuXUaNG'
     'ddg3evTorFixogpTAQBA9QmQbtDc3JwkaWxs7LCvsbExGzZscB0IAAA7JQHSDVpbW5MkdXV1'
     'Hfb17t273TEAALAzESDdoL6%2BPkmyZcuWDvs2b97c7hgAANiZ%2BBSsbvDyqVcvn4r1Ss3N'
     'zWloaEivXr1e9f5z5sxJ//79222bNm1apk2b1rWDAgCwHTf8%2BfZKT1djkLcUAdIN9t133w'
     'wYMCDLly/vsG/ZsmVt3x/yahYuXJiRI0d213gAALwu0/58e6VfJDmsCrO8dTgFq5scd9xxue'
     'OOO9LU1NS2bcmSJVm9enWmTJlSxckAAKB6vAOyAxYtWpSnn346Tz75ZJLktttuyxNPPJEkOf'
     'PMM7PHHnvkggsuyOLFi3PkkUdm9uzZaWlpyfz58zN8%2BPDMnDmzmuMDAEDVCJAdcPnll%2B'
     'fxxx9PktTU1OSWW27Jd7/73dTU1GT69OnZY489MmjQoCxdujRnnXVWzjvvvNTV1WXSpEm5/P'
     'LLt3v9BwAAvJUJkB3wu9/97nUdN2zYsNx9993dPA0AALx5uAYEAAAoRoAAAADFCBAAAKAYAQ'
     'IAABQjQAAAgGIECAAAUIwAAQAAihEgAABAMQIEAAAoRoAAAADFCBAAAKAYAQIAABQjQAAAgG'
     'IECAAAUIwAAQAAihEgAABAMQIEAAAoRoAAAADFCBAAAKAYAQIAABQjQAAAgGIECAAAUIwAAQ'
     'AAihEgAABAMQIEAAAoRoAAAADFCBAAAKAYAQIAABQjQAAAgGIECAAAUIwAAQAAihEgAABAMQ'
     'IEAAAoRoAAAADFCBAAAKAYAQIAABQjQAAAgGIECAAAUIwAAQAAihEgAABAMQIEAAAoRoAAAA'
     'DFCBAAAKAYAQIAABQjQAAAgGIECAAAUIwAAQAAihEgAABAMQIEAAAoRoAAAADFCBAAAKAYAQ'
     'IAABQjQAAAgGIECAAAUIwAAQAAihEgAABAMQIEAAAoRoAAAADFCBAAAKAYAQIAABQjQAAAgG'
     'IECAAAUIwAAQAAihEgAABAMQIEAAAoRoAAAADFCBAAAKAYAQIAABQjQAAAgGIECAAAUIwAAQ'
     'AAihEgAABAMQIEAAAoRoAAAADFCBAAAKAYAQIAABQjQAAAgGIECAAAUIwAAQAAihEgAABAMQ'
     'IEAAAoRoAAAADFCJButGXLlnzmM5/JwIED06dPnxx%2B%2BOH54Q9/WO2xAACgagRIN5oxY0'
     'auuOKKfOITn8iXv/zl7LLLLvnIRz6S//iP/6j2aAAAUBUCpJssW7Ys//Zv/5bLLrssn//85/'
     'PJT34y9957b/bff/%2Bce%2B651R6vx7nhhhuqPQIFWW94K/Pv987FetN5AqSb3HTTTdl111'
     '1z6qmntm2rq6vLP/zDP%2BSnP/1p1qxZU8Xpeh7/Qbpzsd7wVubf752L9abzBEg3WbFiRYYM'
     'GZK%2Bffu22z569OgkycMPP1yNsQAAoKoESDdpbm5OY2Njh%2B0vb3vyySdLjwQAAFUnQLpJ'
     'a2tr6urqOmzv3bt3234AANjZ7FrtAd6q6uvrs2XLlg7bN2/e3Lb/1dx5551ZuXJlt83WE/3u'
     'd7/L5z73uWqPUVxLS0taWlqqPUZxK1asyJQpU6o9RnGtra1tvwN2Fs8888yf/3Rnkp3r91ry'
     'VJKnqz1EFfxXktOqPUQVbEyyqdpDVMGDSf5ftYco7JnXPoTtEiDdpLGxcZunWTU3NydJBg4c'
     'uM37DB06NJ/97Ge7fb6e6Je//GW1R6Cgm266qdojUNTO%2BXtt53VltQegqCXVHqC4oUOHbv'
     'NUe14fAdJNDj300Nx///1paWlJv3792rY/%2BOCDSZIRI0Z0uE9jY2PuvffetkgBAKDnaWxs'
     'FCBvQE2lUqlUe4i3omXLluXwww/P/Pnzc/bZZyd56ZvR3/e%2B92XAgAH5yU9%2BUuUJAQCg'
     'PO%2BAdJMxY8ZkypQpOf/88/OHP/whgwcPzrXXXpsnnngiV199dbXHAwCAqvAOSDfasmVLPv'
     'vZz%2Ba6667LU089lfe///259NJLM2HChGqPBgAAVSFAAACAYnwPCAAAUIwAoVM2btyYSy65'
     'JBMnTsxee%2B2V2traXHvttR2OmzFjRmprazvcDjrooG0%2B7je/%2Bc0cdNBBqa%2Bvz5Ah'
     'Q7Jo0aJOzfU///M/OfHEE/P2t789ffr0yZAhQ3LRRRft0Gvk//TE9f7Nb36Tv/u7v8t%2B%2'
     'B%2B2XPn365D3veU/OPvvsbNiwYYdfJy/pjvW%2B8sorM2XKlLzzne9MbW1tZs6c2amZKpVK'
     'vvCFL%2BSAAw5IfX193v/%2B9%2Bc73/nODr9G/k9PW%2B9Vq1bl3HPPzYgRI7LHHntk4MCB'
     'mTRpUh566KE39Dp5SU9b7790/fXXp7a2tt0nh/LW5SJ0OmXdunW59NJLs//%2B%2B2fEiBG5'
     '//77U1NTs81j6%2Brq8s1vfrPdtre97W0djvva176WT33qUzn%2B%2BONzzjnn5Ec/%2BlHO'
     'PPPMbNq0Keeee%2B5rzvTwww/nr/7qr7LffvvlnHPOSUNDQx5//PE0NTXt2IukTU9b77Vr1%'
     '2Bbwww9Pr169ctppp2W//fbLww8/nEWLFuW%2B%2B%2B7LQw899Krz8dq6Y72/8IUv5Nlnn8'
     '2YMWOydu3aTq/PBRdckM9//vM59dRTM3r06Nx666058cQTU1NTk6lTp3bqsWivp633N77xjf'
     'zLv/xLjj/%2B%2BJxxxhl5%2Bumn87WvfS2HH3547r777owfP75zL5B2etp6v9Kzzz6bc889'
     'N7vvvrvf4TuLCnTCli1bKr///e8rlUql8vOf/7xSU1NTufbaazscd/LJJ1f69ev3mo%2B3ad'
     'OmSkNDQ2Xy5Mnttp900kmVvn37Vp566qnt3v%2BFF16ovO9976uMHTu2snnz5k68El6Pnrbe'
     'V111VaWmpqZy5513ttt%2BySWXVGpqaioPP/zwa87Aq%2Bvq9a5UKpUnnnii7c99%2B/atzJ'
     'w583XP09TUVOnVq1dl1qxZ7baPGzeust9%2B%2B1VeeOGF1/1YdNTT1vuhhx6qbNy4sd22P/'
     '7xj5V99tmn8sEPfvB1Pw7b1tPW%2B5U%2B85nPVIYOHdr2vwW89TkFi07Zbbfdss8%2B%2By'
     'R56dSI7alUKnnxxRfzzDNYLm0CAAAJFElEQVTPvOox9913XzZs2JDTTjut3fbTTz89GzduzP'
     'e///3tPse///u/51e/%2BlUuueSS1NXVZdOmTXnhhRde56vhtfS09e7du3eStM30sne84x1J'
     'kvr6%2Bu3en%2B3r6vVOkv3222%2BH5/ne976X559/vsPPy6c%2B9ak0NTXlpz/96Q4/Nj1v'
     'vUeOHJk%2Bffq027bXXnvlgx/8YFauXLnDj8tLetp6v2z16tVZuHBhrrjiiuyyyy5v%2BPF4'
     'cxAgdJtNmzZljz32SP/%2B/dPQ0JAzzjgjGzdubHfMihUrkiSjRo1qt33kyJGpra3Nww8/vN'
     '3n%2BOEPf5jkpV%2Bso0aNSt%2B%2BfbP77rtn2rRpeeqpp7rw1fBaSqz3cccdlwMPPDCzZ8'
     '/Ogw8%2BmKamptx5552ZO3duPvaxj2XIkCFd%2B6J4Va9nvd%2BoFStWpG/fvhk6dGi77aNH'
     'j06S1/x5oeuUWO9Xs3bt2gwYMKDIc/GSkus9Z86cHHXUUZk4cWK3PD49k2tA6BYDBw7MZz7z'
     'mYwcOTIvvvhi7rrrrnzlK1/JI488kvvvv7/t/%2BVobm7OLrvskr333rvd/Xfbbbc0NDTkyS'
     'ef3O7zrF69Oklywgkn5Oijj86FF16Yhx9%2BOPPmzcv//u//5oEHHuieF0g7pda7T58%2Bee'
     'CBBzJ58uSMHTu2bfuMGTPy9a9/vetfGNv0etf7jWpubs7b3/72DtsbGxuT5DV/XugapdZ7W3'
     '784x/nZz/7WT772c9223PQXsn1/v73v5977rkn//mf/9llj8mbgwChW8ydO7fdP59wwgkZMm'
     'RILrzwwtx0001tF4%2B2trZmt9122%2BZj1NXVpbW1dbvP8%2ByzzyZ56Zvnv/WtbyVJPvax'
     'j6VPnz45//zzs2TJEhcuFlBqvTdu3JjJkyfnsccey5e%2B9KXsv//%2B%2BdGPfpQvf/nLaW'
     'hoyPz587vmBbFdr3e936jW1tbU1dV12P7yqXiv9fNC1yi13n/pD3/4Q0488cS8%2B93vfl0f'
     'SELXKLXezz33XD796U/nU5/6VId3OXnrcwoWxXz6059ObW1tlixZ0ratvr4%2Bzz333DaP37'
     'x582ue0//y/mnTprXbfuKJJyaJc8SrqDvW%2B8orr8zPfvaz3HHHHZk1a1aOOeaYLFiwIBdd'
     'dFG%2B%2BMUvOk%2B8ira13m9UfX19Nm/e3GH7y9tc81M93bHer7Rx48ZMmjQpGzduzPe%2B'
     '970O14ZQVnes9xVXXJENGzbkn/7pn7rsMXnzECAU07t37%2By1117tvq%2BhsbExL7zwQtav'
     'X9/u2Oeeey4bNmzIwIEDt/uYL%2B//y9M0Xj5f2HUg1dMd6/3AAw9k3333zciRI9ttnzx5ci'
     'qViuCsom2t9xvV2NiYtWvXdtje3NycJK/580L36Y71ftlzzz2Xj3/84/nlL3%2BZ733vexk2'
     'bFiXPwed09Xr/ac//Smf%2B9zn8slPfjJPP/10HnvssTz22GN59tlnU6lU8vjjj%2BcPf/hD'
     'lzwXPZMAoZiWlpasX7%2B%2B3cWEhx56aJJk%2BfLl7Y79%2Bc9/nhdffDEjRozY7mO%2BfD'
     'HzX37nx8vnhrtwsXq6Y723bt2a559/fpvbk2xzH2Vsa73fqEMPPTSbNm3q8M7Wgw8%2BmCSv'
     '%2BfNC9%2BmO9U6SF198MdOnT899992Xb3/72/nQhz7UpY/Pjunq9X7qqaeycePGfOELX8i7'
     '3/3uttt3v/vdbNq0KQcccED%2B8R//sUuei55JgNDltmzZkpaWlg7bL7300iRp90kXRx11VP'
     'baa69ceeWV7Y698sors/vuu%2BejH/1o27Znnnkmq1atavexgMcee2zq6upy9dVXt/tYwW98'
     '4xtJkgkTJnTNi%2BJVlVzvkSNH5ve//32WLl3a7v433HBDkv8LHLpPZ9a7M17t3%2B9evXrl'
     'K1/5Stu2SqWSr371qxk0aFCOOOKIHXouXr%2BS650ks2bNyo033pivfOUr%2BZu/%2BZsdem'
     'x2XKn1fvvb355bbrklt956a7vbkUcemd69e%2BfWW2/N%2Beefv%2BMvhB7PReh02qJFi/L0'
     '00%2B3vctw22235YknnkiSnHnmmdmwYUMOPfTQnHjiiTnwwAOTJD/4wQ9y11135eijj86xxx'
     '7b9li9e/fOpZdemtNPPz0nnHBCPvzhD%2BfHP/5xrr/%2B%2BsydOzf9%2B/dvO/a73/1u/v'
     '7v/z5XX311Tj755CQv/RK78MILc/HFF2fixIk59thj88gjj%2BQb3/hGTjzxxBx22GGl/lre'
     'snrSep922mn56le/msmTJ2fWrFl55zvfmaVLl%2BY73/lOPvzhD7d9PCs7rivXO0luv/32PP'
     'LII0leeqfqkUceyec%2B97kkLwXGIYcckmTb673vvvtmzpw5mT9/frZu3ZpRo0bl1ltvzQMP'
     'PJBvf/vbvjG5C/Sk9V64cGGuvPLKjB07NvX19bnuuuvaPfbHP/5x14K8QT1lvevr6zs81svH'
     'LVu2LMccc0z3/AXQc1Tj2w95c3vXu95VqampqdTU1FRqa2srtbW1bX9%2B/PHHK08//XTlE5'
     '/4ROW9731vZffdd6/07t27csghh1Quu%2ByyyvPPP7/Nx/z6179eGTp0aKWurq7y3ve%2Bt/'
     'KlL32pwzHXXHNNpba2dpvf3Lpo0aLKgQceWNltt90q%2B%2B%2B/f%2BXiiy9%2B1eeic3ra'
     'ev/617%2BuHH/88ZW99tqr0qtXr8oBBxxQOffccyutra3d8vp3Nl293jNmzHjVx3vl2r7aer'
     '/44ouVefPmVd71rndV6urqKoccckjl29/%2Bdrf/PewsetJ6z5gxo919Xnl7eR7emJ603tsy'
     'Y8aM1/0t7Ly51VQqr/F1mAAAAF3ENSAAAEAxAgQAAChGgAAAAMUIEAAAoBgBAgAAFCNAAACA'
     'YgQIAABQjAABAACKESAAAEAxAgQAAChGgAAAAMUIEAAAoBgBAgAAFCNAAACAYgQIAABQjAAB'
     'AACKESAAAEAxAgQAAChGgAAAAMUIEAAAoBgBAgAAFCNAAACAYgQIAABQjAABAACKESAAAEAx'
     'AgQAAChGgAAAAMUIEAAAoBgBAgAAFCNAAACAYgQIAABQjAABAACKESAAAEAxAgQAAChGgAAA'
     'AMUIEAAAoBgBAgAAFCNAAACAYgQIAABQzP8Hk1KLKyK0TtcAAAAASUVORK5CYII%3D"/>')]

if __name__ == '__main__':
    main()
