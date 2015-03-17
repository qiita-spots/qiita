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
from collections import defaultdict

from pyparsing import (alphas, nums, Word, dblQuotedString, oneOf, Optional,
                       opAssoc, CaselessLiteral, removeQuotes, Group,
                       operatorPrecedence, stringEnd, ParseException)

from qiita_db.util import (scrub_data, convert_type, get_table_cols,
                           convert_to_id)
from qiita_db.sql_connection import SQLConnectionHandler
from qiita_db.exceptions import QiitaDBIncompatibleDatatypeError


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
    def __init__(self, tokens):
        self.term = tokens[0]
        # clean all the inputs
        for pos, term in enumerate(self.term):
            self.term[pos] = scrub_data(term)

    def generate_sql(self):
        # we can assume that the metadata is either in required_sample_info
        # or the study-specific table
        column_name, operator, argument = self.term
        argument_type = type(convert_type(argument))

        allowable_types = {int: {'<', '<=', '=', '>=', '>'},
                           float: {'<', '<=', '=', '>=', '>'},
                           str: {'=', 'includes', 'startswith'}}

        if operator not in allowable_types[argument_type]:
            raise QiitaDBIncompatibleDatatypeError(operator, argument_type)

        column_name = 'sr.%s' % column_name.lower()

        if operator == "includes":
            # substring search, so create proper query for it
            return "LOWER(%s) LIKE '%%%s%%'" % (column_name, argument.lower())
        else:
            # standard query so just return it, adding quotes if string
            if argument_type == str:
                argument = ''.join(("'", argument, "'"))
            return ' '.join([column_name, operator, argument])

    def __repr__(self):
        column_name, operator, argument = self.term
        if operator == "includes":
            return "LOWER(%s) LIKE '%%%s%%')" % (column_name, argument.lower())
        else:
            return ' '.join(self.term)


class QiitaStudySearch(object):
    """QiitaStudySearch object to parse and run searches on studies."""
    study_cols = frozenset(get_table_cols('study'))
    req_samp_cols = frozenset(get_table_cols('required_sample_info'))
    prep_info_cols = frozenset(get_table_cols('common_prep_info'))

    def __call__(self, searchstr, user, study=None):
        """parses search string into SQL where clause and metadata information

        Parameters
        ----------
        searchstr : str
            The string to parse
        user : User object
            The user performing the search
        study : Study object, optional
            If passed, only search over this study

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

        Metadata column names and string searches are case-insensitive

        References
        ----------
        .. [1] McGuire P (2007) Getting started with pyparsing.
        """
        sql_where, all_headers, meta_headers = self._parse_search(searchstr)

        # At this point it is possible that a metadata header has been
        # reference more than once in the query. We are explicitly disallowing
        # varchar and int/float mixed searches over the same field right now,
        # so raise malformed query error.
        meta_types = {}
        for header, header_type in all_headers:
            if header not in meta_types:
                meta_types[header] = header_type
            elif meta_types[header] != header_type:
                raise ParseException('Can not search over string and '
                                     'integer/float for same field!')

        # remove metadata headers that come from non-dynamic tables
        # get the list of dynamic table columns for sample + prep templates
        dyn_headers = meta_headers - self.req_samp_cols - self.study_cols - \
            self.prep_info_cols

        if study:
            sql = ["%d" % study.id]
        else:
            # get all study ids that contain metadata categories searched for
            sql = []
            for meta in dyn_headers:
                sql.append("SELECT study_id FROM "
                           "qiita.study_sample_columns WHERE "
                           "lower(column_name) = lower('{0}') and "
                           "column_type in {1}".format(scrub_data(meta),
                                                       meta_types[meta]))
        if user.level == 'user':
            # trim to accessable studies
            sql.append("SELECT study_id FROM qiita.study_users WHERE "
                       "email = '{0}' UNION SELECT study_id "
                       "FROM qiita.study WHERE email = '{0}' OR"
                       " study_status_id = {1}".format(
                           user.id, convert_to_id('public', 'study_status')))
        if sql:
            st_sql = " WHERE srd.study_id in (%s)" % ' INTERSECT '.join(sql)
        else:
            st_sql = ""
        # get all studies and processed_data_ids for the studies
        sql = ("SELECT DISTINCT srd.study_id, array_agg(pt.prep_template_id "
               "ORDER BY srd.study_id) FROM qiita.study_raw_data srd "
               "JOIN qiita.prep_template pt USING (raw_data_id)%s "
               "GROUP BY study_id" % st_sql)
        conn_handler = SQLConnectionHandler()
        studies = conn_handler.execute_fetchall(sql)

        if not studies:
            # No studies found, so no need to continue
            return {}, meta_headers

        # create  the sample finding SQL, getting both sample id and values
        # build the sql formatted list of result headers
        meta_headers = sorted(meta_headers)
        header_info = ['sr.study_id', 'sr.processed_data_id', 'sr.sample_id']
        header_info.extend('sr.%s' % meta.lower() for meta in meta_headers)
        headers = ','.join(header_info)
        conn_handler.create_queue('search')

        for study, prep_templates in studies:

            # build giant join table of all metadata from found studies,
            # then search over that table for all samples meeting criteria
            sql = ["SELECT {0} FROM ("
                   "SELECT * FROM qiita.study s "
                   "RIGHT JOIN qiita.study_processed_data USING (study_id) "
                   "JOIN qiita.required_sample_info USING (study_id) "
                   "JOIN qiita.common_prep_info USING (sample_id) "
                   "JOIN qiita.processed_data USING (processed_data_id) "
                   "JOIN qiita.data_type USING (data_type_id) "
                   "JOIN qiita.sample_{1} USING (sample_id)".format(
                       headers, study)]
            for p in prep_templates:
                sql.append("JOIN qiita.prep_{0} USING (sample_id)".format(p))
            sql.append(") AS sr WHERE")
            sql.append(sql_where)

            conn_handler.add_to_queue('search', ' '.join(sql).format(
                                      ','.join(header_info)))
        results = self._process_to_dict(conn_handler.execute_queue('search'),
                                        len(header_info))
        return results, meta_headers

    def _process_to_dict(self, result, rowlen):
        """Processes results to more usable format

        Returns
        -------
        study_processed : dict of list of list
            found samples belonging to a study, with metadata. Format
            {study_id: [[samp1, m1, m2, m3], [samp2, m1, m2, m3], ...], ...}
        """
        study_processed = defaultdict(list)
        # queue flattens all results, so need to loop by position
        for row in range(0, len(result), rowlen):
            study_processed[result[row]].append(result[row+2:row+rowlen])
        return study_processed

    def _parse_search(self, searchstr):
        # build the parse grammar
        category = Word(alphas + nums + "_")
        seperator = oneOf("> < = >= <= !=") | CaselessLiteral("includes") | \
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

        # this lookup will be used to select only studies with columns
        # of the correct type
        type_lookup = {
            int: "('integer', 'float8')",
            float: "('integer', 'float8')",
            str: "('varchar')"}

        # parse out all metadata headers we need to have in a study, and
        # their corresponding types
        all_headers = [(c[0][0].term[0],
                        type_lookup[type(convert_type(c[0][0].term[2]))])
                       for c in
                       (criterion + optional_seps).scanString(searchstr)]
        meta_headers = set(h[0] for h in all_headers)

        return sql_where, all_headers, meta_headers
