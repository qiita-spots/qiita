-- May 6, 2015
-- We attach the prep template directly to the study. The raw data is no longer
-- attached to the study directly, the prep template point to them. This will
-- make the RawData to be effectively just a container for the raw files,
-- which is how it was acting previously.

CREATE TABLE qiita.study_prep_template ( 
    study_id             bigint  NOT NULL,
    prep_template_id     bigint  NOT NULL,
    CONSTRAINT idx_study_raw_data PRIMARY KEY ( study_id, prep_template_id )
 ) ;

CREATE INDEX idx_study_prep_template_0 ON qiita.study_prep_template ( study_id ) ;

CREATE INDEX idx_study_prep_template_1 ON qiita.study_prep_template ( prep_template_id ) ;

COMMENT ON TABLE qiita.study_prep_template IS 'links study to its prep templates';

ALTER TABLE qiita.study_prep_template ADD CONSTRAINT fk_study_prep_template_study FOREIGN KEY ( study_id ) REFERENCES qiita.study( study_id )    ;

ALTER TABLE qiita.study_prep_template ADD CONSTRAINT fk_study_prep_template_pt FOREIGN KEY ( prep_template_id ) REFERENCES qiita.prep_template( prep_template_id )    ;

-- Connect the existing prep templates in the system with their studies
WITH pt_st AS (SELECT prep_template_id, study_id
               FROM qiita.prep_template
                    JOIN qiita.study_raw_data USING (raw_data_id))


DROP TABLE qiita.study_raw_data;

