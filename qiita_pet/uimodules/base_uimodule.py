# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from tornado.web import UIModule


class BaseUIModule(UIModule):
    """Base class for all UiModule so we can centralize functionality"""

    def _is_local(self):
        return ('localhost' in self.request.headers['host'] or
                '127.0.0.1' in self.request.headers['host'])
