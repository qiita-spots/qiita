-- Nov 19, 2016
-- Adding provenance parameter to validate commands

DO $do$
DECLARE
    cmd  RECORD;
BEGIN
    FOR cmd IN
        SELECT command_id FROM qiita.software_command WHERE name = 'Validate'
    LOOP
        INSERT INTO qiita.command_parameter (command_id, parameter_name, parameter_type, required, default_value)
            VALUES (cmd.command_id, 'provenance', 'string', 'False', 'dflt_name');

    END LOOP;
END $do$
