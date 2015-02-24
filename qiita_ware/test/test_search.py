from unittest import TestCase, main

from qiita_core.util import qiita_test_checker
from qiita_db.user import User
from qiita_ware.search import search, filter_by_processed_data, count_metadata


@qiita_test_checker()
class SearchTest(TestCase):
    """Tests that the search helpers work as expected"""

    def test_search(self):
        # make sure the passthrough doesn't error
        search('study_id = 1', User('test@foo.bar'))
        search('study_id = 1', User('test@foo.bar'), True, 1)

    def test_filter_by_processed_data(self):
        results, meta_cols = search('study_id = 1', User('test@foo.bar'))
        study_proc_ids, proc_data_samples = filter_by_processed_data(results)
        exp_spid = {1: {'18S': [1]}}
        exp_pds = {1: [['1.SKM7.640188', 1], ['1.SKD9.640182', 1],
                       ['1.SKM8.640201', 1], ['1.SKB8.640193', 1],
                       ['1.SKD2.640178', 1], ['1.SKM3.640197', 1],
                       ['1.SKM4.640180', 1], ['1.SKB9.640200', 1],
                       ['1.SKB4.640189', 1], ['1.SKB5.640181', 1],
                       ['1.SKB6.640176', 1], ['1.SKM2.640199', 1],
                       ['1.SKM5.640177', 1], ['1.SKB1.640202', 1],
                       ['1.SKD8.640184', 1], ['1.SKD4.640185', 1],
                       ['1.SKB3.640195', 1], ['1.SKM1.640183', 1],
                       ['1.SKB7.640196', 1], ['1.SKD3.640198', 1],
                       ['1.SKD7.640191', 1], ['1.SKD6.640190', 1],
                       ['1.SKB2.640194', 1], ['1.SKM9.640192', 1],
                       ['1.SKM6.640187', 1], ['1.SKD5.640186', 1],
                       ['1.SKD1.640179', 1]]}
        self.assertEqual(study_proc_ids, exp_spid)
        self.assertEqual(proc_data_samples, exp_pds)

    def test_count_metadata(self):
        results, meta_cols = search('study_id = 1 AND ph > 0',
                                    User('test@foo.bar'))
        fullcount, studycount = count_metadata(results, meta_cols)
        expfull = {'study_id': {1: 27}, 'ph': {6.82: 10, 6.8: 9, 6.94: 8}}
        expstudy = {1: {'study_id': {1: 27},
                        'ph': {6.82: 10, 6.8: 9, 6.94: 8}}}
        self.assertEqual(fullcount, expfull)
        self.assertEqual(studycount, expstudy)


if __name__ == '__main__':
    main()
