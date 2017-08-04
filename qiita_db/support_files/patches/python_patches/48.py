# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

# replacing all \t and \n for space as those chars brake QIIME

from qiita_db.study import Study
from qiita_db.sql_connection import TRN


def searcher(df):
    search = r"\t|\n"

    return [col for col in df
            if df[col].str.contains(search, na=False, regex=True).any()]


studies = Study.get_by_status('private').union(
    Study.get_by_status('public')).union(Study.get_by_status('sandbox'))

# we will start search using pandas as is much easier and faster
# than using pgsql. remember that to_dataframe actually transforms what's
# in the db
to_fix = []
for s in studies:
    st = s.sample_template
    if st is None:
        continue
    cols = searcher(st.to_dataframe())
    if cols:
        to_fix.append((st, cols))

    for pt in s.prep_templates():
        if pt is None:
            continue
        cols = searcher(pt.to_dataframe())
        if cols:
            to_fix.append((pt, cols))


# now let's fix the database and regenerate the files
for infofile, cols in to_fix:
    with TRN:
        for col in cols:
            # removing tabs
            sql = """UPDATE qiita.{0}{1}
                        SET {2} = replace({2}, chr(9), ' ')""".format(
                            infofile._table_prefix, infofile.id, col)
            TRN.add(sql)

            # removing enters
            sql = """UPDATE qiita.{0}{1}
                        SET {2} = regexp_replace(
                            {2}, E'[\\n\\r\\u2028]+', ' ', 'g' )""".format(
                            infofile._table_prefix, infofile.id, col)
            TRN.add(sql)

        TRN.execute()

    infofile.generate_files()
