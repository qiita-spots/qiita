-- Feb 22, 2022
-- adding a new parameter `categories` to build_analysis_files

DO $do$
DECLARE
    cmd_id      bigint;
BEGIN
    SELECT command_id INTO cmd_id FROM qiita.software_command WHERE name = 'build_analysis_files';

    INSERT INTO qiita.command_parameter (command_id, parameter_name, parameter_type, required, default_value)
        VALUES (cmd_id, 'categories', 'mchoice', True, NULL);
END $do$;
