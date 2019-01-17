from qiita_db.sql_connection import TRN

with TRN:
    sql = """SELECT DISTINCT table_name
             FROM information_schema.columns
             WHERE table_name LIKE '%_bk'"""
    TRN.add(sql)
    tables = ['qiita.%s' % t for t in TRN.execute_fetchflatten()]

chunk_size = 200
for i in range(0, len(tables), chunk_size):
    chunk = tables[i:chunk_size+i]
    sql = "DROP TABLE %s" % ', '.join(chunk)
    with TRN:
        TRN.add(sql)
        TRN.execute()
        TRN.commit()
