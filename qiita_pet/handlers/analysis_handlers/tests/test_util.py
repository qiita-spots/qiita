# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import main, TestCase

from tornado.web import HTTPError

from qiita_db.user import User
from qiita_db.analysis import Analysis
from qiita_pet.handlers.analysis_handlers import check_analysis_access


class UtilTests(TestCase):
    def test_check_analysis_access(self):
        # Has access, so it allows execution
        u = User('test@foo.bar')
        a = Analysis(1)
        check_analysis_access(u, a)

        # Admin has access to everything
        u = User('admin@foo.bar')
        check_analysis_access(u, a)

        # Raises an error because it doesn't have access
        u = User('demo@microbio.me')
        with self.assertRaises(HTTPError):
            check_analysis_access(u, a)


if __name__ == '__main__':
    main()
