-- Aug 8, 2017
-- Add release validators internal Qiita command

DO $do$
DECLARE
    qiita_sw_id     bigint;
    rv_cmd_id       bigint;
BEGIN
    SELECT software_id INTO qiita_sw_id
        FROM qiita.software
        WHERE name = 'Qiita' AND version = 'alpha';

    INSERT INTO qiita.software_command (software_id, name, description)
        VALUES (qiita_sw_id, 'release_validators', 'Releases the job validators')
        RETURNING command_id INTO rv_cmd_id;

    INSERT INTO qiita.command_parameter (command_id, parameter_name, parameter_type, required, default_value)
        VALUES (rv_cmd_id, 'job', 'string', True, NULL);
END $do$;
