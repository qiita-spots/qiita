# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import TestCase, main

from qiita_core.util import qiita_test_checker
from qiita_db.exceptions import QiitaDBLookupError
from qiita_db.logger import LogEntry


@qiita_test_checker()
class LoggerTests(TestCase):
    def test_create_log_entry(self):
        """"""
        LogEntry.create('Runtime', 'runtime message')
        LogEntry.create('Fatal', 'fatal message', info={1: 2})
        LogEntry.create('Warning', 'warning message', info={9: 0})
        with self.assertRaises(QiitaDBLookupError):
            # This severity level does not exist in the test schema
            LogEntry.create('Chicken', 'warning message',
                            info={9: 0})

    def test_severity_property(self):
        """"""
        log_entry = LogEntry.create('Warning', 'warning test', info=None)
        self.assertEqual(log_entry.severity, 1)

    def test_time_property(self):
        """"""
        sql = "SELECT localtimestamp"
        before = self.conn_handler.execute_fetchone(sql)[0]
        log_entry = LogEntry.create('Warning', 'warning test', info=None)
        after = self.conn_handler.execute_fetchone(sql)[0]
        self.assertTrue(before < log_entry.time < after)

    def test_info_property(self):
        """"""
        log_entry = LogEntry.create('Warning', 'warning test',
                                    info={1: 2, 'test': 'yeah'})
        self.assertEqual(log_entry.info, [{'1': 2, 'test': 'yeah'}])

    def test_message_property(self):
        """"""
        log_entry = LogEntry.create('Warning', 'warning test', info=None)
        self.assertEqual(log_entry.msg, 'warning test')

    def test_add_info(self):
        """"""
        log_entry = LogEntry.create('Warning', 'warning test',
                                    info={1: 2, 'test': 'yeah'})
        log_entry.add_info({'another': 'set', 'of': 'entries', 'test': 3})
        self.assertEqual(log_entry.info, [{'1': 2, 'test': 'yeah'},
                                          {'another': 'set', 'of': 'entries',
                                           'test': 3}])

    def test_clear_info(self):
        """"""
        log_entry = LogEntry.create('Warning', 'warning test',
                                    info={1: 2, 'test': 'yeah'})
        log_entry.clear_info()
        self.assertEqual(log_entry.info, [])

if __name__ == '__main__':
    main()
