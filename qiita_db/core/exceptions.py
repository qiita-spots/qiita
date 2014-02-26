__author__ = "Jose Antonio Navas Molina"
__copyright__ = "Copyright 2013, The Qiita project"
__credits__ = ["Jose Antonio Navas Molina"]
__license__ = "BSD"
__version__ = "0.1.0-dev"
__maintainer__ = "Jose Antonio Navas Molina"
__email__ = "josenavasmolina@gmail.com"

from qiita_core.exceptions import QiitaError


class QiitaDBError(QiitaError):
    """Base class for all Qiita-db exceptions"""
    pass


class QiitaDBNotImplementedError(QiitaDBError):
    """"""
    pass
