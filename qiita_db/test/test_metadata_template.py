# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import TestCase, main

from qiita_core.util import qiita_test_checker
from qiita_core.exceptions import IncompetentQiitaDeveloperError
from qiita_db.metadata_template import MetadataTemplate, SampleTemplate


class TestMetadataTemplate(TestCase):
    """Tests the MetadataTemplate base class"""

    def test_create(self):
        """Create raises an error because it's not called from a subclass"""


@qiita_test_checker()
class TestSampleTemplate(TestCase):
    """"""
    def test_init(self):
        """"""
        SampleTemplate(1)


if __name__ == '__main__':
    main()
