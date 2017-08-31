#!/usr/bin/env python
# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from __future__ import division

from redis import Redis

from qiita_core.configuration_manager import ConfigurationManager

qiita_config = ConfigurationManager()

r_client = Redis(host=qiita_config.redis_host,
                 port=qiita_config.redis_port,
                 password=qiita_config.redis_password,
                 db=qiita_config.redis_db)
