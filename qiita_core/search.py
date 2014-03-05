#!/usr/bin/env python

__author__ = "Jose Antonio Navas Molina"
__copyright__ = "Copyright 2013, The Qiita Project"
__credits__ = ["Jose Antonio Navas Molina", "Joshua Shorenstein"]
__license__ = "BSD"
__version__ = "0.1.0-dev"
__maintainer__ = "Jose Antonio Navas Molina"
__email__ = "josenavasmolina@gmail.edu"
__status__ = "Development"

from json import dumps, loads

from qiita_core.exceptions import QiitaSearchError
OPERATORS = ("AND", "OR", "NOT")
QUERY_TYPES = ("includes", "exact", "starts_with", "ends_with")


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
        return ' '.join([self.field, self.query_type, self.query])

    def dict(self, operator=None):
        """Returns a dictionary ready for serializing into json
        Input:
            operator: (optional) The operator associated with the criterion
        """
        return {"operator": operator,
                "field": self.field,
                "query_type": self.query_type,
                "query": self.query}


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
        """Returns the search string in a human readable way"""
        outstr = [str(self._criteria[0])]
        for op, crit in zip(self._operators, self._criteria[1:]):
            outstr.append(op)
            outstr.append(str(crit))
            outstr.append('\n')
        return ' '.join(outstr)

    def add_criterion(self, criterion, operator):
        """Adds a new criterion to the search

        Inputs:
            criterion: the new criterion to be added to the search
            operator: the operator used in the added criterion
        """
        if operator not in OPERATORS:
            raise QiitaSearchError("Operator not recognised: %s" %
                                   operator)
        self._operators.append(operator)
        self._criteria.append(criterion)

    def remove_criterion(self, criterion):
        """Removes a given criterion from the search

        Inputs:
            criterion: the criterion to be removed
        """
        if criterion not in self._criteria:
            raise QiitaSearchError("Criterion not found in criteria!")
        #need to remove both criterion and operator, if aplicable
        pos = self._criteria.index(criterion)
        self._criteria.remove(criterion)
        if pos > 0:
            del self._operators[pos-1]

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
        json = [self.criterion[0].to_json_str()]
        for pos, criterion in enumerate(self._criteria[1:]):
            json.append(criterion.dict(self._operators[pos]))
        #dump in compact mode because could be sending over internet
        return dumps(json, separators=(',', ':'))

    def load_from_json(self, jsonstr):
        """Loads search criterion from json and adds to existing ones
        Input:
            jsonstr: json sring formatted by to_json_str function
        """
        json = loads(jsonstr)
        for crit in json:
            criterion = QiitaSearchCriterion(crit["field"], crit["query_type"],
                                             crit["query"])
            self._criteria.append(criterion)
            if crit["operator"] is None and len(self._operators) != 0:
                #assume it's an AND when adding first item
                self._operators.append("AND")
            elif crit["operator"] is not None:
                self._operators.append(crit["operator"])
