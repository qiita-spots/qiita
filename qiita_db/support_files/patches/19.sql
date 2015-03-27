-- March 19, 2015
-- Removes the status from the study and adds it to the processed data table.

-- Modify the study_status_table so it becomes the processed_data_status table
ALTER TABLE qiita.study_status RENAME TO processed_data_status;
ALTER TABLE qiita.processed_data_status RENAME COLUMN study_status_id TO processed_data_status_id;
ALTER TABLE qiita.processed_data_status RENAME COLUMN status TO processed_data_status;

-- The description of the statuses are referencing to the study, update them
-- so they refer to the processed data
UPDATE qiita.processed_data_status SET description='Anyone can see this processed data' WHERE processed_data_status_id=2;
UPDATE qiita.processed_data_status SET description='Only owner and shared users can see this processed data' WHERE processed_data_status_id=3;

-- Modify the processed_data table so it include the status column, which
-- is a FK to the processed_data_status table
ALTER TABLE qiita.processed_data ADD processed_data_status_id bigint DEFAULT 4 NOT NULL;
CREATE INDEX idx_processed_data_0 ON qiita.processed_data ( processed_data_status_id );
ALTER TABLE qiita.processed_data ADD CONSTRAINT fk_processed_data_status FOREIGN KEY ( processed_data_status_id ) REFERENCES qiita.processed_data_status( processed_data_status_id );

-- We need to maintain the previous study status values. Those need to be
-- transferred to the processed data object.
WITH study_values as (SELECT study_id, study_status_id FROM qiita.study)
UPDATE qiita.processed_data as pd
    SET processed_data_status_id=sv.study_status_id
    FROM study_values sv
    WHERE pd.processed_data_id IN (
        SELECT processed_data_id FROM qiita.study_processed_data
        WHERE study_id = sv.study_id);


-- We no longer need the status column on the study table
ALTER TABLE qiita.study DROP CONSTRAINT fk_study_study_status;
DROP INDEX qiita.idx_study_0;
ALTER TABLE qiita.study DROP COLUMN study_status_id;