#!/usr/bin/env python
from __future__ import division

__author__ = "Jose Antonio Navas Molina"
__copyright__ = "Copyright 2013, The Qiita project"
__credits__ = ["Jose Antonio Navas Molina", "Adam Robbins-Pianka"]
__license__ = "BSD"
__version__ = "0.1.0-dev"
__maintainer__ = "Jose Antonio Navas Molina"
__email__ = "josenavasmolina@gmail.com"

from pyqi.core.command import Command, CommandIn, ParameterCollection

from qiita_db.metadata_template import SampleTemplate
from qiime.util import MetadataMap


class SampleTemplateAdder(Command):
    BriefDescription = "Adds the sample template information to the storage"
    LongDescription = "Adds sample template information to the storage"
    CommandIns = ParameterCollection([
        CommandIn(Name='sample_template', DataType=MetadataMap,
                  Description="Sample template information to add to the "
                              "storage.",
                  Required=True),
        CommandIn(Name='study_id', DataType=str,
                  Description="The study storage identifier to which the "
                  "sample template belongs to.",
                  Required=True),
        CommandIn(Name='clear', DataType=bool,
                  Description="In case that the metadata already exists on "
                  "the system, remove the old one before the new one is added",
                  Required=False, Default=False)
    ])

    def run(self, **kwargs):
        # Get parameters
        sample_template = kwargs['sample_template']
        study_id = kwargs['study_id']
        clear = kwargs['clear']

        if clear:
            SampleTemplate.delete(study_id)

        sample_temp = SampleTemplate.create(sample_template, study_id)

        return {'sample_template': sample_temp}

CommandConstructor = SampleTemplateAdder
