# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import TestCase, main

from qiita_pet.util import (clean_str, generate_param_str, is_localhost,
                            convert_text_html, get_network_nodes_edges)
from qiita_db.software import DefaultParameters
from qiita_db.artifact import Artifact


class TestUtil(TestCase):
    def test_clean_str(self):
        obs = clean_str("Remove Spaces From:String")
        self.assertEqual(obs, "Remove_Spaces_FromString")

    def test_generate_param_str(self):
        params = DefaultParameters(10)
        obs = generate_param_str(params)
        exp = ("<b>Reference:</b> Greengenes 13_8<br/>"
               "<b>similarity:</b> 0.97<br/>"
               "<b>sortmerna_e_value:</b> 1<br/>"
               "<b>sortmerna_max_pos:</b> 10000<br/>"
               "<b>threads:</b> 1<br/>"
               "<b>sortmerna_coverage:</b> 0.97")
        self.assertEqual(obs, exp)

    def test_is_localhost(self):
        self.assertTrue(is_localhost('127.0.0.1'))
        self.assertTrue(is_localhost('localhost'))
        self.assertTrue(is_localhost('127.0.0.1:21174'))

        self.assertFalse(is_localhost('10.0.0.1'))
        self.assertFalse(is_localhost('10.0.0.1:21174'))

    def test_convert_text_html(self):
        test = ('<b>This is line</b>\nThis is another\n'
                'This is a link: http://test.com')
        exp = ('<b>This is line</b><br/>This is another<br/>'
               'This is a link: <a href="http://test.com">http://test.com</a>')
        obs = convert_text_html(test)
        self.assertEqual(obs, exp)

    def test_get_network_nodes_edges(self):
        graph = Artifact(1).descendants_with_jobs
        obs_nodes, obs_edges, obs_wf = get_network_nodes_edges(graph, True)
        self.assertEqual(len(obs_nodes), 11)
        self.assertEqual(len([x for x in obs_nodes if x[0] == 'job']), 5)
        self.assertEqual(len([x for x in obs_nodes if x[0] == 'artifact']), 6)
        self.assertEqual(len([x for x in obs_nodes if x[0] == 'type']), 0)
        self.assertEqual(len(obs_edges), 10)
        self.assertIsNone(obs_wf)

        # This graph only contains one node - check added to make sure that
        # the graph gets extended accordingly
        graph = Artifact(6).descendants_with_jobs
        obs_nodes, obs_edges, obs_wf = get_network_nodes_edges(
            graph, True, nodes=obs_nodes, edges=obs_edges)
        self.assertEqual(len(obs_nodes), 12)
        self.assertEqual(len([x for x in obs_nodes if x[0] == 'job']), 5)
        self.assertEqual(len([x for x in obs_nodes if x[0] == 'artifact']), 7)
        self.assertEqual(len([x for x in obs_nodes if x[0] == 'type']), 0)
        self.assertEqual(len(obs_edges), 10)
        self.assertIsNone(obs_wf)


if __name__ == "__main__":
    main()
