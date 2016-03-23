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

        self.qclient = QiitaClient('https://test_server.com', 'client_id',
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
    'T\n</p><hr/>']

EXP_HTML_DEMUX = [
    '<h3>Features</h3>',
    '<b>Total</b>: 49', '<br/>',
    '<b>Max</b>: 151', '<br/>',
    '<b>Mean</b>: 151', '<br/>',
    '<b>Standard deviation</b>: 151', '<br/>',
    '<b>Median</b>: 0', '<br/>',
    ('<img src = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAyAAAAJYCAYAA'
     'ACadoJwAAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAPYQAAD2EBqD%2BnaQAAIABJREFUeJ'
     'zs3XmYFIW99%2B3v4AIIKjiiQVEPEhFxQxTjfoI%2BGFSIr3tQREmiJq64RA3ujwnukaBPX'
     'KOgMSbuO264xwWjgB5FJXEh4KAgqMgmS79/qHMcB1QQqrHnvq%2BrrzhV1dW/To2ET6qqu6'
     'pUKpUCAABQgEblHgAAAGg4BAgAAFAYAQIAABRGgAAAAIURIAAAQGEECAAAUBgBAgAAFEaAA'
     'AAAhREgAABAYQQIAABQGAECAAAURoAAAACFESAAAEBhBAgAAFAYAQIAABRGgAAAAIURIAAA'
     'QGEECAAAUBgBAgAAFEaAAAAAhREgAABAYQQIAABQGAECAAAURoAAAACFESAAAEBhBAgAAFA'
     'YAQIAABRGgAAAAIURIAAAQGEECAAAUBgBAgAAFEaAAAAAhREgAABAYQQIAABQGAECAAAURo'
     'AAAACFESAAAEBhBAgAAFAYAQIAABRGgAAAAIURIAAAQGEECAAAUBgBAgAAFEaAAAAAhREgA'
     'ABAYQQIAABQGAECAAAURoAAAACFESAAAEBhBAgAAFAYAQIAABRGgCykxx57LI0aNZrvY/jw'
     '4XW2HT16dLp3754VV1wx1dXV6dOnTyZNmlSmyQEAoPyWLfcA31fHHHNMunTpUmdZu3btav9'
     '53Lhx2WGHHdKyZcucc845mTp1ai688MK8/PLLGT58eJZbbrmiRwYAgLITIIto%2B%2B23z5'
     '577rnA9QMGDMiMGTMyYsSItGnTJkmy5ZZbplu3bhk8eHAOOeSQokYFAIClhkuwFlGpVMrUq'
     'VMzZ86c%2Ba6/9dZb06NHj9r4SJKddtop7du3z0033VTUmAAAsFQRIIuob9%2B%2BWXnlld'
     'O0adPsuOOOeeGFF2rXjR8/PhMnTswWW2xR73ldunTJiBEjihwVAACWGi7BWkiNGzfO3nvvn'
     'V133TWrrrpqXnnllVx44YXZfvvt8/TTT6dTp06pqalJkrRu3bre81u3bp3Jkydn9uzZ7gMB'
     'AKDBESALaeutt87WW29d%2B3OPHj2y9957Z5NNNslvf/vbDB06NDNmzEjyWax8VZMmTZIkM'
     '2bMECAAADQ4AmQxaNeuXX7605/m9ttvT6lUStOmTZMks2bNqrftzJkzk6R2m6%2BqqampPY'
     'MCAMDSp3Xr1vO90oVvR4AsJmuttVY%2B/fTTTJs2rfYXcn4hUVNTk%2Brq6vme/aipqcmOO'
     '%2B6Y1157bYnPCwDAounQoUMeeeQREbKIBMhi8uabb6Zp06Zp3rx5mjdvnlatWuX555%2Bv'
     't93w4cPTqVOn%2Be6jpqYmr732Wv7yl79kgw02WNIjL1X69euXgQMHlnsMCuJ4NyyOd8Pie'
     'DcsDfF4jx49Or17905NTY0AWUQCZCFNnDgxrVq1qrNs1KhRueuuu7LbbrvVLttrr70yZMiQ'
     'jBs3rvajeIcNG5YxY8bk%2BOOP/9rX2GCDDdK5c%2BfFP/xSrEWLFg3uPTdkjnfD4ng3LI5'
     '3w%2BJ4sygEyELab7/9ssIKK2TrrbfOaqutlldffTVXXnllmjdvnnPPPbd2u/79%2B%2Bfm'
     'm29O165dc8wxx2Tq1Km54IILsskmm6Rv375lfAcAAFA%2BvgdkIe2xxx6ZNGlSLr744hxxx'
     'BG5%2Beabs/fee%2Bef//xn1l9//drt2rRpk8cffzzt2rXLySefnAsvvDA9evTIQw895NOv'
     'AABosJwBWUhHHXVUjjrqqG%2B1bceOHXP//fcv4YkAAOD7wxkQlgq9evUq9wgUyPFuWBzvh'
     'sXxblgcbxZFValUKpV7CD7z4osvZvPNN88LL7zghi4AgKWQv699d86AAAAAhXEPCABL1Jgx'
     'YzJ16tRyjwGwWIwePbrcI3zvCRAAlpgxY8akffv25R4DgKWIAAFgifnfMx9/SbJBOUcBWEx'
     'GJ%2Bld7iG%2B1wQIAAXYIImbNQFwEzoAAFAgAQIAABRGgAAAAIURIAAAQGEECAAAUBgBAg'
     'AAFEaAAAAAhREgAABAYQQIAABQGAECAAAURoAAAACFESAAAEBhBAgAAFAYAQIAABRGgAAAA'
     'IURIAAAQGEECAAAUBgBAgAAFEaAAAAAhREgAABAYQQIAABQGAECAAAURoAAAACFESAAAEBh'
     'BAgAAFAYAQIAABRGgAAAAIURIAAAQGEECAAAUBgBAgAAFEaAAAAAhREgAABAYQQIAABQGAE'
     'CAAAURoAAAACFESAAAEBhBAgAAFAYAQIAABRGgAAAAIURIAAAQGEECAAAUBgBAgAAFEaAAA'
     'AAhREgAABAYQQIAABQGAECAAAURoAAAACFESAAAEBhBAgAAFAYAQIAABRGgAAAAIURIAAAQ'
     'GEECAAAUBgBAgAAFEaAAAAAhREgAABAYQQIAABQGAECAAAURoAAAACFESAAAEBhBAgAAFAY'
     'AQIAABRGgAAAAIURIAAAQGEECAAAUBgBAgAAFEaAAAAAhREgAABAYQQIAABQGAECAAAURoA'
     'AAACFESAAAEBhBAgAAFAYAQIAABRGgAAAAIURIN/R73//%2BzRq1Cgbb7xxvXWjR49O9%2B'
     '7ds%2BKKK6a6ujp9%2BvTJpEmTyjAlAAAsHZYt9wDfZ%2BPGjcuAAQPSrFmzVFVV1Vu3ww4'
     '7pGXLljnnnHMyderUXHjhhXn55ZczfPjwLLfccmWaGgAAykeAfAcnnHBCttlmm8yZM6femY'
     '0BAwZkxowZGTFiRNq0aZMk2XLLLdOtW7cMHjw4hxxySDlGBgCAsnIJ1iJ64okncuutt2bgw'
     'IEplUr1zoDceuut6dGjR218JMlOO%2B2U9u3b56abbip6XAAAWCoIkEUwd%2B7cHHXUUTnk'
     'kEOy4YYb1ls/fvz4TJw4MVtssUW9dV26dMmIESOKGBMAAJY6LsFaBJdffnnGjh2bRx55ZL7'
     'ra2pqkiStW7eut65169aZPHlyZs%2Be7T4QAAAaHGdAFtIHH3yQ008/Paeffnqqq6vnu82M'
     'GTOSJI0bN663rkmTJnW2AQCAhkSALKRTTz01q666ao466qgFbtO0adMkyaxZs%2BqtmzlzZ'
     'p1tAACgIXEJ1kIYM2ZMrrrqqgwcODDjxo2rXT5z5sx8%2Bumneeedd7LSSivVXnr1xaVYX1'
     'ZTU5Pq6uqvvfyqX79%2BadGiRZ1lvXr1Sq9evRbTOwEA4Jvd%2BPnjyz4sxyAVRYAshPHjx'
     '2fevHk5%2Buijc/TRR9db37Zt2/Tr1y9/%2BMMf0qpVqzz//PP1thk%2BfHg6der0ta8zcO'
     'DAdO7cebHNDQDAouj1%2BePLXkyyeRlmqRwCZCFsvPHGuf322%2Bt85G6pVMqpp56aTz75J'
     'H/84x/Trl27JMlee%2B2VIUOGZNy4cbUfxTts2LCMGTMmxx9/fFnmBwCAchMgC6G6ujq777'
     '57veUXX3xxkuSnP/1p7bL%2B/fvn5ptvTteuXXPMMcdk6tSpueCCC7LJJpukb9%2B%2Bhc0'
     'MAABLEzehLwZVVVX1voiwTZs2efzxx9OuXbucfPLJufDCC9OjR4889NBDPn4XAIAGyxmQxe'
     'DRRx%2Bd7/KOHTvm/vvvL3gaAABYejkDAgAAFEaAAAAAhREgAABAYQQIAABQGAECAAAURoA'
     'AAACFESAAAEBhBAgAAFAYAQIAABRGgAAAAIURIAAAQGEECAAAUBgBAgAAFEaAAAAAhREgAA'
     'BAYQQIAABQGAECAAAURoAAAACFESAAAEBhBAgAAFAYAQIAABRGgAAAAIURIAAAQGEECAAAU'
     'BgBAgAAFEaAAAAAhREgAABAYQQIAABQGAECAAAURoAAAACFESAAAEBhBAgAAFAYAQIAABRG'
     'gAAAAIURIAAAQGEECAAAUBgBAgAAFEaAAAAAhREgAABAYQQIAABQGAECAAAURoAAAACFESA'
     'AAEBhBAgAAFAYAQIAABRGgAAAAIURIAAAQGEECAAAUJhlyz1AUebNm5dHH300n376abbbbr'
     'usuOKK5R4JAAAanIo8A3LKKaeka9eutT%2BXSqXsvPPO6datW3bbbbdstNFG%2Bfe//13GC'
     'QEAoGGqyAC59dZb06VLl9qfb7nlljzyyCP5/e9/n3vuuSdz587NGWecUcYJAQCgYarIS7DG'
     'jx%2Bf9dZbr/bn2267LRtssEF%2B%2B9vfJkkOP/zwXHbZZeUaDwAAGqyKPAOy7LLLZtasW'
     'Uk%2Bu/dj2LBh6d69e%2B361VZbLRMnTizXeAAA0GBVZIBsuOGGuf766zN58uQMHjw4kyZN'
     'ym677Va7fuzYsVl11VXLOCEAADRMFXkJ1hlnnJEePXrURsa2225b56b0e%2B%2B9t849IgA'
     'AQDEqMkC6deuWF198MQ899FBatmyZ/fbbL1VVVUmSKVOmZPvtt8/uu%2B9e5ikBAKDhqcgA'
     'ST67DGvDDTest7xly5YZOHBgGSYCAAAqNkCS5Jlnnsljjz2W999/P4cffnjWW2%2B9TJ8%2'
     'BPa%2B99lrWW289X0YIAAAFq8ib0D/99NPsscce2XbbbXPKKadk0KBB%2Bc9//pMkqaqqys'
     '4775w//vGPZZ4SAAAanooMkNNOOy333ntvLr/88rz%2B%2BusplUq165o2bZp99tknd911V'
     'xknBACAhqkiA%2BTGG2/Mr371qxx66KFp2bJlvfUdOnTIv//97zJMBgAADVtFBsj777%2Bf'
     'TTbZZIHrl1lmmUyfPr3AiQAAgKRCA6RNmzYZPXr0Atc//fTT%2BeEPf1jgRAAAQFKhAXLAA'
     'QfkiiuuyNNPP137/R9fuOqqq/L3v/89ffr0KdN0AADQcFXkx/D2798/zz77bHbYYYdssMEG'
     'SZLjjjsuH3zwQcaPH59dd901xx57bJmnBACAhqciz4A0btw4Q4cOzeDBg7PuuuumQ4cOmTl'
     'zZjbddNMMHjw4d999d5ZdtiLbCwAAlmoV%2B7fwRo0apXfv3undu3e5RwEAAD5XkWdAPvjg'
     'g7z00ksLXP/SSy9l8uTJBU4EAAAkFRogxx13XA499NAFrv/Vr36VE044ocCJAACApEID5JF'
     'HHknPnj0XuL5nz54ZNmxYgRMBAABJhQbIxIkT06pVqwWuX2WVVfLee%2B8VOBEAAJBUaID8'
     '4Ac/yIsvvrjA9S%2B%2B%2BOLXBgoAALBkVGSA7LHHHvnzn/%2BcO%2B%2B8s966O%2B64I'
     '9dcc0322GOPMkwGAAANW0V%2BDO8ZZ5yRhx9%2BOHvssUc6deqUjTbaKEny8ssvZ9SoUenY'
     'sWPOOuusMk8JAAANT0WeAWnRokWeeeaZnHbaafn0009z880355ZbbsmcOXNy%2Bumn57nnn'
     'kvLli3LPSYAADQ4FXkGJEmaN2%2Bes846y5kOAABYilTkGRAAAGDpVLFnQF599dVce%2B21'
     'eeuttzJlypSUSqXadaVSKVVVVXnkkUfKOCEAADQ8FRkg119/fQ4%2B%2BOAsv/zyWX/99dO'
     'iRYtyjwQAAKRCA%2BTMM8/MZpttlvvvvz%2BrrrpquccBAAA%2BV5H3gLz77rv5xS9%2BIT'
     '4AAGApU5EBsvHGG%2Bfdd98t9xgAAMBXVGSA/OEPf8jVV1%2Bdf/zjH4t936%2B88kr22We'
     'ftGvXLs2aNUt1dXW22Wab3HDDDfW2HT16dLp3754VV1wx1dXV6dOnTyZNmrTYZwIAgO%2BL'
     'irwH5LzzzkuLFi2y/fbbZ8MNN8zaa6%2BdZZZZpt52d91110Lve%2BzYsfnkk09y8MEHZ40'
     '11sj06dNzyy235MADD8zbb7%2BdU045JUkybty47LDDDmnZsmXOOeecTJ06NRdeeGFefvnl'
     'DB8%2BPMstt9x3fp8AAPB9U5EB8vLLL6eqqiprr712pk6dmldeeaXeNlVVVYu071122SW77'
     'LJLnWVHHHFENt9881x55ZW1ATJgwIDMmDEjI0aMSJs2bZIkW265Zbp165bBgwfnkEMOWaTX'
     'BwCA77OKDJC333670Ndr1KhR2rRpk6lTp9Yuu/XWW9OjR4/a%2BEiSnXbaKe3bt89NN90kQ'
     'AAAaJAqMkCKMH369EyfPj0fffRR7rrrrjzwwAO59NJLkyTjx4/PxIkTs8UWW9R7XpcuXTJ0'
     '6NCixwUAgKVCRd6EniRz5szJjTfemEMPPTR77LFHXn755STJRx99lNtuuy3vvffed9r/ccc'
     'dl9VWWy3rrbdeTjrppAwaNCiHHnpokqSmpiZJ0rp163rPa926dSZPnpzZs2d/p9cHAIDvo4'
     'oMkA8//DDbbrttDjjggNx444258847M3HixCRJs2bNcvTRR2fgwIHf6TWOPfbYPPzww7nuu'
     'uuy00475cgjj8yQIUOSJDNmzEiSNG7cuN7zmjRpUmcbAABoSCoyQE4%2B%2BeS8%2Buqruf'
     '/%2B%2B/PWW2/VWbfssstm7733/s6XQa2//vrZcccd07t37wwdOjQ77bRT%2BvXrl5kzZ6Z'
     'p06ZJklmzZtV73syZM5OkdhsAAGhIKvIekDvuuCNHHnlkdt555/l%2B78Z6662Xa6%2B9dr'
     'G%2B5l577ZWHHnoor732Wu2lV19civVlNTU1qa6u/tqP4e3Xr19atGhRZ1mvXr3Sq1evxTo'
     'zAABf58bPH1/2YTkGqSgVGSAfffRR1l133QWunz17dubMmbNYX/OLS6oaNWqUNddcM61atc'
     'rzzz9fb7vhw4enU6dOX7uvgQMHpnPnzot1PgAAFlavzx9f9mKSzcswS%2BWoyEuw1l133bz'
     'wwgsLXP/QQw%2BlY8eOi7TvL%2B4l%2BbLZs2fnuuuuS3V1dTbccMMkn50RueeeezJu3Lja'
     '7YYNG5YxY8Zkn332WaTXBgCA77uKPANyyCGH5MQTT0zXrl2z00471S6fOXNmzj777AwdOjR'
     'XXnnlIu370EMPzdSpU7PDDjtkjTXWyIQJE3LDDTfkjTfeyLXXXlv7jev9%2B/fPzTffnK5d'
     'u%2BaYY47J1KlTc8EFF2STTTZJ3759F8v7BACA75uKDJCjjz46r7zySnr16pWVV145SbL//'
     'vvngw8%2ByNy5c3PYYYfll7/85SLt%2B2c/%2B1n%2B/Oc/57LLLssHH3yQlVZaKT/60Y9y'
     '6aWX1omdNm3a5PHHH89xxx2Xk08%2BOY0bN06PHj1y0UUXfe39HwAAUMkqMkAaNWqUq666K'
     'gcddFBuvvnmjBkzJvPmzUu7du2y3377ZYcddljkfe%2B3337Zb7/9vtW2HTt2zP3337/Irw'
     'UAAJWmIgPkC9ttt1222267co8BAAB8riJvQgcAAJZOFXkGpG3btqmqqkqpVKqzvKqqKklSK'
     'pVSVVWVN998sxzjAQBAg1WRAfLf//3f9ZbNnTs377zzTv7xj39ko4028j0bAABQBhUZIIMH'
     'D17gulGjRuUnP/lJDjjggOIGAgAAkjTAe0A23XTTHHbYYTnppJPKPQoAADQ4DS5AkmS11Vb'
     'LK6%2B8Uu4xAACgwWlwATJp0qRcc801adOmTblHAQCABqci7wHp2rVr7SdefdmUKVPy2muv'
     'Zfbs2bnuuuvKMBkAADRsFRkgX3z87pc/hreqqipt27ZNt27d8vOf/zwdOnQo13gAANBgVWS'
     'APPbYY%2BUeAQAAmI8Gdw8IAABQPhV5BmTIkCHzvQfkm/Tp02cJTAMAAHyhIgOkb9%2B%2B'
     'i/Q8AQIAAEtWRQbIiy%2B%2BmIMOOigtWrTIUUcdlfbt2ydJXn/99VxyySX5%2BOOPM2TIk'
     'Ky88splnhQAABqWigyQgQMHplWrVnnwwQfTqNH/3uayySabZM8998zOO%2B%2Bciy%2B%2B'
     'OIMHDy7fkAAA0ABV5E3od955Z/bcc8868fGFZZZZJnvuuWfuvPPOMkwGAAANW0UGyLx58zJ'
     '69OgFrh89enSd7wgBAACKUZEBsscee%2BSyyy7LRRddlOnTp9cunzZtWi688MJcfvnl2X33'
     '3cs4IQAANEwVew/IW2%2B9ld/85jfp379/WrdunVKplJqamsyZMyfbbrttBg4cWO4xAQCgw'
     'anIAGnRokUee%2Byx3HXXXbnvvvvyzjvvJEm6d%2B%2Be3XbbLT179lyk7wkBAAC%2Bm4oM'
     'kCSpqqrK7rvv7lIrAABYilRsgCTJuHHj8uSTT%2Bb999/PXnvtlTZt2mTu3Ln56KOPstJKK'
     '2XZZSv67QMAwFKnIm9CL5VKOfbYY9O2bdsccMABOe644/LGG28kSaZOnZp11lknl1xySZmn'
     'BACAhqciA%2BSCCy7IoEGD8pvf/CYPPfRQnY/cbdGiRfbaa6/cdtttZZwQAAAapooMkKuuu'
     'ioHHnhgBgwYkE033bTe%2Bo033jivv/56GSYDAICGrSID5D//%2BU%2B23XbbBa5v1qxZPv'
     '744wInAgAAkgoNkFatWmXs2LELXP/iiy9m7bXXLnAiAAAgqdAA2WuvvXLFFVfk3//%2Bd73'
     'v%2B3jwwQczePDg7LPPPmWaDgAAGq6KDJAzzzwzrVu3TqdOndKnT58kyfnnn59tt9023bt3'
     'zyabbJL%2B/fuXeUoAAGh4KjJAWrRokWeeeSYnnXRSxo0blyZNmuTxxx/PRx99lDPPPDNPP'
     'vlkmjVrVu4xAQCgwanYb%2BJbYYUVcuqpp%2BbUU08t9ygAAMDnKvIMyIK8%2BeabGT16dL'
     'nHAACABqsiA2TQoEH52c9%2BVmfZwQcfnB/%2B8IfZcMMNs/nmm%2Bf9998v03QAANBwVWS'
     'AXH311VlttdVqf37ggQdy3XXX5bDDDsull16aN998M2eeeWb5BgQAgAaqIu8Beeedd9KxY8'
     'fan2%2B66ab813/9V/70pz%2BlqqoqEyZMyPXXX1/GCQEAoGGqyDMgpVKpzs8PPvhgdtlll'
     '9rvBFlnnXVSU1NTjtEAAKBBq8gAWW%2B99XLbbbelVCrlgQceyPjx47PLLrvUrh8/fnxatG'
     'hRxgkBAKBhqshLsH7zm99k//33zyqrrJJPPvkkG2ywQX7yk5/Urn/kkUfSqVOnMk4IAAANU'
     '0UGyM9%2B9rNUV1fn3nvvTcuWLXP44YdnueWWS5JMnjw5LVu2zIEHHljmKQEAoOGpyABJkm'
     '7duqVbt271lq%2Byyiq5/fbbyzARAABQkfeAAAAASycBAgAAFEaAAAAAhREgAABAYSoiQAY'
     'NGpQ33nij3GMAAADfoCICpF%2B/fvnnP/9Z%2B3OjRo3y17/%2BtYwTAQAA81MRAdKyZctM'
     'mDCh3GMAAADfoCK%2BB6Rr164588wzM3LkyKy88spJkuuuuy7PPvvs1z5v0KBBRYwHAAB8r'
     'iIC5P/9v/%2BXY489Ng8%2B%2BGAmTpyYJHnwwQfz4IMPfu3zBAgAABSrIi7BWn311fPXv/'
     '41EyZMyNy5c5Mk119/febNm/e1DwAAoFgVESBfdc0112SbbbYp9xgAAMBXVMQlWF918MEHJ'
     '0lKpVJeffXVjB07NkmyzjrrpGPHjmWcDAAAGraKDJAkueOOO3Lcccfl7bffrrO8bdu2%2Bc'
     'Mf/pDdd9%2B9PIMBAEADVpGXYN13333Ze%2B%2B9U1VVlXPOOSe33357br/99pxzzjlJkr3'
     '22itDhw4t85QAANDwVOQZkLPPPjsbb7xxnnrqqTRr1qx2%2Be67754jjzwy2223Xf7v//2/'
     '2WWXXco4JQAANDwVeQbkpZdeysEHH1wnPr7QrFmzHHTQQRk1alQZJgMAgIatIgOkcePG%2B'
     'eCDDxa4fsqUKWnSpEmBEwEAAEmFBshOO%2B2UQYMG5emnn6637tlnn82gQYPyf/7P/ynDZA'
     'AA0LBV5D0g5513Xp588slst912%2BdGPfpT1118/SfLaa69l%2BPDhWX311XPeeeeVeUoAA'
     'Gh4KvIMyLrrrptRo0blmGOOyeTJk/O3v/0tf//73/Phhx%2BmX79%2BGTVqVNq2bVvuMQEA'
     'oMGpyDMgSbL66qvn4osvzsUXX1zuUQAAgM9V5BkQAABg6SRAAACAwggQAACgMAIEAAAojAA'
     'BAAAKU3EBMm3atHTu3DmXX355uUcBAAC%2BouICpFmzZnn77bdTVVVV7lEAAICvqLgASZLu'
     '3bvngQceKPcYAADAV1RkgJx22ml544030rt37zz11FMZP358Jk%2BeXO8BAAAUqyK/CX3DD'
     'TdMkrz66qv561//Ot9tqqqqMnfu3CLHAgCABq8iA%2BT000//xm3cIwIAAMWryAA588wzyz'
     '0CAAAwHxV5D8hXffTRR5kzZ065xwAAgAavYgPk%2Beefz09%2B8pM0bdo0q6yySp544okky'
     'cSJE/PTn/40jz32WHkHBACABqgiA%2BTpp5/O9ttvn3/961/p3bt3SqVS7bpWrVrlo48%2B'
     'yhVXXFHGCQEAoGGqyADp379/OnTokFdeeSXnnHNOvfVdu3bNc889V4bJAACgYavIAHn%2B%'
     '2BefTt2/fNGnSZL7r11xzzdTU1BQ8FQAAUJEBstxyy9W57Oqr3n333TRv3rzAiQAAgKRCA2'
     'SrrbbKLbfcMt9106ZNy7XXXpv//u//LngqAACgIgPkrLPOyvPPP59dd901Q4cOTZKMHDkyV'
     '111VTp37pz3338/p512WpmnBACAhqciA%2BRHP/pRhg4dmn/961856KCDkiQnnHBCDjvssM'
     'ybNy9Dhw7Npptuukj7fv7553PkkUdmww03TPPmzbPOOutkv/32y5gxY%2BptO3r06HTv3j0'
     'rrrhiqqur06dPn0yaNOk7vTcAAPg%2Bq8hvQk%2BSHXfcMa%2B//npGjhyZMWPGZN68eWnX'
     'rl222GKLVFVVLfJ%2BzzvvvDzzzDPZZ599sskmm6SmpiaXXnppOnfunGeffTYbbrhhkmTcu'
     'HHZYYcd0rJly5xzzjmZOnVqLrzwwrz88ssZPnx4lltuucX1VgEA4HujYgMkSaqqqrLZZptl'
     's802W2z7PP7449OlS5csu%2Bz//le33377ZeONN865556b66%2B/PkkyYMCAzJgxIyNGjEi'
     'bNm2SJFtuuWW6deuWwYMH55BDDllsMwEAwPdFRV6ClSQzZ87MJZdckl122SUdO3ZMx44ds%'
     '2Buuu%2BaSSy7JzJkzF3m/W2%2B9dZ34SJIf/vCH6dixY1577bXaZbfeemt69OhRGx9JstN'
     'OO6V9%2B/a56aabFvn1AQDg%2B6wiA2TcuHHp1KlTjjnmmLz00ktZddVVs%2Bqqq2bkyJE5'
     '5phjsummm2bcuHGL7fVKpVLee%2B%2B9rLrqqkmS8ePHZ%2BLEidliiy3qbdulS5eMGDFis'
     'b02AAB8n1RkgBxxxBEZO3Zsbrr%2BPbmAAAAgAElEQVTppowfPz5PPPFEnnjiiYwfPz5///'
     'vfM3bs2Bx%2B%2BOGL7fVuuOGGvPvuu9lvv/2SpPZLDlu3bl1v29atW2fy5MmZPXv2Ynt9A'
     'AD4vqjIe0CGDRuWfv36Ze%2B9966zvKqqKvvss09efPHFXHLJJYvltV577bUcccQR2WabbW'
     'o/cWvGjBlJksaNG9fb/otvZ58xY4Yb0QEAaHAq8gxI8%2BbNs/rqqy9w/Q9%2B8IPF8k3oE'
     'yZMyG677ZaWLVvmlltuqf10raZNmyZJZs2aVe85X9x/8sU2AADQkFTkGZCf//znGTx4cH75'
     'y1%2BmWbNmddZ98sknufbaa/OLX/ziO73GRx99lF122SUff/xxnnzyyfzgBz%2BoXffFpVd'
     'fXIr1ZTU1Namurv7asx/9%2BvVLixYt6izr1atXevXq9Z1mBgBgYdz4%2BePLPizHIBWlIg'
     'Lktttuq/Nzp06dcu%2B992aDDTZInz59st566yVJ3njjjVx33XVZZZVVFvmLCJPPzmL07Nk'
     'z//rXv/Lwww%2BnQ4cOddavueaaadWqVZ5//vl6zx0%2BfHg6der0tfsfOHBgOnfuvMjzAQ'
     'CwOPT6/PFlLybZvAyzVI6KCJCv3uvxZQMGDKi3bPz48enVq1f23XffhX6tuXPnZr/99stzz'
     'z2XO%2B%2B8Mz/60Y/mu91ee%2B2VIUOGZNy4cbUfxTts2LCMGTMmxx9//EK/LgAAVIKKCJ'
     'BHHnmksNc6/vjjc/fdd6dnz56ZNGlS/vKXv9RZ37t37yRJ//79c/PNN6dr16455phjMnXq1'
     'FxwwQXZZJNN0rdv38LmBQCApUlFBMiPf/zjwl5r1KhRqaqqyt1335277767zrqqqqraAGnT'
     'pk0ef/zxHHfccTn55JPTuHHj9OjRIxdddJFPvwIAoMGqiAAp0qOPPvqtt%2B3YsWPuv//%2'
     'BJTgNAAB8v1RsgDz55JO55ppr8tZbb2XKlCkplUq160qlUqqqqvLSSy%2BVcUIAAGh4KjJA'
     'Lr744hx//PFp2rRp1l9//bRs2bLeNl98ZwcAAFCcigyQ888/P9tuu23uueeerLzyyuUeBwA'
     'A%2BFxFfhP6tGnT0rt3b/EBAABLmYoMkB//%2BMd5%2BeWXyz0GAADwFRUZIJdeemkeeOCB'
     'XHDBBZk8eXK5xwEAAD5XkQGy9tpr57DDDstJJ52UVq1apVmzZllxxRWz4oorZqWVVqr9TwA'
     'AoFgVeRP6aaedlt///vdp06ZNNt988/neC%2BJTsAAAoHgVGSBXXHFFdtttt9x5551p1Kgi'
     'T/IAAMD3UkX%2B7fzTTz9Njx49xAcAACxlKvJv6LvuumuefPLJco8BAAB8RUUGyJlnnplXX'
     'nklv/71r/PCCy9k4sSJmTx5cr0HAABQrIq8B6RDhw5JklGjRuWKK66Y7zZVVVWZO3dukWMB'
     'AECDV5EBcvrpp3/jNj4FCwAAileRAXLmmWeWewQAAGA%2BKvIeEAAAYOlUkWdAzjrrrG91i'
     'dW3uVQLAABYfCo2QL4NAQIAAMWqyEuw5s2bV%2B8xe/bs/Otf/8pxxx2XzTffPO%2B//365'
     'xwQAgAanIgNkfpZZZpmsu%2B66ufDCC7PeeuvlqKOOKvdIAADQ4DSYAPmyHXbYIffdd1%2B'
     '5xwAAgAanQQbICy%2B8kEaNGuRbBwCAsqrIm9CHDBky30/B%2BvDDD/P444/n9ttvzy9%2B'
     '8YsyTAYAAA1bRQZI3759F7hu1VVXzcknn%2BwTsAAAoAwqMkDefPPNesuqqqrSsmXLrLTSS'
     'mWYCAAASCo0QP7rv/6r3CMAAADz4U5sAACgMBVzBmTjjTee743n81MqlVJVVZWXXnppCU8F'
     'AAB8WcUESHV19TduU1VVlQkTJuT1118vYCIAAOCrKiZAHnvssa9dP2HChJx33nm54oorssw'
     'yy6R3797FDAYAANSqmABZkAkTJuTcc8/NlVdemTlz5qR379455ZRT0q5du3KPBgAADU7FBk'
     'hNTU3OO%2B%2B8OuFx6qmnZt111y33aAAA0GBVXIDU1NTk3HPPzVVXXZU5c%2BbkwAMPzKm'
     'nnpq2bduWezQAAGjwKiZA3n333drwmDt3bvr06ZNTTjlFeAAAwFKkYgKkXbt2mTVrVjp16p'
     'T%2B/funbdu2mTJlSqZMmbLA53Tu3LnACQEAgIoJkFmzZiVJRo4cmX333fcbt6%2Bqqsrcu'
     'XOX9FgAAMCXVEyAXHPNNeUeAQAA%2BAYVEyAHH3xwuUcAAAC%2BQaNyDwAAADQcAgQAACiM'
     'AAEAAAojQAAAgMIIEAAAoDACBAAAKIwAAQAACiNAAACAwggQAACgMAIEAAAojAABAAAKI0A'
     'AAIDCCBAAAKAwAgQAACiMAAEAAAojQAAAgMIIEAAAoDACBAAAKIwAAQAACiNAAACAwggQAA'
     'CgMAIEAAAojAABAAAKI0AAAIDCCBAAAKAwAgQAACiMAAEAAAojQAAAgMIIEAAAoDACBAAAK'
     'IwAAQAACiNAAACAwggQAACgMAIEAAAojAABAAAKI0AAAIDCCBAAAKAwAgQAACiMAAEAAAoj'
     'QAAAgMIIEAAAoDACBAAAKIwAAQAACiNAAACAwgiQhTRt2rScccYZ6d69e1ZZZZU0atQoQ4Y'
     'Mme%2B2o0ePTvfu3bPiiiumuro6ffr0yaRJkwqeGAAAlh4CZCFNnDgxZ599dl5//fV06tQp'
     'SVJVVVVvu3HjxmWHHXbIm2%2B%2BmXPOOScnnHBC7r333nTr1i2zZ88uemwAAFgqLFvuAb5'
     'v1lhjjUyYMCGrrbZaXnjhhXTp0mW%2B2w0YMCAzZszIiBEj0qZNmyTJlltumW7dumXw4ME5'
     '5JBDihwbAACWCs6ALKTll18%2Bq622WpKkVCotcLtbb701PXr0qI2PJNlpp53Svn373HTTT'
     'Ut8TgAAWBoJkCVg/PjxmThxYrbYYot667p06ZIRI0aUYSoAACg/AbIE1NTUJElat25db13r'
     '1q0zefJk94EAANAgCZAlYMaMGUmSxo0b11vXpEmTOtsAAEBDIkCWgKZNmyZJZs2aVW/dzJk'
     'z62wDAAANiU/BWgK%2BuPTqi0uxvqympibV1dVZbrnlFvj8fv36pUWLFnWW9erVK7169Vq8'
     'gwIA8DVu/PzxZR%2BWY5CKIkCWgDXXXDOtWrXK888/X2/d8OHDa78/ZEEGDhyYzp07L6nxA'
     'AD4Vnp9/viyF5NsXoZZKodLsJaQvfbaK/fcc0/GjRtXu2zYsGEZM2ZM9tlnnzJOBgAA5eMM'
     'yCK49NJL8%2BGHH%2Bbdd99Nktx1110ZO3ZskuToo4/OSiutlP79%2B%2Bfmm29O165dc8w'
     'xx2Tq1Km54IILsskmm6Rv377lHB8AAMpGgCyCiy66KO%2B8806SpKqqKrfffntuu%2B22VF'
     'VVpU%2BfPllppZXSpk2bPP744znuuONy8sknp3HjxunRo0cuuuiir73/AwAAKpkAWQRvvfX'
     'Wt9quY8eOuf/%2B%2B5fwNAAA8P3hHhAAAKAwAgQAACiMAAEAAAojQAAAgMIIEAAAoDACBA'
     'AAKIwAAQAACiNAAACAwggQAACgMAIEAAAojAABAAAKI0AAAIDCCBAAAKAwAgQAACiMAAEAA'
     'AojQAAAgMIIEAAAoDACBAAAKIwAAQAACiNAAACAwggQAACgMAIEAAAojAABAAAKI0AAAIDC'
     'CBAAAKAwAgQAACiMAAEAAAojQAAAgMIIEAAAoDACBAAAKIwAAQAACiNAAACAwggQAACgMAI'
     'EAAAojAABAAAKI0AAAIDCCBAAAKAwAgQAACiMAAEAAAojQAAAgMIIEAAAoDACBAAAKIwAAQ'
     'AACiNAAACAwggQAACgMAIEAAAojAABAAAKI0AAAIDCCBAAAKAwAgQAACiMAAEAAAojQAAAg'
     'MIIEAAAoDACBAAAKIwAAQAACiNAAACAwggQAACgMAIEAAAojAABAAAKI0AAAIDCCBAAAKAw'
     'AgQAACiMAAEAAAojQAAAgMIIEAAAoDACBAAAKIwAAQAACiNAAACAwggQAACgMAIEAAAojAA'
     'BAAAKI0AAAIDCCBAAAKAwAgQAACiMAAEAAAojQAAAgMIIEAAAoDACBAAAKIwAAQAACiNAAA'
     'CAwggQAACgMAIEAAAojABZgmbNmpWTTjopa6yxRlZYYYVstdVWefjhh8s9FgAAlI0AWYIOP'
     'vjgXHzxxTnwwAMzaNCgLLPMMtl1113zj3/8o9yjAQBAWQiQJWT48OH5%2B9//nnPPPTfnnX'
     'defvnLX%2BaRRx7JOuuskxNPPLHc4y11brzxxnKPQIEcb6hk/v1uWBxvFp4AWUJuueWWLLv'
     'ssjn00ENrlzVu3Di/%2BMUv8swzz2T8%2BPFlnG7p4y%2BkDYvjDZXMv98Ni%2BPNwhMgS8'
     'iIESPSvn37NG/evM7yLl26JElGjhxZjrEAAKCsBMgSUlNTk9atW9db/sWyd999t%2BiRAAC'
     'g7ATIEjJjxow0bty43vImTZrUrgcAgIZm2XIPUKmaNm2aWbNm1Vs%2Bc%2BbM2vULct9992'
     'X06NFLbLal0VtvvZXf/e535R6jcFOnTs3UqVPLPUbhRowYkX322afcYxRuxowZtX8GNBQff'
     '/zx5/90X5KG9edaMiXJh%2BUeogxeTXJ4uYcog2lJppd7iDJ4Lsn/KfcQBfv4mzfhawmQJa'
     'R169bzvcyqpqYmSbLGGmvM9zkdOnTIaaedtsTnWxr9z//8T7lHoEC33HJLuUegUA3zz7WG6'
     '7JyD0ChhpV7gMJ16NBhvpfa8%2B0IkCVks802y2OPPZapU6dmxRVXrF3%2B3HPPJUk6depU'
     '7zmtW7fOI488UhspAAAsfVq3bi1AvoOqUqlUKvcQlWj48OHZaqutcsEFF%2BT4449P8tk3o'
     '2%2B00UZp1apVnn766TJPCAAAxXMGZAnZcssts88%2B%2B%2BS3v/1t3n///bRr1y5DhgzJ'
     '2LFjc%2B2115Z7PAAAKAtnQJagWbNm5bTTTstf/vKXTJkyJZtuumnOPvvsdOvWrdyjAQBAW'
     'QgQAACgML4HBAAAKIwAYaFMmzYtZ5xxRrp3755VVlkljRo1ypAhQ%2Bptd/DBB6dRo0b1Hh'
     'tssMF89/vnP/85G2ywQZo2bZr27dvn0ksvXai5/v3vf2f//ffP6quvnhVWWCHt27fPqaeeu'
     'kjvkf%2B1NB7vN954IwcccEDWWmutrLDCCvnhD3%2BY448/PpMnT17k98lnlsTxvuyyy7LP'
     'Pvtk7bXXTqNGjdK3b9%2BFmqlUKuX8889P27Zt07Rp02y66ab529/%2Btsjvkf%2B1tB3v1'
     '157LSeeeGI6deqUlVZaKWussUZ69OiRF1544Tu9Tz6ztB3vr7rhhhvSqFGjOp8cSuVyEzoL'
     'ZeLEiTn77LOzzjrrpFOnTnnsscdSVVU1320bN26cP//5z3WWrbzyyvW2u%2BKKK/LrX/86e'
     '%2B%2B9d0444YQ88cQTOfroozN9%2BvSceOKJ3zjTyJEj8%2BMf/zhrrbVWTjjhhFRXV%2B'
     'edd97JuHHjFu1NUmtpO94TJkzIVlttleWWWy6HH3541lprrYwcOTKXXnppHn300bzwwgsLn'
     'I9vtiSO9/nnn59PPvkkW265ZSZMmLDQx6d///4577zzcuihh6ZLly654447sv/%2B%2B6eq'
     'qir77bffQu2Lupa243311Vfnmmuuyd57750jjzwyH374Ya644opstdVWuf/%2B%2B7PTTjs'
     't3BukjqXteH/ZJ598khNPPDHNmjXzZ3hDUYKFMGvWrNJ7771XKpVKpX/%2B85%2Blqqqq0p'
     'AhQ%2Bptd9BBB5VWXHHFb9zf9OnTS9XV1aWePXvWWd67d%2B9S8%2BbNS1OmTPna58%2BdO'
     '7e00UYblbbeeuvSzJkzF%2BKd8G0sbcf7yiuvLFVVVZXuu%2B%2B%2BOsvPOOOMUlVVVWnk'
     'yJHfOAMLtriPd6lUKo0dO7b2n5s3b17q27fvt55n3LhxpeWWW6501FFH1Vm%2Bww47lNZaa'
     '63S3Llzv/W%2BqG9pO94vvPBCadq0aXWWffDBB6XVVluttN12233r/TB/S9vx/rKTTjqp1K'
     'FDh9r/LaDyuQSLhbL88stntdVWS/LZpRFfp1QqZd68efn4448XuM2jjz6ayZMn5/DDD6%2B'
     'z/Igjjsi0adNy7733fu1rPPjgg3nllVdyxhlnpHHjxpk%2BfXrmzp37Ld8N32RpO95NmjRJ'
     'ktqZvvCDH/wgSdK0adOvfT5fb3Ef7yRZa621FnmeO%2B%2B8M3PmzKn3%2B/LrX/8648aNy'
     'zPPPLPI%2B2bpO96dO3fOCiusUGfZKqusku222y6jR49e5P3ymaXteH9hzJgxGThwYC6%2B'
     '%2BOIss8wy33l/fD8IEJaY6dOnZ6WVVkqLFi1SXV2dI488MtOmTauzzYgRI5IkW2yxRZ3ln'
     'Tt3TqNGjTJy5MivfY2HH344yWd/sG6xxRZp3rx5mjVrll69emXKlCmL8d3wTYo43nvttVfW'
     'X3/9HHPMMXnuuecybty43HfffRkwYED22GOPtG/ffvG%2BKRbo2xzv72rEiBFp3rx5OnToU'
     'Gd5ly5dkuQbf19YfIo43gsyYcKEtGrVqpDX4jNFHu9%2B/fplxx13TPfu3ZfI/lk6uQeEJW'
     'KNNdbISSedlM6dO2fevHkZOnRo/vSnP2XUqFF57LHHav9fjpqamiyzzDJZddVV6zx/%2BeW'
     'XT3V1dd59992vfZ0xY8YkSfbdd9/ssssuOeWUUzJy5Micc845%2Bc9//pOnnnpqybxB6ijq'
     'eK%2Bwwgp56qmn0rNnz2y99da1yw8%2B%2BOBcddVVi/%2BNMV/f9nh/VzU1NVl99dXrLW/'
     'dunWSfOPvC4tHUcd7fp588sk8%2B%2ByzOe2005bYa1BXkcf73nvvzUMPPZSXXnppse2T7w'
     'cBwhIxYMCAOj/vu%2B%2B%2Bad%2B%2BfU455ZTccssttTePzpgxI8svv/x899G4cePMmDH'
     'ja1/nk08%2BSfLZN89fd911SZI99tgjK6ywQn77299m2LBhblwsQFHHe9q0aenZs2fefvvt'
     '/PGPf8w666yTJ554IoMGDUp1dXUuuOCCxfOG%2BFrf9nh/VzNmzEjjxo3rLf/iUrxv%2Bn1'
     'h8SjqeH/V%2B%2B%2B/n/333z/rrrvut/pAEhaPoo73p59%2BmmOPPTa//vWv653lpPK5BI'
     'vCHHvssWnUqFGGDRtWu6xp06b59NNP57v9zJkzv/Ga/i/W9%2BrVq87y/fffP0lcI15GS%2'
     'BJ4X3bZZXn22Wdzzz335KijjspPf/rTXHjhhTn11FPzhz/8wXXiZTS/4/1dNW3aNDNnzqy3'
     '/Itl7vkpnyVxvL9s2rRp6dGjR6ZNm5Y777yz3r0hFGtJHO%2BLL744kydPzllnnbXY9sn3h'
     'wChME2aNMkqq6xS5/saWrdunblz52bSpEl1tv30008zefLkrLHGGl%2B7zy/Wf/UyjS%2Bu'
     'F3YfSPksieP91FNPZc0110znzp3rLO/Zs2dKpZLgLKP5He/vqnXr1pkwYUK95TU1NUnyjb8'
     'vLDlL4nh/4dNPP82ee%2B6Z//mf/8mdd96Zjh07LvbXYOEs7uP90Ucf5Xe/%2B11%2B%2Bc'
     'tf5sMPP8zbb7%2Bdt99%2BO5988klKpVLeeeedvP/%2B%2B4vltVg6CRAKM3Xq1EyaNKnOz'
     'YSbbbZZkuT555%2Bvs%2B0///nPzJs3L506dfrafX5xM/NXv/Pji2vD3bhYPkvieM%2BePT'
     'tz5syZ7/Ik811HMeZ3vL%2BrzTbbLNOnT693Zuu5555Lkm/8fWHJWRLHO0nmzZuXPn365NF'
     'HH81f//rXbL/99ot1/yyaxX28p0yZkmnTpuX888/PuuuuW/u47bbbMn369LRt2za/%2BtWv'
     'FstrsXQSICx2s2bNytSpU%2BstP/vss5Okzidd7LjjjllllVVy2WWX1dn2sssuS7NmzbLbb'
     'rvVLvv444/z2muv1flYwN133z2NGzfOtddeW%2BdjBa%2B%2B%2BuokSbdu3RbPm2KBijze'
     'nTt3znvvvZfHH3%2B8zvNvvPHGJP8bOCw5C3O8F8aC/v1ebrnl8qc//al2WalUyuWXX542b'
     'dpkm222WaTX4tsr8ngnyVFHHZWbbropf/rTn/L//X//3yLtm0VX1PFeffXVc/vtt%2BeOO%'
     '2B6o8%2BjatWuaNGmSO%2B64I7/97W8X/Y2w1HMTOgvt0ksvzYcfflh7luGuu%2B7K2LFjk'
     'yRHH310Jk%2BenM022yz7779/1l9//STJAw88kKFDh2aXXXbJ7rvvXruvJk2a5Oyzz84RRx'
     'yRfffdNzvvvHOefPLJ3HDDDRkwYEBatGhRu%2B1tt92Wn//857n22mtz0EEHJfnsD7FTTjk'
     'lp59%2Berp3757dd989o0aNytVXX539998/m2%2B%2BeVH/tVSspel4H3744bn88svTs2fP'
     'HHXUUVl77bXz%2BOOP529/%2B1t23nnn2o9nZdEtzuOdJHfffXdGjRqV5LMzVaNGjcrvfve'
     '7JJ8FxsYbb5xk/sd7zTXXTL9%2B/XLBBRdk9v/f3t0GRVX9cQD/3uva7sIuArKYmsqDK8nD'
     'ZLhRDohAJjpDmsCgvlAWM7UXTo4zOkOlgSAxPmSlDk7ayBTDZD5mWaYpUAZTMA4j6FSggJl'
     'Ngw/rCDEjyO//4j9sXnfxKVw0v5%2BZnWHP/d1zzj33Db979pzb2QmbzYb9%2B/fj%2BPHj'
     'KC0t5RuT%2B8DDdL/ff/99FBUVYcKECTAajSgpKdHUnZqayrUg/9LDcr%2BNRqNLXT1xP//'
     '8M6ZPn/5gBoAeHv3x9kN6tAUFBYmiKKIoiqiqKqqqOv9uaWkRh8Mhc%2BfOFavVKt7e3mIw'
     'GCQqKkoKCwulq6vLbZ3btm2Tp59%2BWvR6vVitVvnggw9cYoqLi0VVVbdvbt28ebOEhYXJE'
     '088IaNGjZJVq1b12hbdm4ftfv/666%2BSnp4u/v7%2BMnDgQAkODpYVK1ZIR0fHA7n%2Bx0'
     '1f32%2B73d5rfTff297ud3d3t7z77rsSFBQker1eoqKipLS09IGPw%2BPiYbrfdrtdc87Nn'
     '57%2B0L/zMN1vd%2Bx2%2B12/hZ0ebYrIHV6HSURERERE1Ee4BoSIiIiIiDyGCQgREREREX'
     'kMExAiIiIiIvIYJiBEREREROQxTECIiIiIiMhjmIAQEREREZHHMAEhIiIiIiKPYQJCRERER'
     'EQewwSEiIiIiIg8hgkIERHRA2K322E2m/u7G0REDxUmIEREfaSurg7p6ekICgqC0WjEU089'
     'hSlTpmDz5s393bVHWnl5OVRVxd69e/u7K251dHQgJycHFRUVbo8riuLhHhERPdyYgBAR9YH'
     'KykrYbDbU1dVh4cKF2LJlC1577TWoqooPP/ywv7tHD1B7eztWr17dawIiIh7uERHRw03X3x'
     '0gIvovWLNmDfz8/FBdXQ0fHx/NsYsXL/ZTr8iTmGgQEd0dzoAQEfWBM2fOICIiwiX5AICAg'
     'ACXspKSEowfPx5eXl4YPHgw5syZg/Pnz7vEffTRRwgNDYWXlxeef/55/PDDD0hISEBiYqIz'
     'pri4GKqq4ty5c5pze3669P3332vKf/rpJ0ydOhW%2Bvr7w9vZGQkICKisrNTE5OTlQVRVnz'
     'pyB3W6Hn58ffH19MX/%2BfHR0dLi9npiYGHh7e8Pf3x%2BTJk3CkSNHNDHffPMNJk6cCJPJ'
     'BB8fH6SkpOD06dNuRvP%2BOBwOLF26FCNGjIDBYIDVasXatWs1iUFzczNUVcWGDRucY2swG'
     'BATE4OamhqXOnft2oXw8HAYjUZERUVh3759sNvtCA4OdtYXGBgIAMjNzYWqqlBVFatXr3bW'
     'oSgKLly4gFdeeQVmsxmBgYFYvnw5uru7%2B%2BzaiYgeJUxAiIj6QFBQEGpqanDq1Kk7xq5'
     'ZswaZmZkICwvDxo0bsXTpUhw9ehTx8fG4evWqM%2B7jjz/G4sWLMWzYMKxbtw6xsbGYMWMG'
     'zp8/f9/rCo4dO4b4%2BHi0tbUhJycHBQUFcDgcSEpKQnV1tUt8RkYG2tvbUVhYiIyMDBQXF'
     'yM3N1cTk5ubi3nz5kGv1yMvLw%2BrV6/GiBEjUFZW5oz59NNPkZKSAh8fH6xduxYrV67E6d'
     'OnERcXh5aWlvu6lpv9/fffmDRpEkpLS2G327Fp0ybExsYiOzsby5Ytc4kvLS3F%2BvXr8fr'
     'rryM/Px/Nzc1ITU1FV1eXM%2BbgwYOYNWsW9Ho9CgsLkZqaigULFuDEiRPO8Q8MDERRUREA'
     'IDU1FSUlJSgpKUFqaqqznq6uLiQnJ8NisWDDhg2YNGmSMwEiInosCRER/WtHjhwRnU4nOp1'
     'OJkyYICtWrJDDhw9LZ2enJq65uVkGDBgghYWFmvL6%2BnoZOHCgFBQUiIjI9evXJTAwUKKj'
     'ozV1bNu2TRRFkcTERGfZjh07RFEUaWlp0dRZVlYmiqJIRUWFiIh0d3eL1WqVadOmaeI6Ojo'
     'kJCREpkyZ4ix75513RFEUWbBggSY2NTVVAgICnN8bGhpEVVVJS0vrdWyuXbsmvr6%2BsmjR'
     'Ik35X3/9Jb6%2BvrJw4cJez735Ovbs2dNrTF5enphMJmlsbNSUZ2dni06nk99//11ERJqam'
     'kRRFLFYLOJwOJxxBw4cEEVR5KuvvnKWRUVFyciRI6W9vd1ZVlFRIYqiSHBwsLOstbVVFEWR'
     '3Nxcl35lZmaKoiiSn5%2BvKY%2BOjhabzXbb6yYi%2Bq/iDAgRUR%2BYPHkyqqqqMH36dJw'
     '8eRLr1q1DcnIyhg8fji%2B//NIZt3fvXogI0tPTcfHiRednyJAhGD16tHPWoKamBq2trVi8'
     'eDF0un%2BW69ntdgwaNOi%2B%2BlhbW4vGxkbMmTNH03ZbWxuSkpJcfqoFAIsXL9Z8j4uLw'
     '6VLl9DW1gYA2L9/P0QEq1at6rXdI0eO4OrVq5g9e7amXVVVERMTo5kpuV%2B7du1CfHw8fH'
     '19NW28%2BOKLuHHjhsu1zZo1SzOOcXFxAICmpiYAwIULF1BfX4958%2BbBy8vLGRcfH4%2B'
     'oqKh77p%2B7cTx79uw910NE9F/ARehERH3EZrNhz5496OrqQm1tLfbt24eNGzciPT0dtbW1'
     'GDt2LBoaGiAisFqtbuvQ6/UA4PxZ0q1xOp0OISEh99W/hoYGAEBmZqbb44qi4OrVq5p/zEe'
     'OHKmJ8fPzAwBcuXIFJpMJZ86cgcqkSqMAAAWtSURBVKqqCA8Pv2O7SUlJbo/fb0J1axt1dX'
     'WwWCwuxxRFQWtrq6bsdtcF/DP%2Bo0ePdqkvNDQUtbW1d903o9GIwYMHu7TX0xYR0eOGCQg'
     'RUR/T6XSw2Wyw2WwYM2YMsrKysHv3bqxcuRLd3d1QFAWHDh3CgAEDXM41mUx3rF9u2W2pt/'
     'UgN27c0HzvWfS8fv16jBs3zu053t7emu/u%2BuiuD7fT025JSQmefPJJl%2BM3z/DcLxHBl'
     'ClTsGLFCrfHb03k%2BuK67paq8scGREQ3YwJCRPQAjR8/HgDw559/Avj/03MRQVBQUK%2Bz'
     'IAAwatQoAMBvv/2GhIQEZ3lnZyeamprw7LPPOst6nt47HA7Nk/1bF3eHhoYCAMxmc6%2BzE'
     'fcqNDQU3d3dOHXqFJ555hm3MT2zCBaLpc/addePa9eu9Vn9PePfM3tzs8bGRs13vmiQiOje'
     '8LEMEVEf6G0dw9dffw0ACAsLAwCkpaVhwIABLjtJAf9/%2Bn758mUAwHPPPQeLxYKtW7eis'
     '7PTGVNcXKzZKQv4J7G4%2BUV4N27ccNllyWazITQ0FOvXr0d7e7tL%2B7f%2BTOluzJw507'
     'ntbG%2BzB8nJyfDx8UFBQYFml6keffGelIyMDFRVVeHw4cMuxxwOh8ts0J0MGzYMkZGR%2B'
     'OSTTzRjVVFRgfr6ek1szxqR3n5SxQSFiEiLMyBERH1gyZIl6OjowMyZMxEWFobr16%2Bjsr'
     'ISn3/%2BOYKDg5GVlQUACAkJQX5%2BPrKzs9Hc3IwZM2bAbDajqakJ%2B/fvx6JFi7Bs2TL'
     'odDrk5%2Bdj0aJFSEpKQkZGBpqamlBcXOyyBiQiIgIvvPACsrOzcfnyZfj5%2BeGzzz5z%2'
     'BadbURRs374d06ZNQ0REBLKysjBs2DD88ccfKCsrw6BBg3DgwIF7uu7Q0FC89dZbyMvLw8S'
     'JEzFz5kzo9XpUV1dj%2BPDhKCgogNlsRlFREebOnYvo6GjMnj0bAQEBOHfuHA4ePIi4uDhs'
     '2rTpjm3t3r3b7XtD7HY7li9fjgMHDiAlJQV2ux3R0dFob29HXV0d9uzZg5aWFvj7%2B9/Tt'
     'RUUFGDGjBmIjY2F3W7HlStXsGXLFkRGRmqSEqPRiPDwcOzcuRNjxoyBn58foqKiEBERAYAv'
     'KCQictFPu28REf2nHDp0SF599VUZO3asmM1m0ev1MmbMGHnjjTektbXVJX7v3r0yceJEMZl'
     'MYjKZJDw8XJYsWSINDQ2auKKiIgkJCRGDwSAxMTFy/PhxSUhI0GzDKyJy9uxZeemll8RgMM'
     'jQoUPl7bfflu%2B%2B%2B05UVXVuw9ujtrZW0tLSJCAgQAwGgwQHB8vs2bOlrKzMGZOTkyO'
     'qqsqlS5c05%2B7YsUNUVXXZ8nfHjh0SHR0tBoNB/P39JTExUY4ePaqJKS8vl6lTp4qvr68Y'
     'jUaxWq0yf/58OXHixG3Htry8XBRFEVVVRVEUzUdVVfnxxx9FRKStrU3efPNNsVqtotfrxWK'
     'xSFxcnLz33nvOrYx7tuHdsGGDSzvuttLduXOnjB07VvR6vURGRsoXX3whaWlpEh4eromrqq'
     'oSm80mer1eVFV11mO328VsNru01TO%2BRESPI0WEj2aIiB4lCQkJUFUVx44d6%2B%2BuPJb'
     'GjRuHIUOG4Ntvv%2B3vrhARPZK4BoSIiMiNrq4ulzUr5eXlOHnypGZjACIiujdcA0JE9Aji'
     '5PWDd/78eUyePBlz587F0KFD8csvv2Dr1q0YOnSoy4sFiYjo7jEBISJ6xCiKwp2VPMDf3x8'
     '2mw3bt29Ha2srTCYTXn75ZRQWFjq3PiYionvHNSBEREREROQxXANCREREREQewwSEiIiIiI'
     'g8hgkIERERERF5DBMQIiIiIiLyGCYgRERERETkMUxAiIiIiIjIY5iAEBERERGRxzABISIiI'
     'iIij2ECQkREREREHsMEhIiIiIiIPIYJCBERERERecz/AE2W6Y530pZyAAAAAElFTkSuQmCC'
     '"/>')]

if __name__ == '__main__':
    main()
