-- Jun 8, 2022
-- adding the new visibility level: archived

INSERT INTO qiita.visibility (visibility, visibility_description) VALUES ('archived', 'Archived artifact');

-- update function to ignore archived artifacts
CREATE OR REPLACE FUNCTION qiita.bioms_from_preparation_artifacts(prep_id bigint) RETURNS TEXT AS $$
DECLARE
  artifacts TEXT := NULL;
BEGIN
  SELECT array_to_string(array_agg(artifact_id), ',') INTO artifacts
  FROM qiita.preparation_artifact
  LEFT JOIN qiita.artifact USING (artifact_id)
  LEFT JOIN qiita.artifact_type USING (artifact_type_id)
  LEFT JOIN qiita.software_command USING (command_id)
  LEFT JOIN qiita.software USING (software_id)
  LEFT JOIN qiita.visibility USING (visibility_id)
  WHERE
    prep_template_id = prep_id AND
    artifact_type = 'BIOM' AND
    NOT deprecated AND
    visibility != 'archived';
  RETURN artifacts;
END
$$ LANGUAGE plpgsql;
