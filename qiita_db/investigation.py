from __future__ import division

"""
Objects for dealing with Qiita studies

This module provides the implementation of the Investigation class.


Classes
-------
- `Investigation` -- A Qiita investigation class
"""
# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

import qiita_db as qdb

REQUIRED_KEYS = {"name", "description", "contact_person"}


class Investigation(qdb.base.QiitaObject):
    """
    Study object to access to the Qiita Study information

    Attributes
    ----------
    name: str
        name of the investigation
    description: str
        description of what the investigation is investigating
    contact_person: StudyPerson object
    studies: list of Study Objects
        all studies that are part of the investigation

    Methods
    -------
    add_study
        Adds a study to the investigation
    """
    _table = "investigation"

    @classmethod
    def create(cls, owner, info, investigation=None):
        """Creates a new investigation on the database"""
        raise NotImplementedError()

    @classmethod
    def delete(cls, id_):
        """Deletes an investigation on the database"""
        raise NotImplementedError()

    @property
    def name(self):
        raise NotImplementedError()

    @name.setter
    def name(self, value):
        raise NotImplementedError()

    @property
    def description(self):
        raise NotImplementedError()

    @description.setter
    def description(self, value):
        raise NotImplementedError()

    @property
    def contact_person(self):
        raise NotImplementedError()

    @contact_person.setter
    def contact_person(self, value):
        raise NotImplementedError()
