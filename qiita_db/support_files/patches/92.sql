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
	start_stamp			 TIMESTAMP,
	node_name			 varchar DEFAULT NULL,
	node_model           varchar DEFAULT NULL,
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
