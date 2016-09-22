# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import main, TestCase
from json import loads

from tornado.web import HTTPError

from qiita_db.handlers.tests.oauthbase import OauthTestingBase
from qiita_db.handlers.plugin import _get_plugin
import qiita_db as qdb


class UtilTests(TestCase):
    def test_get_plugin(self):
        obs = _get_plugin("QIIME", "1.9.1")
        exp = qdb.software.Software(1)
        self.assertEqual(obs, exp)

        # It does not exist
        with self.assertRaises(HTTPError):
            _get_plugin("QiIME", "1.9.1")


class PluginHandlerTests(OauthTestingBase):
    def test_get_plugin_does_not_exist(self):
        obs = self.get('/qiita_db/plugins/QIIME/1.9.0/', headers=self.header)
        self.assertEqual(obs.code, 404)

    def test_get_no_header(self):
        obs = self.get('/qiita_db/plugins/QIIME/1.9.0/')
        self.assertEqual(obs.code, 400)

    def test_get(self):
        obs = self.get('/qiita_db/plugins/QIIME/1.9.1/', headers=self.header)
        self.assertEqual(obs.code, 200)
        exp = {
            'name': 'QIIME',
            'version': '1.9.1',
            'description': 'Quantitative Insights Into Microbial Ecology '
                           '(QIIME) is an open-source bioinformatics pipeline '
                           'for performing microbiome analysis from raw DNA '
                           'sequencing data',
            'commands': ['Split libraries FASTQ', 'Split libraries',
                         'Pick closed-reference OTUs'],
            'publications': [{'DOI': '10.1038/nmeth.f.303',
                              'PubMed': '20383131'}],
            'default_workflows': ['FASTQ upstream workflow',
                                  'FASTA upstream workflow',
                                  'Per sample FASTQ upstream workflow'],
            'type': 'artifact transformation',
            'active': False}
        self.assertEqual(loads(obs.body), exp)


if __name__ == '__main__':
    main()
