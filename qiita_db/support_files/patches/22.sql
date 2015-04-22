-- April 16, 2015
-- Add primary key to analysis_sample table
ALTER TABLE qiita.analysis_sample ADD CONSTRAINT pk_analysis_sample PRIMARY KEY ( analysis_id, processed_data_id, sample_id );