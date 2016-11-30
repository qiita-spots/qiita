-- Nov 30, 2016
-- Adding jobs to parent/child artifacts without them

-- returns all artifacts and the jobs that created that are descendants of a_id
CREATE OR REPLACE FUNCTION qiita.artifact_descendants_with_jobs(a_id bigint) RETURNS TABLE (processing_job_id UUID, input_id bigint, output_id bigint) AS $$
BEGIN
    IF EXISTS(SELECT * FROM qiita.artifact WHERE artifact_id = a_id) THEN
        RETURN QUERY WITH RECURSIVE root AS (
          SELECT qiita.artifact_processing_job.processing_job_id AS processing_job_id,
                 qiita.artifact_processing_job.artifact_id AS input_id,
                 qiita.artifact_output_processing_job.artifact_id AS output_id
            FROM qiita.artifact_processing_job
            LEFT JOIN qiita.artifact_output_processing_job USING (processing_job_id)
            WHERE qiita.artifact_processing_job.artifact_id = a_id
          UNION
            SELECT apj.processing_job_id AS processing_job_id,
                   apj.artifact_id AS input_id,
                   aopj.artifact_id AS output_id
              FROM qiita.artifact_processing_job apj
              LEFT JOIN qiita.artifact_output_processing_job aopj USING (processing_job_id)
              JOIN root r ON (r.output_id = apj.artifact_id)
        )
        SELECT DISTINCT root.processing_job_id, root.input_id, root.output_id
            FROM root
            WHERE root.output_id IS NOT NULL
            ORDER BY root.input_id ASC, root.output_id ASC;
    END IF;
END
$$ LANGUAGE plpgsql;
