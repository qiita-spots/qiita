-- September 22, 2015
-- Update the database schema to be able to store all the information that EBI
-- returns, and it is needed to perform further modifications/additions
-- to the information already present in EBI

ALTER TABLE qiita.prep_template_sample ADD ebi_experiment_accession varchar  ;
ALTER TABLE qiita.study ADD ebi_study_accession varchar  ;
ALTER TABLE qiita.study ADD ebi_submission_status varchar  NOT NULL DEFAULT 'not submitted';
ALTER TABLE qiita.study_sample ADD ebi_sample_accession varchar  ;
ALTER TABLE qiita.study_sample ADD biosample_accession varchar  ;

CREATE TABLE qiita.ebi_run_accession (
	sample_id               varchar    NOT NULL,
	preprocessed_data_id    bigint     NOT NULL,
	ebi_run_accession       varchar    NOT NULL,
	CONSTRAINT idx_ebi_run_accession PRIMARY KEY ( sample_id, preprocessed_data_id, ebi_run_accession )
 ) ;
CREATE INDEX idx_ebi_run_accession_sid ON qiita.ebi_run_accession ( sample_id ) ;
CREATE INDEX idx_ebi_run_accession_ppd_id ON qiita.ebi_run_accession ( preprocessed_data_id ) ;
ALTER TABLE qiita.ebi_run_accession ADD CONSTRAINT fk_ebi_run_accession FOREIGN KEY ( sample_id ) REFERENCES qiita.study_sample( sample_id )    ;
ALTER TABLE qiita.ebi_run_accession ADD CONSTRAINT fk_ebi_run_accession_ppd FOREIGN KEY ( preprocessed_data_id ) REFERENCES qiita.preprocessed_data( preprocessed_data_id )    ;

-- Transfer the data from the old structure to the new one.
-- We currently don't have all the data, so we are just going to transfer
-- the study accession numbers and we will pull down the rest of the information
-- from EBI later
WITH ebi_data AS (SELECT study_id, string_agg(ebi_study_accession, ', ') AS ebi_study_accessions
				  FROM qiita.study_preprocessed_data
				  	JOIN qiita.preprocessed_data USING (preprocessed_data_id)
				  WHERE ebi_study_accession IS NOT NULL
				  GROUP BY study_id)
	UPDATE qiita.study AS st
		SET ebi_study_accession = ebi_data.ebi_study_accessions,
			ebi_submission_status = 'success'
		FROM ebi_data
		WHERE st.study_id = ebi_data.study_id;

-- Drop the old columns
ALTER TABLE qiita.preprocessed_data DROP COLUMN submitted_to_insdc_status;
ALTER TABLE qiita.preprocessed_data DROP COLUMN ebi_submission_accession;
ALTER TABLE qiita.preprocessed_data DROP COLUMN ebi_study_accession;
