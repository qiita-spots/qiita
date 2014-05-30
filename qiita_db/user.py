#!/usr/bin/env python
from __future__ import division

"""
Objects for dealing with Qiita users

This modules provides the implementation of the User class.

Classes
-------
- `User` -- A Qiita user class
"""
# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from .base import QiitaObject
from .exceptions import QiitaDBNotImplementedError

LEVELS = {'admin', 'dev', 'superuser', 'user', 'guest'}


class User(QiitaObject):
    """
    User object to access to the Qiita user information

    Attributes
    ----------
    email
    level
    info
    private_studies
    shared_studies
    private_analyses
    shared_analyses

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

    @staticmethod
    def create(email, password):
        """Creates a new user on the database

        Parameters
        ----------
        email : str
            the email of the user - used for log in
        password :
            the password of the user
        """
        raise QiitaDBNotImplementedError()

    @staticmethod
    def delete(id_):
        """Deletes the user `id` from the database

        Parameters
        ----------
        id_ :
            The object identifier
        """
        raise QiitaDBNotImplementedError()

    def __eq__(self, other):
        return other.id == self.id

    def __ne__(self, other):
        return other.id == self.id

    @property
    def email(self):
        """The email of the user"""
        return self.Id

    @property
    def level(self):
        """The level of privileges of the user"""
        raise QiitaDBNotImplementedError()

    @level.setter
    def level(self, level):
        """ Sets the level of privileges of the user

        Parameters
        ----------
        level : {'admin', 'dev', 'superuser', 'user', 'guest'}
            The new level of the user
        """
        raise QiitaDBNotImplementedError()

    @property
    def info(self):
        """Dict with any other information attached to the user"""
        raise QiitaDBNotImplementedError()

    @info.setter
    def info(self, info):
        """Updates the information attached to the user

        Parameters
        ----------
        info : dict
        """
        raise QiitaDBNotImplementedError()

    @property
    def private_studies(self):
        """Returns a list of private studies owned by the user"""
        raise QiitaDBNotImplementedError()

    @property
    def shared_studies(self):
        """Returns a list of studies shared with the user"""
        raise QiitaDBNotImplementedError()

    @property
    def private_analyses(self):
        """Returns a list of private analyses owned by the user"""
        raise QiitaDBNotImplementedError()

    @property
    def shared_analyses(self):
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
