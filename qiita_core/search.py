#!/usr/bin/env python

__author__ = "Jose Antonio Navas Molina"
__copyright__ = "Copyright 2013, The Qiita Project"
__credits__ = ["Jose Antonio Navas Molina", "Joshua Shorenstein"]
__license__ = "BSD"
__version__ = "0.1.0-dev"
__maintainer__ = "Jose Antonio Navas Molina"
__email__ = "josenavasmolina@gmail.edu"
__status__ = "Development"

QUERY_TYPES = ["includes", "exact", "starts_with", "ends_with"]

from qiita_core.exceptions import QiitaSearchError


class QiitaSearchCriterion(object):
    """Models a search criterion"""

    def __init__(self, field, query_type, query):
        """Initializes the criterion object

        Inputs:
            field: the field in which the criterion applies
            query_type: the type of query of the criterion
            query: the actual string containing the query

        Raises a QiitaSearchError if the query type is not recognized
        """
        if query_type not in QUERY_TYPES:
            raise QiitaSearchError("Query type not recognized: %s" %
                                   query_type)
        self.field = field
        self.query_type = query_type
        self.query = query

    def __str__(self):
        """Returns the criterion in a human-readable string"""
        raise NotImplementedError("")


class QiitaSearch(object):
    """Models a search query"""

    def __init__(self, fields, criterion):
        """Initializes the search object

        Inputs:
            fields: the fields in which the search can apply
            criterion: the first criterion of the search

        Raises a QiitaSearchError if the criterion does not apply to the given
            search fields
        """
        if criterion.field not in fields:
            raise QiitaSearchError("Field not recognized")
        self._fields = fields
        self._criteria = [criterion]
        self._operators = []

    def __str__(self):
        """Returns the search string in a json string"""
        raise NotImplementedError("")

    def add_criterion(self, criterion, operator):
        """Adds a new criterion to the search

        Inputs:
            criterion: the new criterion to be added to the search
            operator: the operator used in the added criterion
        """
        raise NotImplementedError("")

    def remove_criterion(self, criterion):
        """Removes a given criterion from the search

        Inputs:
            criterion: the criterion to be removed
        """
        raise NotImplementedError("")

    def get_criteria(self):
        """Iterator to loop through all the criterion on the search

        Yields a pair of (operator, criterion) in which the operator
            for the first criterion is not defined
        """
        yield None, self._criteria[0]

        for op, criterion in zip(self._operators, self._criteria[1:]):
            yield op, criterion

    def to_json_str(self):
        """"""
        pass

    def load_from_json(self):
        """"""
        pass
