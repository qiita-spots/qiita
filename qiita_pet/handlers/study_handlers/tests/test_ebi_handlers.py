# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from unittest import main
from os import remove, close
from os.path import exists
from tempfile import mkstemp

from h5py import File
from mock import Mock

from qiita_pet.handlers.base_handlers import BaseHandler
from qiita_pet.test.tornado_test_base import TestHandlerBase
from qiita_db.artifact import Artifact
from qiita_db.user import User
from qiita_ware.demux import to_hdf5


class TestEBISubmitHandler(TestHandlerBase):
    # TODO: add tests for post function once we figure out how. Issue 567
    def setUp(self):
        super(TestEBISubmitHandler, self).setUp()
        self._clean_up_files = []

    def tearDown(self):
        for fp in self._clean_up_files:
            if exists(fp):
                remove(fp)

    def test_get(self):
        demux_fp = [fp for _, fp, fp_type in Artifact(2).filepaths
                    if fp_type == 'preprocessed_demux'][0]
        fd, fna_fp = mkstemp(suffix='_seqs.fna')
        close(fd)
        self._clean_up_files.extend([fna_fp, demux_fp])
        with open(fna_fp, 'w') as f:
            f.write('>a_1 X orig_bc=X new_bc=X bc_diffs=0\nCCC')
        with File(demux_fp, "w") as f:
            to_hdf5(fna_fp, f)
        BaseHandler.get_current_user = Mock(return_value=User("admin@foo.bar"))
        response = self.get("/ebi_submission/2")
        self.assertEqual(response.code, 200)

    def test_get_no_admin(self):
        response = self.get("/ebi_submission/2")
        self.assertEqual(response.code, 403)

    def test_get_no_exist(self):
        response = self.get('/ebi_submission/100')
        self.assertEqual(response.code, 404)

if __name__ == "__main__":
    main()
