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
from .sql_connection import TRN


class Ontology(QiitaObject):
    """Object to access ontologies and associated terms from the database

    Attributes
    ----------
    terms
    shortname
    """
    _table = 'ontology'

    def __contains__(self, value):
        with TRN:
            sql = """SELECT EXISTS (
                        SELECT *
                        FROM qiita.term t
                            JOIN qiita.{0} o ON t.ontology_id = o.ontology_id
                        WHERE o.ontology_id = %s
                            AND term = %s)""".format(self._table)
            TRN.add(sql, [self._id, value])
            return TRN.execute_fetchlast()

    @property
    def terms(self):
        with TRN:
            sql = """SELECT term
                     FROM qiita.term
                     WHERE ontology_id = %s AND user_defined = false"""
            TRN.add(sql, [self.id])
            return TRN.execute_fetchflatten()

    @property
    def user_defined_terms(self):
        with TRN:
            sql = """SELECT term
                     FROM qiita.term
                     WHERE ontology_id = %s AND user_defined = true"""
            TRN.add(sql, [self.id])
            return TRN.execute_fetchflatten()

    @property
    def shortname(self):
        return convert_from_id(self.id, 'ontology')

    def add_user_defined_term(self, term):
        """Add a user defined term to the ontology

        Parameters
        ----------
        term : str
            New user defined term to add into a given ontology
        """
        with TRN:
            # we don't need to add an existing term
            terms = self.user_defined_terms + self.terms

            if term not in terms:
                sql = """INSERT INTO qiita.term
                            (ontology_id, term, user_defined)
                         VALUES (%s, %s, true);"""
                TRN.add(sql, [self.id, term])
                TRN.execute()

    def term_type(self, term):
        """Get the type of a given ontology term

        Parameters
        ----------
        term : str
            String for which the method will check the type

        Returns
        -------
        str
            The term type: 'ontology' if the term is part of the ontology,
            'user_defined' if the term is part of the ontology and was
            user-defined and 'not_ontology' if the term is not part of the
            ontology.
        """
        with TRN:
            sql = """SELECT user_defined FROM
                     qiita.term
                     WHERE term = %s AND ontology_id = %s"""
            TRN.add(sql, [term, self.id])
            result = TRN.execute_fetchindex()

            if not result:
                return 'not_ontology'
            elif result[0][0]:
                return 'user_defined'
            elif not result[0][0]:
                return 'ontology'
