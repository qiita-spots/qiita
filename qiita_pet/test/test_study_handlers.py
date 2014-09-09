from unittest import main

try:
    from urllib import urlencode
except ImportError:  # py3
    from urllib.parse import urlencode

from .tornado_test_base import TestHandlerBase


class CreateStudyHandlerTestsDB(TestHandlerBase):
    database = True

    def test_new_person_created(self):
        post_data = {'new_people_names': ['Adam', 'Ethan'],
                     'new_people_emails': ['a@mail.com', 'e@mail.com'],
                     'new_people_affiliations': ['CU Boulder', 'NYU'],
                     'new_people_addresses': ['Some St., Boulder, CO 80305',
                                              ''],
                     'new_people_phones': ['', '']}



class CreateStudyHandlerTestsNoDB(TestHandlerBase):
    def test_page_load(self):
        """Make sure the page loads when no arguments are passed"""
        response = self.get('/create_study/')
        self.assertEqual(response.code, 200)


if __name__ == '__main__':
    main()
