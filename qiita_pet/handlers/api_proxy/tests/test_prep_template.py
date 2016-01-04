from unittest import TestCase, main

from qiita_pet.handlers.api_proxy.prep_template import prep_template_get_req


class TestPrepAPI(TestCase):
    def test_prep_template_get_req(self):
        obs = prep_template_get_req(1, 'test@foo.bar')
        exp = {
            'status': 'success',
            'message': '',
            'info': {
                '18S': [
                    {'id': 1,
                     'name': 'PREP 1 NAME',
                     'status': 'private',
                     'start_artifact_id': 1,
                     'start_artifact': 'FASTQ',
                     'last_artifact': 'TODO new gui'
                     }]
                }
            }
        self.assertEqual(obs, exp)

    def test_prep_template_get_req_no_access(self):
        obs = prep_template_get_req(1, 'demo@microbio.me')
        exp = {'status': 'error',
               'message': 'User does not have access to study'}
        self.assertEqual(obs, exp)

if __name__ == '__main__':
    main()
