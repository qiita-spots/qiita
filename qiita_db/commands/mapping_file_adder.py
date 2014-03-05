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

from qiita_db.metadata_map import MetadataMap
from qiime.util import MetadataMap as QiimeMetadataMap


class MappingFileAdder(Command):
    BriefDescription = "Adds the mapping file information to the storage"
    LongDescription = "Adds the mapping file information to the storage"
    CommandIns = ParameterCollection([
        CommandIn(Name='metadata_map', DataType=QiimeMetadataMap,
                  Description="Mapping information to add to the storage.",
                  Required=True),
        CommandIn(Name='study_id', DataType=str,
                  Description="The study storage identifier to which the "
                  "metadata map belongs to.",
                  Required=True),
        CommandIn(Name='idx', DataType=int, Description="Metadata map index",
                  Required=False, Default=None),
        CommandIn(Name='clear', DataType=bool,
                  Description="In case that the metadata already exists on "
                  "the system, remove the old one before the new one is added",
                  Required=False, Default=False)
    ])

    def run(self, **kwargs):
        # Get parameters
        metadata_map = kwargs['metadata_map']
        study_id = kwargs['study_id']
        idx = kwargs['idx']
        clear = kwargs['clear']

        if clear:
            if idx is None:
                raise CommandError("metadata map index missing - needed for"
                                   "clear up before inserting")
            metadata_map_id = (study_id, idx)
            MetadataMap.delete(metadata_map_id)

        md_map = MetadataMap.create(metadata_map, study_id, idx)

        return {}

CommandConstructor = MappingFileAdder
