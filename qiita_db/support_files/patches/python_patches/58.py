# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from qiita_db.sql_connection import TRN
from qiita_db.software import Software, Command

with TRN:
    # Retrieve the Qiita plugin
    qiita_plugin = Software.from_name_and_version('Qiita', 'alpha')

    # Create the submit command for VAMPS command
    parameters = {'artifact': ['artifact:["Demultiplexed"]', None]}
    Command.create(qiita_plugin, "submit_to_VAMPS",
                   "submits an artifact to VAMPS", parameters)

    # Create the copy artifact command
    parameters = {'artifact': ['artifact:["Demultiplexed"]', None],
                  'prep_template': ['prep_template', None]}
    Command.create(qiita_plugin, "copy_artifact",
                   "Creates a copy of an artifact", parameters)

    # Create the submit command for EBI command
    parameters = {'artifact': ['artifact:["Demultiplexed"]', None],
                  'submission_type': ['choice:["ADD", "MODIFY"]', 'ADD']}
    Command.create(qiita_plugin, "submit_to_EBI",
                   "submits an artifact to EBI", parameters)

    # Create the submit command for delete_artifact
    parameters = {'artifact': ['artifact:["Demultiplexed"]', None]}
    Command.create(qiita_plugin, "delete_artifact",
                   "Delete an artifact", parameters)

    # Create the submit command for create a sample template
    parameters = {
        'fp': ['string', None], 'study_id': ['integer', None],
        'is_mapping_file': ['boolean', True], 'data_type': ['string', None]}
    Command.create(qiita_plugin, "create_sample_template",
                   "Create a sample template", parameters)

    # Create the update sample template command
    parameters = {'study': ['integer', None], 'template_fp': ['string', None]}
    Command.create(qiita_plugin, "update_sample_template",
                   "Updates the sample template", parameters)

    # Create the delete sample template command
    parameters = {'study': ['integer', None]}
    Command.create(qiita_plugin, "delete_sample_template",
                   "Deletes a sample template", parameters)

    # Create the update prep template command
    parameters = {'prep_template': ['integer', None],
                  'template_fp': ['string', None]}
    Command.create(qiita_plugin, "update_prep_template",
                   "Updates the prep template", parameters)

    # Create the delete sample or column command
    parameters = {
        'obj_class': ['choice:["SampleTemplate", "PrepTemplate"]', None],
        'obj_id': ['integer', None],
        'sample_or_col': ['choice:["samples", "columns"]', None],
        'name': ['string', None]}
    Command.create(qiita_plugin, "delete_sample_or_column",
                   "Deletes a sample or a columns from the metadata",
                   parameters)
