r"""
Search objects (:mod: `qiita_db.search`)
====================================

..currentmodule:: qiita_db.search

This module provides functionality for searching studies and samples contained
in the qiita database. All language processing and querying of the database is
contained within each object.

Classes
-------

..autosummary::
    :toctree: generated/

    QiitaStudySearch

Examples
--------
Searches are done using boolean language, with AND, OR, and NOT supported,
as well as ordering through parenthesis. You can search over metadata using the
following operators::

>  <  =  <=  >=  includes

The operators act as they normally do, with includes used for substring
searches.

The object itself is used to search using the call method. In this
example, we will use the complex query::

(sample_type = ENVO:soil AND COMMON_NAME = "rhizosphere metagenome") AND
NOT Description_duplicate includes Burmese

>>> from qiita_db.search import QiitaStudySearch # doctest: +SKIP
>>> search = QiitaStudySearch() # doctest: +SKIP
>>> res, meta = search('(sample_type = ENVO:soil AND COMMON_NAME = '
...                    '"rhizosphere metagenome") AND NOT '
...                    'Description_duplicate includes Burmese',
...                    "test@foo.bar") # doctest: +SKIP
>>> print(res) # doctest: +SKIP
{1: [['SKM4.640180', 'rhizosphere metagenome', 'Bucu Rhizo', 'ENVO:soil'],
     ['SKM5.640177', 'rhizosphere metagenome', 'Bucu Rhizo', 'ENVO:soil'],
     ['SKD4.640185', 'rhizosphere metagenome', 'Diesel Rhizo', 'ENVO:soil'],
     ['SKD6.640190', 'rhizosphere metagenome', 'Diesel Rhizo', 'ENVO:soil'],
     ['SKM6.640187', 'rhizosphere metagenome', 'Bucu Rhizo', 'ENVO:soil'],
     ['SKD5.640186', 'rhizosphere metagenome', 'Diesel Rhizo', 'ENVO:soil']]}
>>> print(meta) # doctest: +SKIP
["COMMON_NAME", "Description_duplicate", "sample_type"]

Note that the userid performing the search must also be passed, so the search
knows what studies are accessable. Also note that the sample list is in the
order of sample ID followed by metadata in the same order as the metadata
headers returned.
"""

# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from pyparsing import (alphas, nums, Word, dblQuotedString, oneOf, Optional,
                       opAssoc, CaselessLiteral, removeQuotes, Group,
                       operatorPrecedence, stringEnd)

from qiita_db.util import scrub_data, typecast_string, get_table_cols
from qiita_db.sql_connection import SQLConnectionHandler
from qiita_db.study import Study
from qiita_db.user import User


# classes to be constructed at parse time, from intermediate ParseResults
class UnaryOperation(object):
    def __init__(self, t):
        self.op, self.a = t[0]


class BinaryOperation(object):
    def __init__(self, t):
        self.op = t[0][1]
        self.operands = t[0][0::2]


class SearchAnd(BinaryOperation):
    def generate_sql(self):
        return "(%s)" % " AND ".join(oper.generate_sql()
                                     for oper in self.operands)

    def __repr__(self):
        return "AND:(%s)" % (",".join(str(oper) for oper in self.operands))


class SearchOr(BinaryOperation):
    def generate_sql(self):
        return "(%s)" % " OR ".join(oper.generate_sql()
                                    for oper in self.operands)

    def __repr__(self):
        return "OR:(%s)" % (",".join(str(oper) for oper in self.operands))


class SearchNot(UnaryOperation):
    def generate_sql(self):
        return "NOT %s" % self.a.generate_sql()

    def __repr__(self):
        return "NOT:(%s)" % str(self.a)


class SearchTerm(object):
    # column names from required_sample_info table
    required_cols = None

    def __init__(self, tokens):
        self.term = tokens[0]
        # clean all the inputs
        for pos, term in enumerate(self.term):
            self.term[pos] = scrub_data(term)
        # create set of columns if needed
        if not self.required_cols:
            self.required_cols = set(get_table_cols("required_sample_info"))

    def generate_sql(self):
        # we can assume that the metadata is either in required_sample_info
        # or the study-specific table
        if self.term[0] in self.required_cols:
            self.term[0] = "r.%s" % self.term[0].lower()
        else:
            self.term[0] = "s.%s" % self.term[0].lower()

        if self.term[1] == "includes":
            # substring search, so create proper query for it
            return "%s LIKE '%%%s%%'" % (self.term[0], self.term[2])
        else:
            # standard query so just return it, adding quotes if string
            if isinstance(typecast_string(self.term[2]), str):
                self.term[2] = ''.join(("'", self.term[2], "'"))
            return ' '.join(self.term)

    def __repr__(self):
        if self.term[1] == "includes":
            return "%s LIKE '%%%s%%')" % (self.term[0], self.term[2])
        else:
            return ' '.join(self.term)


class QiitaStudySearch(object):
    """QiitaStudySearch object to parse and run searches on studies."""

    # column names from required_sample_info table
    required_cols = None

    def __init__(self):
        if not self.required_cols:
            self.required_cols = set(get_table_cols("required_sample_info"))

    def __call__(self, searchstr, user):
        """Runs a Study query and returns matching studies and samples

        Parameters
        ----------
        searchstr : str
            Search string to use
        user : str
            User making the search. Needed for permissions checks.

        Returns
        -------
        dict
            Found samples in format
            {study_id: [[samp_id1, meta1, meta2, ...],
                        [samp_id2, meta1, meta2, ...], ...}
        list
            metadata column names searched for

        Notes
        -----
        Metadata information for each sample is in the same order as the
        metadata columns list returned

        Metadata column names and string searches are case-sensitive
        """
        study_sql, sample_sql, meta_headers = \
            self._parse_study_search_string(searchstr)
        conn_handler = SQLConnectionHandler()
        # get all studies containing the metadata headers requested
        study_ids = {x[0] for x in conn_handler.execute_fetchall(study_sql)}
        # strip to only studies user has access to
        userobj = User(user)
        study_ids = study_ids.intersection(Study.get_public() +
                                           userobj.private_studies +
                                           userobj.shared_studies)
        results = {}
        # run search on each study to get out the matching samples
        for sid in study_ids:
            study_res = conn_handler.execute_fetchall(sample_sql.format(sid))
            if study_res:
                # only add study to results if actually has samples in results
                results[sid] = study_res
        return results, meta_headers

    def _parse_study_search_string(self, searchstr):
        """parses string into SQL query for study search

        Parameters
        ----------
        searchstr : str
            The string to parse

        Returns
        -------
        study_sql : str
            SQL query for selecting studies with the required metadata columns
        sample_sql : str
            SQL query for each study to get the sample ids that mach the query
        meta_headers : list
            metadata categories in the query string in alphabetical order

        Notes
        -----
        All searches are case-sensitive

        References
        ----------
        [1] McGuire P (2007) Getting started with pyparsing.
        """
        # build the parse grammar
        category = Word(alphas + nums + "_")
        seperator = oneOf("> < = >= <=") | CaselessLiteral("includes") | \
            CaselessLiteral("startswith")
        value = Word(alphas + nums + "_" + ":" + ".") | \
            dblQuotedString().setParseAction(removeQuotes)
        criterion = Group(category + seperator + value)
        criterion.setParseAction(SearchTerm)
        and_ = CaselessLiteral("and")
        or_ = CaselessLiteral("or")
        not_ = CaselessLiteral("not")
        optional_seps = Optional(and_ | or_ | not_)

        # create the grammar for parsing operators AND, OR, NOT
        search_expr = operatorPrecedence(
            criterion, [
                (not_, 1, opAssoc.RIGHT, SearchNot),
                (and_, 2, opAssoc.LEFT, SearchAnd),
                (or_, 2, opAssoc.LEFT, SearchOr)])

        # parse the search string to get out the SQL WHERE formatted query
        eval_stack = (search_expr + stringEnd).parseString(searchstr)[0]
        sql_where = eval_stack.generate_sql()

        # parse out all metadata headers we need to have in a study
        meta_headers = set(c[0][0].term[0] for c in
                           (criterion + optional_seps).scanString(searchstr))
        all_headers = list(meta_headers)
        # sort headers so tehy return in same order every time. Should be a
        # relatively short list so very quick
        all_headers.sort()

        # create the study finding SQL
        # remove metadata headers that are in required_sample_info table
        meta_headers = meta_headers.difference(self.required_cols)
        # get all study ids that contain all metadata categories searched for
        sql = []
        if meta_headers:
            # have study-specific metadata, so need to find specific studies
            for meta in meta_headers:
                sql.append("SELECT study_id FROM qiita.study_sample_columns "
                           "WHERE column_name = '%s'" % scrub_data(meta))
        else:
            # no study-specific metadata, so need all studies
            sql.append("SELECT study_id FROM qiita.study_sample_columns")
        # combine the query
        study_sql = ' INTERSECT '.join(sql)

        # create  the sample finding SQL, getting both sample id and values
        # build the sql formatted list of metadata headers
        header_info = []
        for meta in all_headers:
            if meta in self.required_cols:
                header_info.append("r.%s" % meta)
            else:
                header_info.append("s.%s" % meta)
        # build the SQL query
        sample_sql = ("SELECT r.sample_id,%s FROM qiita.required_sample_info "
                      "r JOIN qiita.sample_{0} s ON s.sample_id = r.sample_id "
                      "WHERE %s" % (','.join(header_info), sql_where))

        return study_sql, sample_sql, all_headers
