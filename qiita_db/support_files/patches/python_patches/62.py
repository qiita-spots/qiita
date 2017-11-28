# Nov 28, 2017 (only in py file)
# Adding a new command into Qiita/Alpha: delete_analysis

from qiita_db.software import Software, Command

# Create the delete study command
Command.create(Software.from_name_and_version('Qiita', 'alpha'),
               'delete_analysis', 'Deletes a full analysis',
               {'analysis_id': ['integer', None]})
