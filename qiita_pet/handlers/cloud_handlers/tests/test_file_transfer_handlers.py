import filecmp
from os import remove, makedirs
from os.path import exists, basename, join, isdir, splitext, abspath
from unittest import main
from shutil import rmtree, make_archive
import hashlib

import qiita_db as qdb
from qiita_db.handlers.tests.oauthbase import OauthTestingBase
from qiita_db.sql_connection import TRN
from qiita_pet.handlers.cloud_handlers.file_transfer_handlers import \
    is_directory


class FetchFileFromCentralHandlerTests(OauthTestingBase):
    def setUp(self):
        super(FetchFileFromCentralHandlerTests, self).setUp()
        self.endpoint = '/cloud/fetch_file_from_central/'
        self.base_data_dir = qdb.util.get_db_files_base_dir()
        self._clean_up_files = []

    def tearDown(self):
        for fp in self._clean_up_files:
            if exists(fp):
                if isdir(fp):
                    rmtree(fp)
                else:
                    remove(fp)

    def test_get(self):
        obs = self.get_authed(self.endpoint + 'nonexistingfile')
        self.assertEqual(obs.status_code, 403)
        self.assertIn('outside of the BASE_DATA_DIR', obs.reason)

        obs = self.get_authed(
            self.endpoint + self.base_data_dir[1:] + '/nonexistingfile')
        self.assertEqual(obs.status_code, 403)
        self.assertIn('The requested file is not present', obs.reason)

        obs = self.get_authed(
            self.endpoint + self.base_data_dir[1:] +
            '/raw_data/FASTA_QUAL_preprocessing.fna')
        self.assertEqual(obs.status_code, 200)
        self.assertIn('FLP3FBN01ELBSX length=250 xy=1766_01', str(obs.content))

        self.assertNotIn('Is-Qiita-Directory', obs.headers.keys())

    def test_get_directory(self):
        # a directory that exists BUT is not managed as a directory by Qiita
        obs = self.get_authed(
            self.endpoint + self.base_data_dir[1:] + '/BIOM/7')
        self.assertEqual(obs.status_code, 403)
        self.assertIn('You cannot access this directory', obs.reason)

        # create directory and file for a negative test as mountpoint is not
        # correct. 2_test_folder is registered in DB through
        # populate_test_db.sql
        fp_testfolder = join(self.base_data_dir, 'wrongmount', '2_test_folder')
        makedirs(fp_testfolder, exist_ok=True)
        PushFileToCentralHandlerTests._create_test_dir(self, fp_testfolder)
        self._clean_up_files.append(fp_testfolder)
        obs = self.get_authed(self.endpoint + fp_testfolder[1:])
        self.assertEqual(obs.status_code, 403)
        self.assertIn('You cannot access this directory', obs.reason)

        # create directory and file for a positive test. 2_test_folder is
        # registered in DB through populate_test_db.sql
        fp_testfolder = join(self.base_data_dir, 'job', '2_test_folder')
        makedirs(fp_testfolder, exist_ok=True)
        PushFileToCentralHandlerTests._create_test_dir(self, fp_testfolder)
        self._clean_up_files.append(fp_testfolder)
        obs = self.get_authed(self.endpoint + fp_testfolder[1:])
        self.assertEqual(obs.status_code, 200)
        self.assertIn('call me c', str(obs.content))
        self.assertIn('Is-Qiita-Directory', obs.headers.keys())


class PushFileToCentralHandlerTests(OauthTestingBase):
    def setUp(self):
        super(PushFileToCentralHandlerTests, self).setUp()
        self.endpoint = '/cloud/push_file_to_central/'
        self.base_data_dir = qdb.util.get_db_files_base_dir()
        self._clean_up_files = []

    def tearDown(self):
        for fp in self._clean_up_files:
            if exists(fp):
                if isdir(fp):
                    rmtree(fp)
                else:
                    remove(fp)

    def test_post(self):
        # create a test file "locally", i.e. in current working directory
        fp_source = 'foo.bar'
        with open(fp_source, 'w') as f:
            f.write("this is a test\n")
        self._files_to_remove.append(fp_source)

        # if successful, expected location of the file in BASE_DATA_DIR
        fp_target = self.base_data_dir + '/bar/' + basename(fp_source)
        self._files_to_remove.append(fp_target)

        # create a second test file
        fp_source2 = 'foo_two.bar'
        with open(fp_source2, 'w') as f:
            f.write("this is another test\n")
        self._files_to_remove.append(fp_source2)
        fp_target2 = self.base_data_dir + '/barr/' + basename(fp_source2)
        self._files_to_remove.append(fp_target2)

        # test raise error if no file is given
        obs = self.post_authed(self.endpoint)
        self.assertIn("No files to upload defined!", obs.reason)

        # test correct mechanism
        with open(fp_source, 'rb') as fh:
            content = fh.read()
            files = {'file': ("dummy", content, "text/plain")}
            obs = self.post_authed(self.endpoint, files=files)
            self.assertIn('No target_filepath defined!', obs.reason)

            data = {'target_filepath': fp_target}
            obs = self.post_authed(self.endpoint, files=files, data=data)
            self.assertIn('No current_chunk argument provided', obs.reason)

            data['current_chunk'] = 1
            obs = self.post_authed(self.endpoint, files=files, data=data)
            self.assertIn('No total_chunks argument provided', obs.reason)

            data['total_chunks'] = 1
            obs = self.post_authed(self.endpoint, files=files, data=data)
            self.assertIn('Stored 1 file into BASE_DATA_DIR of Qiita',
                          str(obs.content))
            self.assertTrue(filecmp.cmp(fp_source, fp_target, shallow=False))

        # check if error is raised, if file already exists
        # we need to let qiita thinks for this test, to NOT be in test mode
        with TRN:
            TRN.add("UPDATE settings SET test = False")
            TRN.execute()
        obs = self.post_authed(self.endpoint, files=files, data=data)
        # reset test mode to true
        with TRN:
            TRN.add("UPDATE settings SET test = True")
            TRN.execute()
        self.assertIn("already present in Qiita's BASE_DATA_DIR!",
                        obs.reason)

        # I ditched sending multiple files on 2026-03.24 in favor of a clean
        # interface to transfer a single but huge file in chunks
        # # test transfer of multiple files
        # if exists(fp_target):
        #     remove(fp_target)
        # with open(fp_source, 'rb') as fh1:
        #     with open(fp_source2, 'rb') as fh2:
        #         obs = self.post_authed(
        #             self.endpoint, files={'bar/': fh1, 'barr/': fh2})
        #         self.assertIn('Stored 2 files into BASE_DATA_DIR of Qiita',
        #                       str(obs.content))
        #         self.assertTrue(filecmp.cmp(fp_source, fp_target,
        #                                     shallow=False))
        #         self.assertTrue(filecmp.cmp(fp_source2, fp_target2,
        #                                     shallow=False))

    def test_chuncked_transfer(self):
        long_content = (b"This is a very long file content, "
                        b"that needs to be chunked :-)")
        chunk_size = 25
        chunks = {c+1: long_content[i:i+chunk_size]
                  for c, i
                  in enumerate(range(0, len(long_content), chunk_size))}

        # transfer all but second chunk
        fp_target = self.base_data_dir + '/chunked.txt'
        self._clean_up_files.append(fp_target)
        data = {'target_filepath': fp_target,
                'total_chunks': len(chunks)}
        resumable_identifier = hashlib.md5(
            abspath(fp_target).encode()).hexdigest()
        for i, content in chunks.items():
            self._clean_up_files.append(resumable_identifier + ('%i' % i))
            if i == 2:
                continue
            data['current_chunk'] = i
            obs = self.post_authed(
                self.endpoint,
                files={'file': ("dummy", content, "text/plain")},
                data=data)
            # test that chunk 1 transferred OK, chunk 3 also BUT file
            # could not yet be reconstructed as chunk 2 is missing
            if i < len(chunks):
                self.assertEqual(obs.status_code, 200)
            else:
                self.assertIn(
                    ("Not all %i chunks for file %s have been "
                     "transferred yet") % (len(chunks), fp_target),
                     obs.reason)
            # also test presense of chunk
            tmp_dirname = join(
                self.base_data_dir,
                'tmp_chunked_https_transfer',
                resumable_identifier[:2])
            self.assertTrue(exists(join(
                tmp_dirname, resumable_identifier + '.%i' % i)))

        # transfer missing chunk
        data['current_chunk'] = 2
        obs = self.post_authed(
            self.endpoint,
            files={'file': ("dummy", chunks[data['current_chunk']],
                            "text/plain")},
            data=data)
        self.assertEqual(obs.status_code, 200)
        self.assertTrue(exists(join(
                tmp_dirname,
                resumable_identifier + '.%i' % data['current_chunk'])))

        # all chunks have been transferred, but file has not been reconstructed
        # as last expected chunk needs to be re-transferred to trigger this
        data['current_chunk'] = 3
        obs = self.post_authed(
            self.endpoint,
            files={'file': ("dummy", chunks[data['current_chunk']],
                            "text/plain")},
            data=data)
        self.assertEqual(obs.status_code, 200)

        # test existance of transferred and reconstructred file
        self.assertTrue(exists(fp_target))
        self.assertIn(b'Stored 1 file into BASE_DATA_DIR of Qiita',
                      obs.content)

        # test that tmp files have been removed
        self.assertTrue(all([not exists(join(
                tmp_dirname,
                resumable_identifier + '.%i' % i)) for i in chunks.keys()]))

        # test file content
        with open(fp_target, 'r') as f:
            filecontent = f.read()
            self.assertEqual(long_content.decode("utf-8"), filecontent)

    def _create_test_dir(self, prefix=None):
        """Creates a test directory with files and subdirs."""
        # prefix
        # |- testdir/
        # |---- fileA.txt
        # |---- subdirA_l1/
        # |-------- fileB.fna
        # |-------- subdirC_l2/
        # |------------ fileC.log
        # |------------ fileD.seq
        # |---- subdirB_l1/
        # |-------- fileE.sff
        if (prefix is not None) and (prefix != ""):
            prefix = join(prefix, 'testdir')
        else:
            prefix = 'testdir'

        for dir in [join(prefix, 'subdirA_l1', 'subdirC_l2'),
                    join(prefix, 'subdirB_l1')]:
            if not exists(dir):
                makedirs(dir)
        for file, cont in [(join(prefix, 'fileA.txt'), 'contentA'),
                           (join(prefix, 'subdirA_l1',
                                 'fileB.fna'), 'this is B'),
                           (join(prefix, 'subdirA_l1', 'subdirC_l2',
                                 'fileC.log'), 'call me c'),
                           (join(prefix, 'subdirA_l1', 'subdirC_l2',
                                 'fileD.seq'), 'I d'),
                           (join(prefix, 'subdirB_l1', 'fileE.sff'), 'oh e')]:
            with open(file, "w") as f:
                f.write(cont + "\n")
        self._clean_up_files.append(prefix)

        return prefix

    def _send_dir(self, fp_zipped='tmp_senddir.zip'):
        dir = self._create_test_dir(prefix='/tmp/try1')

        make_archive(splitext(fp_zipped)[0], 'zip', dir)
        self._clean_up_files.append(fp_zipped)

        with open(fp_zipped, 'rb') as fh:
            obs = self.post_authed(
                self.endpoint,
                data={'is_directory': 'true',
                      'target_filepath': dir,
                      'current_chunk': 1,
                      'total_chunks': 1},
                files={'file': ("dummy", fh.read(), "text/plain")})

        return obs

    def test_post_directory(self):
        obs = self._send_dir()
        self.assertTrue(obs.status_code == 200)
        qmain_dir = obs.content.decode().split('\n')[1].split(' - ')[-1]

        self.assertTrue(
            len(filecmp.cmpfiles(
                '/tmp/try1/testdir/', qmain_dir,
                ['fileA.txt',
                 'subdirA_l1/fileB.fna',
                 'subdirA_l1/subdirC_l2/fileC.log',
                 'subdirA_l1/subdirC_l2/fileD.seq',
                 'subdirB_l1/fileE.sff'])[0]) == 5)

    def test_post_directory_testexisting(self):
        # check if error is raised, if directory already exists
        # send first time, should be OK
        obs = self._send_dir()
        self.assertTrue(obs.status_code == 200)

        # we need to let qiita thinks for this test, to NOT be in test mode
        with TRN:
            TRN.add("UPDATE settings SET test = False")
            TRN.execute()
        # send again, should fal
        obs = self._send_dir()
        # reset test mode to true
        with TRN:
            TRN.add("UPDATE settings SET test = True")
            TRN.execute()

        self.assertIn("already present in Qiita's BASE_DATA_DIR!",
                      obs.reason)


class UtilsTests(OauthTestingBase):
    def setUp(self):
        self.base_data_dir = qdb.util.get_db_files_base_dir()
        self._files_to_remove = []

    def test_is_directory(self):
        obs = is_directory(join('/wrong_root', 'karl', 'heinz'))
        self.assertFalse(obs)

        # no path given
        obs = is_directory('')
        self.assertFalse(obs)

        # just pointing to BASE_DATA_DIR, i.e. no mountpoint given
        obs = is_directory(self.base_data_dir)
        self.assertFalse(obs)

        # existing dir, but not accessible as not managed by Qiita DB as dir
        obs = is_directory(join(self.base_data_dir, 'BIOM'))
        self.assertFalse(obs)

        # managed directory, but wrong mountpoint
        fp_testfolder = join(self.base_data_dir, 'wrongmount', '2_test_folder')
        obs = is_directory(fp_testfolder)
        self.assertFalse(obs)

        # positive test
        fp_testfolder = join(self.base_data_dir, 'job', '2_test_folder')
        obs = is_directory(fp_testfolder)
        self.assertTrue(obs)


if __name__ == "__main__":
    main()
