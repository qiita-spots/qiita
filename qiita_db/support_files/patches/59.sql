-- Sep 15, 2017
-- Adding "name" parameter to validate commands

DO $do$
DECLARE
    cmd     RECORD;
BEGIN
    FOR cmd IN
        SELECT command_id FROM qiita.software_command WHERE name = 'Validate'
    LOOP
        INSERT INTO qiita.command_parameter (command_id, parameter_name, parameter_type, required, default_value)
            VALUES (cmd.command_id, 'name', 'string', 'False', NULL);
    END LOOP;
END $do$
