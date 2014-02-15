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

from qiita_db import MetadataMapStorage
from qiita_core.metadata_map import MetadataMap


class MappingFileAdder(Command):
    BriefDescription = "Adds the mapping file information to the storage"
    LongDescription = "Adds the mapping file information to the storage"
    CommandIns = ParameterCollection([
        CommandIn(Name='metadata_map', DataType=MetadataMap,
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
        metadata_map = kwargs['metadata_map']
        clear_tables = kwargs['clear_tables']

        metadata_map_stg = MetadataMapStorage()

        if clear_tables:
            metadata_map_stg.delete(metadata_map.id_)

        metadata_map_stg.insert(metadata_map)

        return {}

CommandConstructor = MappingFileAdder
