-- Sep 21, 2016
-- Adding active column to the software and software command table to be able
-- to disallow plugins and/or individual software commands

ALTER TABLE qiita.software ADD active bool DEFAULT 'False' NOT NULL;

ALTER TABLE qiita.software_command ADD active bool DEFAULT 'True' NOT NULL;

-- Add function to set a key in a JSON value
-- Adapted from http://stackoverflow.com/a/23500670/3746629
CREATE OR REPLACE FUNCTION qiita.json_object_set_key(
  "json"          json,
  "key_to_set"    TEXT,
  "value_to_set"  anyelement
)
  RETURNS json
  LANGUAGE sql
  IMMUTABLE
  STRICT
AS $function$
SELECT concat('{', string_agg(to_json("key") || ':' || "value", ','), '}')::json
  FROM (SELECT *
          FROM json_each("json")
         WHERE "key" <> "key_to_set"
         UNION ALL
        SELECT "key_to_set", to_json("value_to_set")) AS "fields"
$function$;

-- Change the phred_offset from string to choice
DO $do$
DECLARE
    cmd_id      bigint;
    dflt_p      RECORD;
    a_vals      RECORD;
BEGIN
    -- select command id of interest
    SELECT command_id FROM qiita.software_command WHERE name = 'Split libraries FASTQ' INTO cmd_id;

    -- Update the phred_offset parameter type
    UPDATE qiita.command_parameter SET parameter_type = 'choice:["auto", "33", "64"]'
        WHERE parameter_name = 'phred_offset' AND command_id = cmd_id;

    -- Update all the default parameter sets to use "auto" instead of ""
    FOR dflt_p IN
        SELECT *
        FROM qiita.default_parameter_set
        WHERE command_id = cmd_id AND parameter_set->>'phred_offset' = ''
    LOOP
        UPDATE qiita.default_parameter_set
            SET parameter_set = qiita.json_object_set_key(dflt_p.parameter_set, 'phred_offset', 'auto'::varchar)
            WHERE default_parameter_set_id = dflt_p.default_parameter_set_id;
    END LOOP;

    -- Update all current artifacts that have been generated with this command
    FOR a_vals IN
        SELECT *
        FROM qiita.artifact
        WHERE command_id = cmd_id AND command_parameters->>'phred_offset' = ''
    LOOP
        UPDATE qiita.artifact
            SET command_parameters = qiita.json_object_set_key(a_vals.command_parameters, 'phred_offset', 'auto'::varchar)
            WHERE artifact_id = a_vals.artifact_id;
    END LOOP;
END $do$;
