#!/usr/bin/env python

__author__ = "Jose Antonio Navas Molina"
__copyright__ = "Copyright 2013, The Qiita Project"
__credits__ = ["Jose Antonio Navas Molina", "Daniel McDonald"]
__license__ = "BSD"
__version__ = "0.1.0-dev"
__maintainer__ = "Jose Antonio Navas Molina"
__email__ = "josenavasmolina@gmail.edu"
__status__ = "Development"


class ConfigurationManager(object):
    """"""
    def __init__(self):
        self.user = 'defaultuser'
        self.database = 'qiime_md'
        self.host = 'localhost'
        self.port = 5432
        self.backend = "SQL"

qiita_db_config = ConfigurationManager()
