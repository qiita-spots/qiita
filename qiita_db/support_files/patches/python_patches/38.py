#
# This is a really heavy step and it will be better not to run after each test
#

# from qiita_db.sql_connection import TRN
#
# with TRN:
#     # select all table and column names from all sample template
#     sql = """SELECT table_name, column_name FROM information_schema.columns
#                 WHERE (table_name LIKE 'sample_%'
#                        OR table_name LIKE 'prep_%')
#                     AND table_name NOT LIKE '%template%'
#                 ORDER BY column_name"""
#     TRN.add(sql)
#
#     for table, column in TRN.execute_fetchindex():
#         sql = "ALTER TABLE qiita.%s ALTER COLUMN %s TYPE VARCHAR" % (table,
#                                                                      column)
#         TRN.add(sql)
#
#     TRN.execute()
