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
	job_start            TIMESTAMP,
	node_name            varchar DEFAULT NULL,
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

-- Jun 19, 2024
-- Adding a new column to the user table that logs when this account was created
-- Usefull e.g. to prune non-verified=inactive user or to plot user growth

ALTER TABLE qiita.qiita_user
  ADD creation_timestamp timestamp without time zone DEFAULT NOW();

COMMENT ON COLUMN qiita.qiita_user.creation_timestamp IS 'The date the user account was created';

-- Jun 28, 2024
-- These columns were added by mistake to qiita-db-unpatched.sql in PR:
-- https://github.com/qiita-spots/qiita/pull/3412 so adding here now

ALTER TABLE qiita.qiita_user ADD social_orcid character varying DEFAULT NULL;
ALTER TABLE qiita.qiita_user ADD social_researchgate character varying DEFAULT NULL;
ALTER TABLE qiita.qiita_user ADD social_googlescholar character varying DEFAULT NULL;

-- Add human_reads_filter_method so we can keep track of the available methods
-- and link them to the preparations

CREATE  TABLE qiita.human_reads_filter_method (
	human_reads_filter_method_id    bigint  NOT NULL,
	human_reads_filter_method_method character varying NOT NULL;
	CONSTRAINT pk_human_reads_filter_method_id PRIMARY KEY (
    human_reads_filter_method_id )
 );

ALTER TABLE qiita.prep_template
  ADD human_reads_filter_method_id bigint DEFAULT NULL;
ALTER TABLE qiita.prep_template
  ADD CONSTRAINT fk_human_reads_filter_method
  FOREIGN KEY ( human_reads_filter_method_id )
  REFERENCES qiita.human_reads_filter_method ( human_reads_filter_method_id );
