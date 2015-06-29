# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

r"""
Ontology and Controlled Vocabulary objects (:mod:`qiita_db.study`)
==================================================================

.. currentmodule:: qiita_db.ontology

This module provides the encapsulation of an ontology. The resulting object can
be used to interrogate the terms in an ontology.

Classes
-------

.. autosummary::
   :toctree: generated/

   Ontology
"""

from __future__ import division

from .base import QiitaObject
from .util import convert_from_id
from .sql_connection import SQLConnectionHandler


class Ontology(QiitaObject):
    """Object to access ontologies and associated terms from the database

    Methods
    -------
    contains
    terms
    user_defined_terms
    shortname
    add_user_defined_term
    term_type
    """
    _table = 'ontology'

    def contains(self, term, trans=None):
        """Checks if the ontology contains the term `term`

        Parameters
        ----------
        term : str
            The term to be checked
        trans : Transaction, optional
            Transaction in which this method should be executed

        Returns
        -------
        bool
            True if the ontology contains the term `term`. False otherwise.
        """
        trans = trans if trans is not None else Transaction("contains_%s"
                                                            % self._id)
        with trans:
            sql = """SELECT EXISTS (
                        SELECT *
                        FROM qiita.term
                            JOIN qiita.{0} USING (ontology_id)
                        WHERE ontology_id = %s AND term = %s
                    )""".format(self._table)
            trans.add(sql, [self._id, term])
            return trans.execute()[-1][0][0]

    def terms(self, trans=None):
        """Get the terms of the ontology

        Parameters
        ----------
        trans : Transaction, optional
            Transaction in which this method should be executed

        Returns
        -------
        list of str
            The terms of the ontology
        """
        trans = trans if trans is not None else Transaction("terms"
                                                            % self._id)
        with trans:
            sql = """SELECT term FROM qiita.term WHERE ontology_id = %s AND
                     user_defined = false"""
            trans.add(sql, [self.id])
            return [row[0] for row in trans.execute()[-1]]

    def user_defined_terms(self, trans=None):
        """Get the user-defined terms of the ontology

        Parameters
        ----------
        trans : Transaction, optional
            Transaction in which this method should be executed

        Returns
        -------
        list of str
            The user-defined terms of the ontology
        """
        trans = trans if trans is not None else Transaction(
            "user_defined_terms" % self._id)
        with trans:
            sql = """SELECT term FROM qiita.term WHERE ontology_id = %s AND
                     user_defined = true"""
            trans.add(sql, [self.id])
            return [row[0] for row in trans.execute()[-1]]

    def shortname(self, trans=None):
        """Return the short name of the ontology

        Parameters
        ----------
        trans : Transaction, optional
            Transaction in which this method should be executed

        Return
        ------
        str
            The short name of the ontology
        """
        trans = trans if trans is not None else Transaction("shortname"
                                                            % self._id)
        with trans:
            return convert_from_id(self.id, 'ontology', trans=trans)

    def add_user_defined_term(self, term, trans=None):
        """Add a user defined term to the ontology

        Parameters
        ----------
        term : str
            New user defined term to add into a given ontology
        trans : Transaction, optional
            Transaction in which this method should be executed
        """
        trans = trans if trans is not None else Transaction(
            "add_user_defined_term_%s" % self._id)

        with trans:
            # we don't need to add an existing term
            terms = self.user_defined_terms(trans=trans) + self.terms(
                trans=trans)

            if term not in terms:
                sql = """INSERT INTO qiita.term
                         (ontology_id, term, user_defined)
                         VALUES
                         (%s, %s, true);"""
                trans.add(sql, [self.id, term])
                trans.execute()

    def term_type(self, term, trans=None):
        """Get the type of a given ontology term

        Parameters
        ----------
        term : str
            String for which the method will check the type
        trans : Transaction, optional
            Transaction in which this method should be executed

        Returns
        -------
        str
            The term type: 'ontology' if the term is part of the ontology,
            'user_defined' if the term is part of the ontology and was
            user-defined and 'not_ontology' if the term is not part of the
            ontology.
        """
        trans = trans if trans is not None else Transaction("term_type_%s"
                                                            % self._id)

        with trans:
            sql = """SELECT user_defined FROM
                     qiita.term
                     WHERE term = %s AND ontology_id = %s
                  """
            trans.add(sql, [term, self.id])
            result = trans.execute()[-1][0][0]

            if result is None:
                return 'not_ontology'
            elif result[0]:
                return 'user_defined'
            elif not result[0]:
                return 'ontology'
