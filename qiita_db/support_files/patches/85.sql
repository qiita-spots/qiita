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

-- Feb 28, 2022
-- adding a new column to the default_workflow table to keep track of the
-- artifact type that is expecting vs. "guessing"

ALTER TABLE qiita.default_workflow ADD artifact_type_id BIGINT NOT NULL DEFAULT 3;
ALTER TABLE qiita.default_workflow
  ADD CONSTRAINT fk_artifact_type_id
    FOREIGN KEY (artifact_type_id)
    REFERENCES qiita.artifact_type(artifact_type_id)
    ON UPDATE CASCADE;

-- Mar 17, 2022
-- deleting specimen_id_column from qiita.study

ALTER TABLE qiita.study DROP COLUMN specimen_id_column;
