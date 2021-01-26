-- Jan 25, 2021
-- Add creation_timestamp and modification_timestamp for qiita.prep_template

ALTER TABLE qiita.prep_template ADD creation_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE qiita.prep_template ADD modification_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
