#!/usr/bin/env python

# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from __future__ import division

from pyparsing import (alphas, nums, Word, dblQuotedString, oneOf, Optional,
                       opAssoc, CaselessLiteral, removeQuotes, Group,
                       operatorPrecedence, stringEnd)

from qiita_core.exceptions import QiitaSearchError

class QiitaStudySearch(object):
    """Models a search query"""

    def __init__(self, searchstr):
        """Initializes the search object

        Parameters
        ----------
        searchstr : str
            the search string

        Raises
        ------
        ParseError
            Search string can not be parsed
        """
        self.searchstr = searchstr
        self._parse_study_search_string(searchstr)

    def _parse_study_search_string(self, searchstr):
        """parses string into SQL query for study search

        Parameters
        ----------
        searchstr : str
            The string to parse

        Returns
        -------
        tuple of list of indeterminate list nesting
            Parsed information from the query string

        Notes
        -----
        The irst item will be a set of all metadata categories searched for.
        The second item will be the parsed search query in depth first order
        for further query creation

        Citations
        ---------
        [1] McGuire P (2007) Getting started with pyparsing.
        """
        # build the parse grammar
        category = Word(alphas + nums)
        seperator = oneOf("> < = : >= <=") | CaselessLiteral("includes") | \
            CaselessLiteral("startswith")
        value = Word(alphas + nums) | dblQuotedString().setParseAction(
            removeQuotes)
        criterion = Group(category + seperator + value)
        and_ = CaselessLiteral("and")
        or_ = CaselessLiteral("or")
        not_ = CaselessLiteral("not")
        optional_seps = Optional(and_ | or_ | not_)

        # create the grammar for parsing operators AND, OR, NOT
        search_expr = operatorPrecedence(
            criterion, [
                (not_, 1, opAssoc.RIGHT),
                (and_, 2, opAssoc.LEFT),
                (or_, 2, opAssoc.LEFT)])
        print "Search string:", searchstr

        # parse out all metadata headers we need to have in a study
        meta_headers = set(c[0][0][0] for c in
                           (criterion + optional_seps).scanString(searchstr))

        # parse the actual query
        parsed_query = (search_expr + stringEnd).searchString(searchstr)

        print meta_headers
        print parsed_query
        return (meta_headers, parsed_query)

if __name__ == "__main__":
    QiitaStudySearch('pH>5 AND pH < 6 OR author Includes Steve')