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

-- for testing: provide creation date for one of the existing users

UPDATE qiita.qiita_user SET creation_timestamp = '2015-12-03 13:52:42.751331-07' WHERE email = 'test@foo.bar';

-- Jun 20, 2024
-- Add some non-verified users to the test DB to test new admin page: /admin/purge_users/

INSERT INTO qiita.qiita_user VALUES ('justnow@nonvalidat.ed', 5, '$2a$12$gnUi8Qg.0tvW243v889BhOBhWLIHyIJjjgaG6dxuRJkUM8nXG9Efe', 'JustNow', 'NonVeriUser', '1634 Edgemont Avenue', '303-492-1984', NULL, NULL, NULL, false, NULL, NULL, NULL, NOW());
INSERT INTO qiita.qiita_user VALUES ('ayearago@nonvalidat.ed', 5, '$2a$12$gnUi8Qg.0tvW243v889BhOBhWLIHyIJjjgaG6dxuRJkUM8nXG9Efe', 'Oldie', 'NonVeriUser', '172 New Lane', '102-111-1984', NULL, NULL, NULL, false, NULL, NULL, NULL, NOW() - INTERVAL '1 YEAR');
INSERT INTO qiita.qiita_user VALUES ('3Xdays@nonvalidat.ed', 5, '$2a$12$gnUi8Qg.0tvW243v889BhOBhWLIHyIJjjgaG6dxuRJkUM8nXG9Efe', 'TooLate', 'NonVeriUser', '564 C Street', '508-492-222', NULL, NULL, NULL, false, NULL, NULL, NULL, NOW() - INTERVAL '30 DAY');
