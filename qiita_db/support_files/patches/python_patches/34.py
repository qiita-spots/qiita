# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

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

    sql = """INSERT INTO qiita.oauth_software (software_id, client_id)
             VALUES (%s, %s)"""
    TRN.add(sql, [1, client_id])
    TRN.execute()
