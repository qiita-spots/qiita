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

    -- inserting new possible default_parameter_sets
    INSERT INTO qiita.default_parameter_set (command_id, parameter_set_name, parameter_set)
        VALUES (cmd_id, 'per sample FASTQ defaults, phred_offset 33',
                '{"max_bad_run_length":3,"min_per_read_length_fraction":0.75,"sequence_max_n":0,"rev_comp_barcode":false,"rev_comp_mapping_barcodes":false,"rev_comp":false,"phred_quality_threshold":3,"barcode_type":"not-barcoded","max_barcode_errors":1.5,"phred_offset":"33"}'::json);
    INSERT INTO qiita.default_parameter_set (command_id, parameter_set_name, parameter_set)
        VALUES (cmd_id, 'per sample FASTQ defaults, phred_offset 64',
                '{"max_bad_run_length":3,"min_per_read_length_fraction":0.75,"sequence_max_n":0,"rev_comp_barcode":false,"rev_comp_mapping_barcodes":false,"rev_comp":false,"phred_quality_threshold":3,"barcode_type":"not-barcoded","max_barcode_errors":1.5,"phred_offset":"64"}'::json);
END $do$;
