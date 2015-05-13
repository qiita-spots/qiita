-- May 12, 2015
-- Add in analysis status marking that undelying data has changed.
-- Add logging tables for changes to sample and prep templates
INSERT INTO qiita.analysis_status (status) VALUES ('altered_data');

-- Add logging tables for template edits
CREATE TABLE qiita.sample_template_edit (
	study_id   bigint  NOT NULL,
	change               varchar  NOT NULL,
	timestamp            timestamp DEFAULT current_timestamp NOT NULL,
	CONSTRAINT idx_sample_template_edit PRIMARY KEY ( study_id, change )
 );

CREATE INDEX idx_sample_template_edit_0 ON qiita.sample_template_edit ( study_id );

COMMENT ON TABLE qiita.sample_template_edit IS 'Holds information on edits made to sample templates';

ALTER TABLE qiita.sample_template_edit ADD CONSTRAINT fk_sample_template_edit FOREIGN KEY ( study_id ) REFERENCES qiita.study( study_id );

CREATE TABLE qiita.prep_template_edit (
	prep_template_id     bigint  NOT NULL,
	change               varchar  NOT NULL,
	timestamp            timestamp DEFAULT current_timestamp NOT NULL,
	CONSTRAINT idx_prep_template_edit_0 PRIMARY KEY ( prep_template_id, change )
 );

CREATE INDEX idx_prep_template_edit ON qiita.prep_template_edit ( prep_template_id );

ALTER TABLE qiita.prep_template_edit ADD CONSTRAINT fk_prep_template_edit FOREIGN KEY ( prep_template_id ) REFERENCES qiita.prep_template( prep_template_id );
