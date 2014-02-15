__author__ = "Jose Antonio Navas Molina"
__copyright__ = "Copyright 2013, The Qiita project"
__credits__ = ["Jose Antonio Navas Molina"]
__license__ = "BSD"
__version__ = "0.1.0-dev"
__maintainer__ = "Jose Antonio Navas Molina"
__email__ = "josenavasmolina@gmail.com"

from qiita_db.core.exceptions import QiitaDBError


class QiitaDBSQLError(QiitaDBError):
    """Base class for all Qiita-db SQL backend errors"""
    pass


class QiitaDBSQLExecutionError(QiitaDBSQLError):
    """Exception for error when executing SQL queries"""
    pass


class QiitaDBSQLParseError(QiitaDBError):
    """Exception for error when parsing files"""
    pass


class QiitaDBSQLConnectionError(QiitaDBError):
    """Exception for error when connecting to the db"""
    pass