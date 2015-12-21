from random import SystemRandom
from string import ascii_letters, digits

from qiita_db.sql_connection import TRN

pool = ascii_letters + digits
client_id = ''.join([SystemRandom().choice(pool) for _ in range(50)])
client_secret = ''.join([SystemRandom().choice(pool) for _ in range(255)])

with TRN:
    sql = """INSERT INTO qiita.oauth_identifiers (client_id, client_secret)
             VALUES (%s, %s)"""
    TRN.add(sql, [client_id, client_secret])
    TRN.execute()

print "Please, add these values to your target gene plugin configuration file:"
print "CLIENT_ID = %s" % client_id
print "CLIENT_SECRET = %s" % client_secret
