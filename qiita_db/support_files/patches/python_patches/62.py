# Nov 28, 2017 (only in py file)
# Adding a new command into Qiita/Alpha: delete_analysis

from qiita_db.software import Software, Command
from qiita_db.sql_connection import TRN

# Create the delete study command
Command.create(Software.from_name_and_version('Qiita', 'alpha'),
               'delete_analysis', 'Deletes a full analysis',
               {'analysis_id': ['integer', None]})

# Make sure that all validate commands have the "analysis" parameter
with TRN:
    # Get all validate commands that are missing the analysis parameter
    sql = """SELECT command_id
             FROM qiita.software_command sc
             WHERE name = 'Validate' AND NOT (
                SELECT EXISTS(SELECT *
                              FROM qiita.command_parameter
                              WHERE parameter_name = 'analysis'
                                AND command_id = sc.command_id));"""
    TRN.add(sql)
    sql = """INSERT INTO qiita.command_parameter
                (command_id, parameter_name, parameter_type,
                 required, default_value, name_order, check_biom_merge)
             VALUES (6, 'analysis', 'analysis', false, NULL, NULL, false)"""
    sql_params = [[cmd_id, 'analysis', 'analysis', False, None, None, False]
                  for cmd_id in TRN.execute_fetchflatten()]
    TRN.add(sql, sql_params, many=True)
    TRN.execute()
