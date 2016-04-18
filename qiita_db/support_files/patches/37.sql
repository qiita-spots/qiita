-- Apr 18, 2016
-- Adding phred_offset to split libraries

DO $do$
DECLARE
    cmd_id            bigint;
BEGIN
    -- selecting command_id of interest
    SELECT command_id FROM qiita.software_command WHERE name = 'Split libraries FASTQ' INTO cmd_id;

    -- adding new parameter
    INSERT INTO qiita.command_parameter (command_id, parameter_name, parameter_type, required, default_value)
        VALUES (cmd_id, 'phred_offset', 'string', False, '');

    -- updating all current artifacts that were generated with this command
    UPDATE qiita.artifact
        SET command_parameters = (
            substring(command_parameters::text FROM 0 FOR char_length(command_parameters::text)) || ',"phred_offset":""}'
        )::json
        WHERE artifact_id=2;

    -- updating the per sample FASTQ defaults
    UPDATE qiita.default_parameter_set
        SET parameter_set = (
            substring(parameter_set::text FROM 0 FOR char_length(parameter_set::text)) || ',"phred_offset":""}'
        )::json
        WHERE command_id=cmd_id;
END $do$;
