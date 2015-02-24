-- Feb 23, 2015
-- This patch adds the status to the processed data object
-- We take advantage of the study status table as the values should be the same
-- The default value for the processed data so the patch can be applied is the
-- sandbox value (id = 4). This value will be then corrected in 16.py.

ALTER TABLE qiita.processed_data ADD processed_data_status_id bigint DEFAULT 4 NOT NULL;

CREATE INDEX idx_processed_data_0 ON qiita.processed_data ( processed_data_status_id ) ;

ALTER TABLE qiita.processed_data ADD CONSTRAINT fk_processed_data_study_status FOREIGN KEY ( processed_data_status_id ) REFERENCES qiita.study_status( study_status_id )    ;

