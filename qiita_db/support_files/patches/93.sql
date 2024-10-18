-- Oct 18, 2024
-- ProcessingJob.create can take up to 52 seconds if creating a complete_job; mainly
-- due to the number of jobs of this command and using json. The solution in the database
-- is to convert to jsonb and index the values of the database

-- ### This are the stats before the change in a single example
-- GroupAggregate  (cost=67081.81..67081.83 rows=1 width=77) (actual time=51859.962..51862.637 rows=1 loops=1)
-- 	Group Key: processing_job.processing_job_id, processing_job_status.processing_job_status
-- 	->  Sort  (cost=67081.81..67081.81 rows=1 width=77) (actual time=51859.952..51862.627 rows=1 loops=1)
-- 				Sort Key: processing_job.processing_job_id, processing_job_status.processing_job_status
-- 				Sort Method: quicksort  Memory: 25kB
-- 				->  Nested Loop Left Join  (cost=4241.74..67081.80 rows=1 width=77) (actual time=51859.926..51862.604 rows=1 loops=1)
-- 							->  Nested Loop  (cost=4237.30..67069.64 rows=1 width=69) (actual time=51859.889..51862.566 rows=1 loops=1)
-- 										Join Filter: (processing_job.processing_job_status_id = processing_job_status.processing_job_status_id)
-- 										Rows Removed by Join Filter: 1
-- 										->  Gather  (cost=4237.30..67068.50 rows=1 width=45) (actual time=51859.846..51862.522 rows=1 loops=1)
-- 													Workers Planned: 2
-- 													Workers Launched: 2
-- 													->  Parallel Bitmap Heap Scan on processing_job  (cost=3237.30..66068.40 rows=1 width=45) (actual time=51785.317..51785.446 rows=0 loops=3)
-- 																Recheck Cond: (command_id = 83)
-- 																Filter: (((command_parameters ->> 'job_id'::text) ~~* '3432a908-f7b8-4e36-89fc-88f3310b84d5'::text) AND ((command_parameters ->> '
-- payload'::text) ~~* '{"success": true, "error": "", "artifacts": {"alpha_diversity": {"artifact_type": "alpha_vector", "filepaths": [["/qmounts/qiita_test_data/tes
-- tlocal/working_dir/3432a908-f7b8-4e36-89fc-88f3310b84d5/alpha_phylogenetic/alpha_diversity/alpha-diversity.tsv", "plain_text"], ["/qmounts/qiita_test_data/testloca
-- l/working_dir/3432a908-f7b8-4e36-89fc-88f3310b84d5/alpha_phylogenetic/alpha_diversity.qza", "qza"]], "archive": {}}}}'::text))
-- 																Rows Removed by Filter: 97315
-- 																Heap Blocks: exact=20133
-- 																->  Bitmap Index Scan on idx_processing_job_command_id  (cost=0.00..3237.30 rows=294517 width=0) (actual time=41.569..41.569 rows=
-- 293054 loops=1)
-- 																			Index Cond: (command_id = 83)
-- 										->  Seq Scan on processing_job_status  (cost=0.00..1.09 rows=4 width=40) (actual time=0.035..0.035 rows=2 loops=1)
-- 													Filter: ((processing_job_status)::text = ANY ('{success,waiting,running,in_construction}'::text[]))
-- 													Rows Removed by Filter: 1
-- 							->  Bitmap Heap Scan on artifact_output_processing_job aopj  (cost=4.43..12.14 rows=2 width=24) (actual time=0.031..0.031 rows=0 loops=1)
-- 										Recheck Cond: (processing_job.processing_job_id = processing_job_id)
-- 										->  Bitmap Index Scan on idx_artifact_output_processing_job_job  (cost=0.00..4.43 rows=2 width=0) (actual time=0.026..0.026 rows=0 loops=1)
-- 													Index Cond: (processing_job_id = processing_job.processing_job_id)
-- Planning Time: 1.173 ms
-- Execution Time: 51862.756 ms

-- Note: for this to work you need to have created as admin the extension
-- CREATE EXTENSION pg_trgm;

-- This alter table will take close to 11 min
ALTER TABLE qiita.processing_job
    ALTER COLUMN command_parameters TYPE JSONB USING command_parameters::jsonb;

-- This indexing will take like 5 min
CREATE INDEX IF NOT EXISTS processing_job_command_parameters_job_id ON qiita.processing_job
  USING GIN((command_parameters->>'job_id') gin_trgm_ops);

-- This indexing will take like an hour
CREATE INDEX IF NOT EXISTS processing_job_command_parameters_payload ON qiita.processing_job
  USING GIN((command_parameters->>'payload') gin_trgm_ops);

-- After the changes
-- 18710.404 ms
