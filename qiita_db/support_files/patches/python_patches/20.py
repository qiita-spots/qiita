# March 28, 2015
# Add default analyses for all existing users
from qiita_db.sql_connection import SQLConnectionHandler

conn_handler = SQLConnectionHandler()

sql = "SELECT email FROM qiita.qiita_user"
users = [x[0] for x in conn_handler.execute_fetchall(sql)]

queue = "patch20"
conn_handler.create_queue(queue)

sql = ("INSERT INTO qiita.analysis "
       "(email, name, description, dflt, analysis_status_id) "
       "VALUES (%s, %s, %s, %s, 1)")
for user in users:
    conn_handler.add_to_queue(queue, sql,
                              (user, '%s-dflt' % user, 'dflt', True))

conn_handler.execute_queue(queue)
