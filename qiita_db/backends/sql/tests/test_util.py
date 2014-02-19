#!/usr/bin/env python
from __future__ import division

__author__ = "Adam Robbins-Pianka"
__copyright__ = "Copyright 2013, The Qiita project"
__credits__ = ["Adam Robbins-Pianka"]
__license__ = "BSD"
__version__ = "0.1.0-dev"
__maintainer__ = "Adam Robbins-Pianka"
__email__ = "adam.robbinspianka@colorado.edu"

from unittest import TestCase, main
from qiita_core.metadata_map import MetadataMap
from string import isdigit

class UtilTests(TestCase):
    
    def setUp(self):
        pass


    def test_quote_column_name(self):
        """Tests proper lower-casing and double-quoting of input string
        """
        self.assertEqual(quote_column_name('HeLlo'), '"hello"')


    def test_quote_data_value(self):
        """Tests proper single-quoting of input string
        """
        self.assertEqual(quote_data_value('HElLO'), "'HElLO'")


    def test_get_datatypes(self):
        """Tests proper inferral of datatypes from a MetadataMap object
        """
        pass
