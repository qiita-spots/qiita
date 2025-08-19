from unittest import main
from os.path import exists, basename
from os import remove
import filecmp

from qiita_db.handlers.tests.oauthbase import OauthTestingBase
import qiita_db as qdb


class FetchFileFromCentralHandlerTests(OauthTestingBase):
    def setUp(self):
        super(FetchFileFromCentralHandlerTests, self).setUp()

    def test_get(self):
        endpoint = '/cloud/fetch_file_from_central/'
        base_data_dir = qdb.util.get_db_files_base_dir()

        obs = self.get_authed(endpoint + 'nonexistingfile')
        self.assertEqual(obs.status_code, 403)
        self.assertIn('outside of the BASE_DATA_DIR', obs.reason)

        obs = self.get_authed(
            endpoint + base_data_dir[1:] + '/nonexistingfile')
        self.assertEqual(obs.status_code, 403)
        self.assertIn('The requested file is not present', obs.reason)

        obs = self.get_authed(
            endpoint + base_data_dir[1:] +
            '/raw_data/FASTA_QUAL_preprocessing.fna')
        self.assertEqual(obs.status_code, 200)
        self.assertIn('FLP3FBN01ELBSX length=250 xy=1766_01', str(obs.content))


class PushFileToCentralHandlerTests(OauthTestingBase):
    def setUp(self):
        super(PushFileToCentralHandlerTests, self).setUp()

    def test_post(self):
        endpoint = '/cloud/push_file_to_central/'
        base_data_dir = qdb.util.get_db_files_base_dir()

        # create a test file "locally", i.e. in current working directory
        fp_source = 'foo.bar'
        with open(fp_source, 'w') as f:
            f.write("this is a test\n")
        self._files_to_remove.append(fp_source)

        # if successful, expected location of the file in BASE_DATA_DIR
        fp_target = base_data_dir + '/bar/' + basename(fp_source)
        self._files_to_remove.append(fp_target)

        # create a second test file
        fp_source2 = 'foo_two.bar'
        with open(fp_source2, 'w') as f:
            f.write("this is another test\n")
        self._files_to_remove.append(fp_source2)
        fp_target2 = base_data_dir + '/barr/' + basename(fp_source2)
        self._files_to_remove.append(fp_target2)

        # test raise error if no file is given
        obs = self.post_authed(endpoint)
        self.assertEqual(obs.reason, "No files to upload defined!")

        # test correct mechanism
        with open(fp_source, 'rb') as fh:
            obs = self.post_authed(endpoint, files={'bar/': fh})
            self.assertIn('Stored 1 files into BASE_DATA_DIR of Qiita',
                          str(obs.content))
            self.assertTrue(filecmp.cmp(fp_source, fp_target, shallow=False))

        # check if error is raised, if file already exists
        with open(fp_source, 'rb') as fh:
            obs = self.post_authed(endpoint, files={'bar/': fh})
            self.assertIn("already present in Qiita's BASE_DATA_DIR!",
                          obs.reason)

        # test transfer of multiple files
        if exists(fp_target):
            remove(fp_target)
        with open(fp_source, 'rb') as fh1:
            with open(fp_source2, 'rb') as fh2:
                obs = self.post_authed(
                    endpoint, files={'bar/': fh1, 'barr/': fh2})
                self.assertIn('Stored 2 files into BASE_DATA_DIR of Qiita',
                              str(obs.content))
                self.assertTrue(filecmp.cmp(fp_source, fp_target,
                                            shallow=False))
                self.assertTrue(filecmp.cmp(fp_source2, fp_target2,
                                            shallow=False))


if __name__ == "__main__":
    main()
