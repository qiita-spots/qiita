"""
Objects for dealing with Qiita studies

This module provides the base object for dealing with Qiita studies.
It standardizes the Qiita interface and all the different Qiita-db
backends should inherit from it in order to implement the Study object.

The subclasses implementing this object should not provide any extra
public function in order to maintain back-end independence.

Classes
-------
- `QittaStudy` -- A Qiita study class
"""
__author__ = "Jose Antonio Navas Molina"
__copyright__ = "Copyright 2013, The Qiita Project"
__credits__ = ["Jose Antonio Navas Molina", "Joshua Shorenstein"]
__license__ = "BSD"
__version__ = "0.1.0-dev"
__maintainer__ = "Jose Antonio Navas Molina"
__email__ = "josenavasmolina@gmail.edu"
__status__ = "Development"

from .base import QiitaStatusObject
from .exceptions import QiitaDBNotImplementedError


class QittaStudy(QiitaStatusObject):
    """
    Base study object to access to the Qiita study information

    Standardizes the QittaStudy interface for all the back-ends.

    Attributes
    ----------
    Name
    SampleIds
    Info

    Methods
    -------
    add_samples(samples)
        Adds the samples listed in `samples` to the study

    remove_samples(samples)
        Removes the samples listed in `samples` from the study
    """

    @property
    def Name(self):
        """Returns the name of the study"""
        raise QiitaDBNotImplementedError()

    @Name.setter
    def Name(self, name):
        """Sets the name of the study

        Parameters
        ----------
            name : string
                The new study name
        """
        raise QiitaDBNotImplementedError()

    @property
    def SampleIds(self):
        """Returns the IDs of all samples in study

        The sample IDs are returned as a list of strings in alphabetical order.
        """
        raise QiitaDBNotImplementedError()

    @property
    def Info(self):
        """Dict with any other information attached to the study"""
        raise QiitaDBNotImplementedError()

    @Info.setter
    def Info(self, info):
        """Updates the information attached to the study

        Parameters
        ----------
            info : dict
        """
        raise QiitaDBNotImplementedError()

    def add_samples(self, samples):
        """Adds the samples listed in `samples` to the study
        Parameters
        ----------
            samples : list of strings
                The sample Ids to be added to the study
        """
        raise QiitaDBNotImplementedError()

    def remove_samples(self, samples):
        """Removes the samples listed in `samples` from the study
        Parameters
        ----------
            samples : list of strings
                The sample Ids to be removed from the study
        """
        raise QiitaDBNotImplementedError()
