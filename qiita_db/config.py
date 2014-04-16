#!/usr/bin/env python
from __future__ import division

__author__ = "Jose Antonio Navas Molina"
__copyright__ = "Copyright 2013, The Qiita Project"
__credits__ = ["Jose Antonio Navas Molina", "Daniel McDonald"]
__license__ = "BSD"
__version__ = "0.1.0-dev"
__maintainer__ = "Jose Antonio Navas Molina"
__email__ = "josenavasmolina@gmail.edu"
__status__ = "Development"


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
