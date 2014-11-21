-- Nov 21, 2014
-- adding new tables to support multiple filepaths for sample/prep templates

CREATE TABLE qiita.prep_template_filepath (
	prep_template_id     bigint  NOT NULL,
	filepath_id          bigint  NOT NULL,
	CONSTRAINT idx_prep_template_filepath PRIMARY KEY ( prep_template_id, filepath_id )
 ) ;

CREATE TABLE qiita.sample_template_filepath (
	study_id             bigint  NOT NULL,
	filepath_id          bigint  NOT NULL,
	CONSTRAINT idx_sample_template_filepath PRIMARY KEY ( study_id, filepath_id )
 ) ;

ALTER TABLE qiita.prep_template_filepath ADD CONSTRAINT fk_filepath_id FOREIGN KEY ( filepath_id ) REFERENCES qiita.filepath( filepath_id )    ;

ALTER TABLE qiita.prep_template_filepath ADD CONSTRAINT fk_prep_template_id FOREIGN KEY ( prep_template_id ) REFERENCES qiita.prep_template( prep_template_id )    ;

ALTER TABLE qiita.sample_template_filepath ADD CONSTRAINT fk_study_id FOREIGN KEY ( study_id ) REFERENCES qiita.study( study_id )    ;

ALTER TABLE qiita.sample_template_filepath ADD CONSTRAINT fk_filepath_id FOREIGN KEY ( filepath_id ) REFERENCES qiita.filepath( filepath_id )    ;

-- inserting the new filepath types

INSERT INTO qiita.filepath_type (filepath_type) VALUES ('sample_template'), ('prep_template');
