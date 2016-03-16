from random import SystemRandom
from string import ascii_letters, digits

from qiita_db.sql_connection import TRN

pool = ascii_letters + digits
with TRN:
    # 2 and 3 are the ids of the 2 new software rows, the BIOM and
    # target gene type plugins
    for i in [2, 3]:
        client_id = ''.join([SystemRandom().choice(pool) for _ in range(50)])
        client_secret = ''.join(
            [SystemRandom().choice(pool) for _ in range(255)])

        sql = """INSERT INTO qiita.oauth_identifiers (client_id, client_secret)
                VALUES (%s, %s)"""
        TRN.add(sql, [client_id, client_secret])

        sql = """INSERT INTO qiita.oauth_software (software_id, client_id)
                 VALUES (%s, %s)"""
        TRN.add(sql, [i, client_id])
        TRN.execute()
