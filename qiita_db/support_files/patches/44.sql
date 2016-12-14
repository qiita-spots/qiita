-- Dec 14, 2016
-- Keeping track of the validator jobs

CREATE TABLE qiita.processing_job_validator (
	processing_job_id    UUID  NOT NULL,
	validator_id         UUID  NOT NULL,
	artifact_info        json,
	CONSTRAINT idx_processing_job_validator PRIMARY KEY ( processing_job_id, validator_id )
 ) ;
CREATE INDEX idx_processing_job_validator_0 ON qiita.processing_job_validator ( processing_job_id ) ;
CREATE INDEX idx_processing_job_validator_1 ON qiita.processing_job_validator ( validator_id ) ;
ALTER TABLE qiita.processing_job_validator ADD CONSTRAINT fk_processing_job_validator_p FOREIGN KEY ( processing_job_id ) REFERENCES qiita.processing_job( processing_job_id )    ;
ALTER TABLE qiita.processing_job_validator ADD CONSTRAINT fk_processing_job_validator_c FOREIGN KEY ( validator_id ) REFERENCES qiita.processing_job( processing_job_id )    ;
