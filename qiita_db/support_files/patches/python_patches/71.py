from qiita_db.sql_connection import TRN


with TRN:
    sql = """SELECT DISTINCT table_name
             FROM information_schema.columns
             WHERE table_name LIKE '%_bk'"""
    TRN.add(sql)
    tables = ['qiita.%s' % t for t in TRN.execute_fetchflatten()]


with TRN:
    sql = "DROP TABLE %s" % ', '.join(tables)
    TRN.add(sql)
    TRN.execute()
