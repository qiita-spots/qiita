from unittest import TestCase, main

from qiita_core.util import qiita_test_checker


@qiita_test_checker()
class TestSQL(TestCase):
    """Tests that the database triggers and procedures work properly"""
    def test_collection_job_trigger_bad_insert(self):
        # make sure an incorrect job raises an error
        with self.assertRaises(ValueError):
            self.conn_handler.execute(
                'INSERT INTO qiita.collection_job (collection_id, job_id) '
                'VALUES (1, 3)')
        obs = self.conn_handler.execute_fetchall(
            'SELECT * FROM qiita.collection_job')
        exp = [[1, 1]]
        self.assertEqual(obs, exp)

    def test_collection_job_trigger(self):
        # make sure a correct job inserts successfully
        self.conn_handler.execute(
            'INSERT INTO qiita.collection_job (collection_id, job_id) '
            'VALUES (1, 2)')
        obs = self.conn_handler.execute_fetchall(
            'SELECT * FROM qiita.collection_job')
        exp = [[1, 1], [1, 2]]
        self.assertEqual(obs, exp)

if __name__ == '__main__':
    main()
