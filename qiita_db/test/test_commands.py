from unittest import TestCase, main
from future.utils.six import StringIO
try:
    # Python 2
    from ConfigParser import NoOptionError
except ImportError:
    # Python 3
    from configparser import NoOptionError

from qiita_db.commands import make_study_from_cmd
from qiita_db.study import StudyPerson
from qiita_db.user import User
from qiita_core.util import qiita_test_checker


@qiita_test_checker()
class TestMakeStudyFromCmd(TestCase):
    def setUp(self):
        StudyPerson.create('SomeDude', 'somedude@foo.bar',
                           '111 fake street', '111-121-1313')
        User.create('test@test.com', 'password')
        self.config1 = """
[required]
timeseries_type_id = 1
metadata_complete = True
mixs_compliant = True
number_samples_collected = 50
number_samples_promised = 25
portal_type_id = 3
principal_investigator = SomeDude, somedude@foo.bar
reprocess = False
study_alias = 'test study'
study_description = 'test study description'
study_abstract = 'study abstract'
efo_ids = 1,2,3,4
[optional]
lab_person = SomeDude, somedude@foo.bar
funding = 'funding source'
vamps_id = vamps_id
"""
        self.config2 = """
[required]
timeseries_type_id = 1
metadata_complete = True
number_samples_collected = 50
number_samples_promised = 25
portal_type_id = 3
principal_investigator = SomeDude, somedude@foo.bar
reprocess = False
study_alias = 'test study'
study_description = 'test study description'
study_abstract = 'study abstract'
efo_ids = 1,2,3,4
[optional]
lab_person = SomeDude, somedude@foo.bar
funding = 'funding source'
vamps_id = vamps_id
"""

    def test_make_study_from_cmd(self):
        fh = StringIO(self.config1)
        make_study_from_cmd('test@test.com', 'newstudy', fh)
        sql = ("select study_id from qiita.study where email = %s and "
               "study_title = %s")
        study_id = self.conn_handler.execute_fetchone(sql, ('test@test.com',
                                                            'newstudy'))
        self.assertTrue(study_id is not None)

        fh2 = StringIO(self.config2)
        with self.assertRaises(NoOptionError):
            make_study_from_cmd('test@test.com', 'newstudy2', fh2)

if __name__ == "__main__":
    main()
