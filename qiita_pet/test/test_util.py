from unittest import TestCase, main

from qiita_pet.util import clean_str

# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------


class TestUtil(TestCase):
    def test_clean_str(self):
        obs = clean_str("Remove Spaces From:String")
        self.assertEqual(obs, "Remove_Spaces_FromString")


if __name__ == "__main__":
    main()
