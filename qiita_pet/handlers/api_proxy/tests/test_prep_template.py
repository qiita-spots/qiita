from unittest import TestCase, main

from qiita_pet.handlers.api_proxy.prep_template import study_prep_proxy


class TestPrepAPI(TestCase):
    def test_study_prep_proxy(self):
        obs = study_prep_proxy(1, 'test@foo.bar')
        exp = {'18S': [
            {'id': 1,
             'name': 'PREP 1 NAME',
             'status': 'private',
             'start_artifact_id': 1,
             'start_artifact': 'FASTQ',
             'last_artifact': 'TODO new gui'
             }]}
        self.assertEqual(obs, exp)

    def test_study_prep_proxy_no_access(self):
        obs = study_prep_proxy(1, 'demo@microbio.me')
        exp = {'status': 'error',
               'message': 'User does not have access to study'}
        self.assertEqual(obs, exp)

if __name__ == '__main__':
    main()
