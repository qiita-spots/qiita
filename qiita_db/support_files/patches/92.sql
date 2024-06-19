-- Apr 16, 2024
-- Adding a new table to contain the basic slurm information to minimize
-- the number of times we need to retrieve this information

CREATE  TABLE qiita.slurm_resource_allocations (
	processing_job_id    uuid  NOT NULL,
	samples              integer,
	columns              integer,
	input_size           bigint,
	extra_info           varchar DEFAULT NULL,
	memory_used          bigint,
	walltime_used        integer,
	CONSTRAINT pk_slurm_resource_allocations_processing_job_id PRIMARY KEY (
    processing_job_id )
 );

ALTER TABLE qiita.slurm_resource_allocations
  ADD CONSTRAINT fk_slurm_resource_allocations
  FOREIGN KEY ( processing_job_id )
  REFERENCES qiita.processing_job ( processing_job_id );

-- Apr 21, 2024
-- Adding a new column: current_human_filtering to qiita.prep_template
ALTER TABLE qiita.prep_template ADD current_human_filtering boolean DEFAULT False;

-- Apr 22, 2024
-- Adding a new column: reprocess_job_id to qiita.prep_template to keep track of
-- the job that reprocessed this prep
ALTER TABLE qiita.prep_template ADD reprocess_job_id uuid DEFAULT NULL;

-- Jun 19, 2024
-- Adding a new column to the user table that logs when this account was created
-- Usefull e.g. to prune non-verified=inactive user or to plot user growth

ALTER TABLE qiita.qiita_user
  ADD creation_timestamp timestamp without time zone DEFAULT NOW();

COMMENT ON COLUMN qiita.qiita_user.creation_timestamp IS 'The date the user account was created';

-- for testing: provide creation date for one of the existing users

UPDATE SET creation_timestamp = '2015-12-03 13:52:42.751331-07' WHERE email = 'test@foo.bar';
