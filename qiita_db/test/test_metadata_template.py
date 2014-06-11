# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import TestCase, main

import pandas as pd

from qiita_core.util import qiita_test_checker
from qiita_core.exceptions import IncompetentQiitaDeveloperError
from qiita_db.study import Study
from qiita_db.metadata_template import (MetadataTemplate, SampleTemplate,
                                        PrepTemplate)


@qiita_test_checker()
class TestMetadataTemplate(TestCase):
    """Tests the MetadataTemplate base class"""
    def setUp(self):
        self.study = Study(1)
        self.metadata = pd.DataFrame.from_dict({})

    def test_create(self):
        """Create raises an error because it's not called from a subclass"""
        with self.assertRaises(IncompetentQiitaDeveloperError):
            MetadataTemplate.create(self.metadata, self.study)


@qiita_test_checker()
class TestSampleTemplate(TestCase):
    """"""


@qiita_test_checker()
class TestPrepTemplate(TestCase):
    """"""


if __name__ == '__main__':
    main()
