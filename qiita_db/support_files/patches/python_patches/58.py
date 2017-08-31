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

    # Create the submit to VAMPS command
    parameters = {'artifact': ['artifact:["Demultiplexed"]', None]}
    Command.create(qiita_plugin, "submit_to_VAMPS",
                   "submits an artifact to VAMPS", parameters)

    # Create the copy artifact command
    parameters = {'artifact': ['artifact:["Demultiplexed"]', None],
                  'prep_template': ['prep_template', None]}
    Command.create(qiita_plugin, "copy_artifact",
                   "Creates a copy of an artifact", parameters)
