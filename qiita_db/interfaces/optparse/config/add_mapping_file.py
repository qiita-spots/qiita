#!/usr/bin/env python
from __future__ import division

__author__ = "Jose Antonio Navas Molina"
__copyright__ = "Copyright 2013, The Qiita project"
__credits__ = ["Jose Antonio Navas Molina", "Adam Robbins-Pianka"]
__license__ = "BSD"
__version__ = "0.1.0-dev"
__maintainer__ = "Jose Antonio Navas Molina"
__email__ = "josenavasmolina@gmail.com"

from pyqi.core.interfaces.optparse import (OptparseUsageExample,
                                           OptparseOption, OptparseResult)
from pyqi.core.command import (make_command_in_collection_lookup_f,
                               make_command_out_collection_lookup_f)
from qiita_db.commands.mapping_file_adder import CommandConstructor
from qiita_db.interfaces.optparse.input_handler import load_mapping_file

# Convenience function for looking up parameters by name.
cmd_in_lookup = make_command_in_collection_lookup_f(CommandConstructor)
cmd_out_lookup = make_command_out_collection_lookup_f(CommandConstructor)

# Examples of how the command can be used from the command line using an
# optparse interface.
usage_examples = [
    OptparseUsageExample(ShortDesc="Add a mapping file to the storage",
                         LongDesc="Add a mapping file to the storage",
                         Ex="%prog -m study_1_mapping_file.txt"),
    OptparseUsageExample(ShortDesc="Add a mapping file to the storage, "
                                   "clearing the previous stored data",
                         LongDesc="If the mapping file already exists in the "
                                   "storage, passing '-d' will delete it "
                                   "before adding the new mapping information",
                         Ex="%prog -m study_1_mapping_file.txt -d")
]

inputs = [
    OptparseOption(Parameter=cmd_in_lookup('clear_tables'),
                   Type=None,
                   Action='store_true',
                   Handler=None,
                   ShortName='d',
                   ),
    OptparseOption(Parameter=cmd_in_lookup('metadata_map'),
                   Type='existing_filepath',
                   Action='store',
                   Handler=load_mapping_file,
                   ShortName='m',
                   )
]

outputs = []
