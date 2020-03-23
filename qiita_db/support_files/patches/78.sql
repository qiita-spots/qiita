-- Nov 27, 2019
-- Adds download_link table for allowing jwt secured downloads of artifacts from shortened links
ALTER TABLE qiita.prep_template ADD deprecated BOOL DEFAULT FALSE;

ALTER TABLE qiita.study ADD notes TEXT NOT NULL DEFAULT '';

CREATE TABLE qiita.preparation_artifact (
  prep_template_id BIGINT,
  artifact_id BIGINT,
  CONSTRAINT fk_prep_template_id FOREIGN KEY ( prep_template_id ) REFERENCES qiita.prep_template( prep_template_id ),
  CONSTRAINT fk_artifact_id FOREIGN KEY ( artifact_id ) REFERENCES qiita.artifact( artifact_id )
);

INSERT INTO qiita.preparation_artifact (artifact_id, prep_template_id)
  SELECT a.artifact_id, prep_template_id FROM qiita.artifact a, qiita.find_artifact_roots(artifact_id) root_id
    JOIN qiita.prep_template pt ON (root_id = pt.artifact_id);
ALTER TABLE qiita.preparation_artifact ADD PRIMARY KEY (prep_template_id, artifact_id);
CREATE INDEX idx_preparation_artifact_prep_template_id  ON qiita.preparation_artifact ( prep_template_id );

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
  WHERE prep_template_id = prep_id AND artifact_type = 'BIOM' AND NOT deprecated;
  RETURN artifacts;
END
$$ LANGUAGE plpgsql;
