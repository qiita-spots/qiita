#!/usr/bin/env python
from __future__ import division

# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from pyqi.core.interfaces.optparse import (OptparseUsageExample,
                                           OptparseOption)
from pyqi.core.command import (make_command_in_collection_lookup_f,
                               make_command_out_collection_lookup_f)
from qiita_db.commands.sample_template_adder import CommandConstructor
from qiita_db.interfaces.optparse.input_handler import load_mapping_file

# Convenience function for looking up parameters by name.
cmd_in_lookup = make_command_in_collection_lookup_f(CommandConstructor)
cmd_out_lookup = make_command_out_collection_lookup_f(CommandConstructor)

# Examples of how the command can be used from the command line using an
# optparse interface.
usage_examples = [
    OptparseUsageExample(ShortDesc="Add a sample template file to the db",
                         LongDesc="Add a sample template file to the db",
                         Ex="%prog -i study_1_mapping_file.txt -s 1"),
    OptparseUsageExample(ShortDesc="Add a mapping file to the db, "
                                   "clearing the previous stored data",
                         LongDesc="If the mapping file already exists in the "
                                   "db, passing '-c' will delete it "
                                   "before adding the new mapping information",
                         Ex="%prog -i study_1_mapping_file.txt -s 1 -c")
]

inputs = [
    OptparseOption(Parameter=cmd_in_lookup('clear'),
                   Type=None,
                   Action='store_true',
                   Handler=None,
                   ShortName='c',
                   ),
    OptparseOption(Parameter=cmd_in_lookup('sample_template'),
                   Type='existing_filepath',
                   Action='store',
                   Handler=load_mapping_file,
                   ShortName='i',
                   ),
    OptparseOption(Parameter=cmd_in_lookup('study_id'),
                   Type=int,
                   Action='store',
                   Handler=None,
                   ShortName='s',
                   ),
]

outputs = []
