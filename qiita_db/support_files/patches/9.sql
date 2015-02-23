-- Dec 17, 2014
-- Adding the processing status to all preprocessed_data

ALTER TABLE qiita.preprocessed_data ADD processing_status varchar DEFAULT 'not_processed' NOT NULL;

-- Make sure that the added field is consistent with the data on the database
UPDATE qiita.preprocessed_data SET processing_status='processed' WHERE preprocessed_data_id IN (
	SELECT preprocessed_data_id FROM qiita.preprocessed_processed_data);
