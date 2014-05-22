#!/usr/bin/env python
from __future__ import division

# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

DATATYPES = ["16S", "18S", "Metabolites", "Metagenomes", "Metaproteomes"]
# This is going to be dynamically filled, hardcoding now for development
FUNCTIONS = ["Alpha_Diversity", "Beta_Diversity", "Procrustes"]

from qiita_core.configuration_manager import ConfigurationManager

qiita_config = ConfigurationManager()