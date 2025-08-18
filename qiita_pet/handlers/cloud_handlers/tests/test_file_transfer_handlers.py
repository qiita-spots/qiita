from unittest import main
from os.path import exists, isfile
from os import remove
from shutil import rmtree

from qiita_db.handlers.tests.oauthbase import OauthTestingBase
import qiita_db as qdb


class FetchFileFromCentralHandlerTests(OauthTestingBase):
    def setUp(self):
        super(FetchFileFromCentralHandlerTests, self).setUp()

        self._clean_up_files = []

    def tearDown(self):
        super(FetchFileFromCentralHandlerTests, self).tearDown()
        for fp in self._clean_up_files:
            if exists(fp):
                if isfile(fp):
                    remove(fp)
                else:
                    rmtree(fp)

    def test_get(self):
        endpoint = '/cloud/fetch_file_from_central/'
        obs = self.get(endpoint + 'nonexistingfile', headers=self.header)
        self.assertEqual(obs.code, 403)
        self.assertIn('outside of the BASE_DATA_DIR', obs.reason)

        base_data_dir = qdb.util.get_db_files_base_dir()
        obs = self.get(endpoint + base_data_dir[1:] + '/nonexistingfile',
                       headers=self.header)
        self.assertEqual(obs.code, 403)
        self.assertIn('The requested file is not present', obs.reason)

        obs = self.get(endpoint + base_data_dir[1:] +
                       '/raw_data/FASTA_QUAL_preprocessing.fna',
                       headers=self.header)
        print(obs.__dict__)


if __name__ == "__main__":
    main()
