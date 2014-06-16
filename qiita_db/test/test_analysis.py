from unittest import TestCase, main

from qiita_core.exceptions import IncompetentQiitaDeveloperError
from qiita_core.util import qiita_test_checker
from qiita_db.analysis import Analysis
from qiita_db.job import Job
from qiita_db.user import User
from qiita_db.exceptions import (QiitaDBDuplicateError, QiitaDBColumnError,
                                 QiitaDBStatusError)
from qiita_db.sql_connection import SQLConnectionHandler

# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------


@qiita_test_checker()
class TestAnalysis(TestCase):
    def setUp(self):
        self.analysis = Analysis(1)

    def test_lock_public(self):
        raise NotImplementedError()

    def test_create(self):
        raise NotImplementedError()

    def test_create_parent(self):
        raise NotImplementedError()

    def test_retrieve_owner(self):
        raise NotImplementedError()

    def test_retrieve_name(self):
        raise NotImplementedError()

    def test_retrieve_description(self):
        raise NotImplementedError()

    def test_set_description(self):
        raise NotImplementedError()

    def test_retrieve_shared_with(self):
        raise NotImplementedError()

    def test_retrieve_biom_tables(self):
        raise NotImplementedError()

    def test_retrieve_jobs(self):
        raise NotImplementedError()

    def test_retrieve_pmid(self):
        raise NotImplementedError()

    def test_set_pmid(self):
        raise NotImplementedError()

    # def test_get_parent(self):
    #     raise NotImplementedError()

    # def test_get_children(self):
    #     raise NotImplementedError()

    def test_add_samples(self):
        raise NotImplementedError()

    def test_remove_samples(self):
        raise NotImplementedError()

    def test_add_biom_tables(self):
        raise NotImplementedError()

    def test_remove_biom_tables(self):
        raise NotImplementedError()

    def test_add_jobs(self):
        raise NotImplementedError()

    def test_share(self):
        raise NotImplementedError()

    def test_unshare(self):
        raise NotImplementedError()