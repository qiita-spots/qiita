#!/usr/bin/env python

__author__ = ""
__copyright__ = "Copyright 2013, The Qiita Project"
__credits__ = [""]
__license__ = "BSD"
__version__ = "0.1.0-dev"
__maintainer__ = ""
__email__ = ""
__status__ = "Development"

from qiita_db.core.base_api import BaseStorageAPI
from qiita_db.backends.sql.sql_connection import SQLConnectionHandler


class BaseSQLStorageAPI(BaseStorageAPI):
    """"""
    def __init__(self):
        """"""
        self.conn_handler = SQLConnectionHandler()