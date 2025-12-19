-- Dec 12, 2025
-- Adding SEQUENCEs and support tables for sample_idx, prep_sample_idx,
-- and artifact_sample_idx

CREATE SEQUENCE qiita.sequence_sample_idx AS BIGINT; 
CREATE TABLE qiita.map_sample_idx (
    sample_name VARCHAR NOT NULL PRIMARY KEY,
    study_idx BIGINT NOT NULL,
    sample_idx BIGINT DEFAULT NEXTVAL('qiita.sequence_sample_idx') NOT NULL,
    UNIQUE (sample_idx),
    CONSTRAINT fk_study FOREIGN KEY (study_idx) REFERENCES qiita.study (study_id)
);

CREATE SEQUENCE qiita.sequence_prep_sample_idx AS BIGINT; 
CREATE TABLE qiita.map_prep_sample_idx (
    prep_sample_idx BIGINT NOT NULL PRIMARY KEY DEFAULT NEXTVAL('qiita.sequence_prep_sample_idx'),
    prep_idx BIGINT NOT NULL,
    sample_idx BIGINT NOT NULL,
    CONSTRAINT uc_prep_sample UNIQUE(prep_idx, sample_idx),
    CONSTRAINT fk_prep_template FOREIGN KEY (prep_idx) REFERENCES qiita.prep_template (prep_template_id)
);

CREATE SEQUENCE qiita.sequence_artifact_sample_idx AS BIGINT; 
CREATE TABLE qiita.map_artifact_sample_idx (
    artifact_sample_idx BIGINT NOT NULL PRIMARY KEY DEFAULT NEXTVAL('qiita.sequence_artifact_sample_idx'),
    artifact_idx BIGINT NOT NULL,
    prep_sample_idx BIGINT NOT NULL,
    CONSTRAINT uc_artifact_sample UNIQUE(artifact_idx, prep_sample_idx),
    CONSTRAINT fk_artifact FOREIGN KEY (artifact_idx) REFERENCES qiita.artifact (artifact_id)
);
