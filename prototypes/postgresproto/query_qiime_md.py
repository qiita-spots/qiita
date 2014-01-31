#!/usr/bin/env python

from sys import argv
from re import match
from argparse import ArgumentParser

from psycopg2 import connect

parser = ArgumentParser()
parser.add_argument(
    '-q',
    '--query',
    required=True,
    type=str,
    help=("The query to execute")
)

parser.add_argument(
    '-c',
    '--common_only',
    action='store_true',
    help=("Return only columns common between the studies that the query "
          "can be run on.")
)

def parse_query(q):
    """Parses a query of the form lefthand-side, operator, righthand-side

    Returns LHS, operator, RHS, and datatype. Datatype is determined to be
    either numerical (if casting RHS to a float is successful) or string.

    Currently supported operators: <, >, <=, >=, =

    Only the = operator is suppoted for RHS type string
    """
    pat = '(\w+?)([<>=]+?)([^<>=]+)'
    results = match(pat, q)

    if not results:
        raise ValueError("Could not parse query: %s" %q)

    lhs = results.group(1)
    operator = results.group(2)
    rhs = results.group(3)

    try:
        float(rhs)
        datatype = 'numerical'
    except ValueError:
        # assume the RHS is a string
        datatype = 'string'

    if operator not in ('=', '<=', '>=', '<', '>'):
        raise ValueError("Unknown operator: %s" % operator)

    if datatype == 'string' and operator not in ('=',):
        raise ValueError("Invalid operator %s for string comparison" %
                         operator)

    return lhs, operator, rhs, datatype

def get_all_samples(conn, lhs, operator, rhs, datatype, common_only=True):
    # determine tables that have the column in question with the proper
    # datatype
    find_tables_sql = ("select distinct(table_name) from column_tables where "
                       "lower(column_name) = '%s' and datatype in (%s)")

    if datatype == 'string':
        find_tables_sql = find_tables_sql % (lhs.lower(), "'varchar'")
    elif datatype == 'numerical':
        find_tables_sql = find_tables_sql % (lhs.lower(), "'int', 'float'")

    tables_cursor = conn.cursor()
    tables_cursor.execute(find_tables_sql)
    table_names = [x[0] for x in tables_cursor]

    get_columns_sql = ("select column_name, datatype from column_tables where "
                       "table_name = '%s'")
    columns_cursor = conn.cursor()

    # this cursor is used to go through the final results sets, and is used
    # later
    results_cursor = conn.cursor()
    if common_only:

        # get common columns
        common_columns = set()
        for table_name in table_names:
            columns_cursor.execute(get_columns_sql % table_name)
            columns = [x for x in columns_cursor]
            # if the set is empty, this is the first table, so just add all the
            # columns
            if not common_columns:
                for col_and_type in columns:
                    common_columns.add(col_and_type)
            # otherwise, intersect the current set of columns with the growing
            # set of columns
            else:
                common_columns = common_columns.intersection(set(columns))

        # make the set a list so that we have a consistent ordering
        common_columns_list = list(common_columns)
        common_columns_list = [x[0] for x in common_columns_list]
        # generate the list of columns to fetch in the query
        columns_part = ', '.join([x for x in common_columns_list])

        query_part_template = ("select "+columns_part+" from {0} where "+
                               lhs+" "+operator+" "+rhs)

        query_parts = [query_part_template.format(x)
                       for x in table_names]

        results_cursor.execute(' union '.join(query_parts))
        for row in results_cursor:
            yield dict(zip(common_columns_list, row))
    else:
        for table_name in table_names:
            columns_cursor.execute(get_columns_sql % table_name)
            columns = [x[0] for x in columns_cursor]
            columns_part = ', '.join([x for x in columns])

            q='select %s from %s where '+lhs+' '+operator+' '+rhs
            results_cursor.execute(q % (columns_part, table_name))
            for row in results_cursor:
                yield dict(zip(columns, row))

def main():
    args = parser.parse_args()
    common_only = args.common_only
    query = args.query

    conn = connect(user='adro2179', database='qiime_md')
    cur = conn.cursor()

    lhs, operator, rhs, datatype = parse_query(query)
    for row in get_all_samples(conn, lhs, operator, rhs, datatype,
            common_only):
        print row
        print "\n"

if __name__ == '__main__':
    main()
