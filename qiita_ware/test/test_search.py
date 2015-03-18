from unittest import TestCase, main

from qiita_core.util import qiita_test_checker
from qiita_db.user import User
from qiita_db.study import Study
from qiita_ware.search import search, count_metadata


@qiita_test_checker()
class SearchTest(TestCase):
    """Tests that the search helpers work as expected"""

    def test_search(self):
        # make sure the passthrough doesn't error
        search('study_id = 1', User('test@foo.bar'))
        search('study_id = 1', User('test@foo.bar'), Study(1))

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
