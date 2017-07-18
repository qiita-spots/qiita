# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import main
from json import loads

from qiita_db.analysis import Analysis
from qiita_db.user import User
from qiita_pet.test.tornado_test_base import TestHandlerBase


class TestShareStudyAjax(TestHandlerBase):

    def test_get(self):
        a = Analysis(1)
        u = User('shared@foo.bar')
        self.assertEqual(a.shared_with, [u])

        # deselecting
        args = {'deselected': u.id, 'id': a.id}
        response = self.get('/analysis/sharing/', args)
        self.assertEqual(response.code, 200)
        exp = {'users': [], 'links': ''}
        self.assertEqual(loads(response.body), exp)
        self.assertEqual(a.shared_with, [])

        # Make sure unshared message added to the system
        self.assertEqual("Analysis 'SomeAnalysis' has been unshared with you.",
                         u.messages()[0][1])

        # selecting
        args = {'selected': u.id, 'id': a.id}
        response = self.get('/analysis/sharing/', args)
        self.assertEqual(response.code, 200)
        exp = {
            'users': ['shared@foo.bar'],
            'links':
                ('<a target="_blank" href="mailto:shared@foo.bar">Shared</a>')}
        self.assertEqual(loads(response.body), exp)
        self.assertEqual(a.shared_with, [u])

        # Make sure shared message added to the system
        self.assertEqual(
            'Analysis <a href="/analysis/description/1">\'SomeAnalysis\'</a> '
            'has been shared with you.', u.messages()[0][1])

    def test_get_no_access(self):
        args = {'selected': 'demo@microbio.me', 'id': 2}
        response = self.get('/analysis/sharing/', args)
        self.assertEqual(response.code, 403)


if __name__ == '__main__':
    main()
