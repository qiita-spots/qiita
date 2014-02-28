"""
Objects for dealing with Qiita users

This module provides the base object for dealing with Qiita users.
It standardizes the user interface and all the different Qiita-db
backends should inherit from it in order to implement the user object.

The subclasses implementing this object should not provide any extra
public function in order to maintain back-end independence.

Classes
-------
- `QiitaUser` -- A Qiita user class
"""
__author__ = "Jose Antonio Navas Molina"
__copyright__ = "Copyright 2013, The Qiita Project"
__credits__ = ["Jose Antonio Navas Molina", "Joshua Shorenstein"]
__license__ = "BSD"
__version__ = "0.1.0-dev"
__maintainer__ = "Jose Antonio Navas Molina"
__email__ = "josenavasmolina@gmail.edu"
__status__ = "Development"

from .base import QiitaObject
from .exceptions import QiitaDBNotImplementedError

LEVELS = ('admin', 'dev', 'superuser', 'user', 'guest')


class QiitaUser(QiitaObject):
    """
    Base user object to access to the Qiita user information

    Standardizes the QiitaUser interface for all the back-ends.

    Attributes
    ----------
    Email
    Level
    Info
    PrivateStudies
    SharedStudies
    PrivateAnalyses
    SharedAnalyses

    Methods
    -------
    add_private_study(study)
        Adds a new private study to the user

    remove_private_study(study)
        Removes a private study from the user

    add_shared_study(study)
        Adds a new shared study to the user

    remove_shared_study(study)
        Removes a shared study from the user

    add_private_analysis(analysis)
        Adds a new private analysis to the user

    remove_private_analysis(analysis)
        Removes a private analysis from the user

    add_shared_analysis(analysis)
        Adds a new shared analysis to the user

    remove_shared_analysis(analysis)
        Removes a shared analysis from the user
    """

    @property
    def Email(self):
        """The email of the user"""
        return self.Id

    @property
    def Level(self):
        """The level of privileges of the user"""
        raise QiitaDBNotImplementedError()

    @Level.setter
    def Level(self, level):
        """ Sets the level of privileges of the user

        Parameters
        ----------
            level : {'admin', 'dev', 'superuser', 'user', 'guest'}
                The new level of the user
        """
        raise QiitaDBNotImplementedError()

    @property
    def Info(self):
        """Dict with any other information attached to the user"""
        raise QiitaDBNotImplementedError()

    @Info.setter
    def Info(self, info):
        """Updates the information attached to the user

        Parameters
        ----------
            info : dict
        """
        raise QiitaDBNotImplementedError()

    @property
    def PrivateStudies(self):
        """Returns a list of private studies owned by the user"""
        raise QiitaDBNotImplementedError()

    @property
    def SharedStudies(self):
        """Returns a list of studies shared with the user"""
        raise QiitaDBNotImplementedError()

    @property
    def PrivateAnalyses(self):
        """Returns a list of private analyses owned by the user"""
        raise QiitaDBNotImplementedError()

    @property
    def SharedAnalyses(self):
        """Returns a list of analyses shared with the user"""
        raise QiitaDBNotImplementedError()

    def add_private_study(self, study):
        """Adds a new private study to the user

        Parameters
        ----------
            study :
                The study to be added to the private list
        """
        raise QiitaDBNotImplementedError()

    def remove_private_study(self, study):
        """Removes a private study from the user

        Parameters
        ----------
            study :
                The study to be removed from the private list
        """
        raise QiitaDBNotImplementedError()

    def add_shared_study(self, study):
        """Adds a new shared study to the user

        Parameters
        ----------
            study :
                The study to be added to the shared list
        """
        raise QiitaDBNotImplementedError()

    def remove_shared_study(self, study):
        """Removes a shared study from the user

        Parameters
        ----------
            study :
                The study to be removed from the shared list
        """
        raise QiitaDBNotImplementedError()

    def add_private_analysis(self, analysis):
        """Adds a new private analysis to the user

        Parameters
        ----------
            analysis :
                The analysis to be added to the private list
        """
        raise QiitaDBNotImplementedError()

    def remove_private_analysis(self, analysis):
        """Removes a private analysis from the user

        Parameters
        ----------
            analysis :
                The analysis to be removed from the private list
        """
        raise QiitaDBNotImplementedError()

    def add_shared_analysis(self, analysis):
        """Adds a new shared analysis to the user

        Parameters
        ----------
            analysis :
                The analysis to be added to the shared list
        """
        raise QiitaDBNotImplementedError()

    def remove_shared_analysis(self, analysis):
        """Removes a shared analysis from the user

        Parameters
        ----------
            analysis :
                The analysis to be removed from the shared list
        """
        raise QiitaDBNotImplementedError()
