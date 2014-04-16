#!/usr/bin/env python
from __future__ import division

# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------


# Values hard-coded from now - refactor!
class ConfigurationManager(object):
    """"""
    def __init__(self):
        self.user = 'defaultuser'
        self.database = 'qiita'
        self.host = 'localhost'
        self.port = 5432
        self.schema = "qiita"

qiita_db_config = ConfigurationManager()
