#!/usr/bin/env python
from __future__ import division

__author__ = "Jose Antonio Navas Molina"
__copyright__ = "Copyright 2013, The Qiita project"
__credits__ = ["Jose Antonio Navas Molina", "Adam Robbins-Pianka"]
__license__ = "BSD"
__version__ = "0.1.0-dev"
__maintainer__ = "Jose Antonio Navas Molina"
__email__ = "josenavasmolina@gmail.com"

from pyqi.core.command import (Command, CommandIn, CommandOut,
                               ParameterCollection)
from pyqi.core.exception import CommandError
from qiita_db.add_mapping_file import add_mapping_file


class MappingFileAdder(Command):
    BriefDescription = "Adds the mapping file information to the storage"
    LongDescription = "Adds the mapping file information to the storage"
    CommandIns = ParameterCollection([
        CommandIn(Name='mapping_file_info', DataType=tuple,
                  Description="Mapping information to add to the storage. "
                  "Format is (study id, dict of dicts, list of column headers,"
                  " columns datatypes)", Required=True),
        CommandIn(Name='clear_tables', DataType=bool,
                  Description="Deletes all rows from column_tables for this "
                  "study, and drops the study's table", Required=False,
                  Default=False)
    ])

    def run(self, **kwargs):
        # Get parameters
        mapping_file_info = kwargs['mapping_file_info']
        clear_tables = kwargs['clear_tables']
        # Extract mapping file information
        try:
            study_id, mapping, headers, datatypes = mapping_file_info
        except ValueError, e:
            raise CommandError("Wrong mapping file information format")

        add_mapping_file(study_id, mapping, headers, datatypes, clear_tables)
        return {}

CommandConstructor = MappingFileAdder
