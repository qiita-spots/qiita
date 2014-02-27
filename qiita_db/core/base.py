"""
Objects for dealing with Qiita-db objects

This module provides base objects for dealing with any qiita-db object that
needs to be stored.

Classes
-------
- `QiitaObject` -- A Qiita object class with a storage id
- `QiitaStatusObject` -- A Qiita object class with a storage id and status
"""

__author__ = "Jose Antonio Navas Molina"
__copyright__ = "Copyright 2013, The Qiita Project"
__credits__ = ["Jose Antonio Navas Molina"]
__license__ = "BSD"
__version__ = "0.1.0-dev"
__maintainer__ = "Jose Antonio Navas Molina"
__email__ = "josenavasmolina@gmail.edu"
__status__ = "Development"


class QiitaObject(object):
    """Base class for any Qiita-db object

    Parameters
    ----------
    id_:
        The object id on the storage system

    Attributes
    ----------
    Id

    Methods
    -------
    create()
        Creates a new object with a new id on the storage system

    delete(id)
        Deletes the object `id` from the storage system
    """

    @staticmethod
    def create():
        """Creates a new object with a new id on the storage system"""
        raise QiitaDBNotImplementedError()

    @staticmethod
    def delete(id_):
        """Deletes the object `id` on the storage system

        Parameters
        ----------
        id_ :
            The object identifier
        """
        raise QiitaDBNotImplementedError()

    def __init__(self, id_):
        """Initializes the object

        Parameters
        ----------
        id_: the object identifier
        """
        self._id = id_

    @property
    def Id(self):
        """The object id on the storage system"""
        return self._id


class QiitaStatusObject(QiitaObject):
    """Base class for any Qiita-db object with a status property

    Attributes
    ----------
    Status :
        The current status of the object
    """

    @property
    def Status(self):
        """String with the current status of the analysis"""
        raise QiitaDBNotImplementedError()

    @Status.setter
    def Status(self, status):
        """Change the status of the analysis

        Parameters
        ----------
        status: String
            The new object status
        """
        raise QiitaDBNotImplementedError()
