-- Jul 26, 2017
-- Updating Pick OTUs to work with Qiita.

DELETE FROM qiita.command_parameter
WHERE parameter_name  = 'reference'
  AND command_id = (
    SELECT command_id
    FROM qiita.software_command
    WHERE name = 'Pick closed-reference OTUs');

INSERT INTO qiita.command_parameter
    (command_id, parameter_name, parameter_type, required, default_value)
  VALUES
    ((SELECT command_id FROM qiita.software_command WHERE name = 'Pick closed-reference OTUs'), 'reference-tax', 'string', false, ''),
    ((SELECT command_id FROM qiita.software_command WHERE name = 'Pick closed-reference OTUs'), 'reference-seq', 'string', false, '');
