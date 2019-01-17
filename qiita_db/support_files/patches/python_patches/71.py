from qiita_db.sql_connection import TRN


with TRN:
    sql = """SELECT DISTINCT table_name
             FROM information_schema.columns
             WHERE table_name LIKE '%_bk'"""
    TRN.add(sql)
    tables = TRN.execute_fetchflatten()

sql = "DROP TABLE qiita.%s"
for table in tables:
    with TRN:
        TRN.add(sql % table)
        TRN.execute()
