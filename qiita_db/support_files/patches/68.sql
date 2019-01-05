-- January 4, 2019
-- add external_job_id column to record mapping of Torque Job IDs to Qiita Job IDs.
-- COMMENT ON COLUMN qiita.processing_job IS 'Store an external job ID (e.g. Torque job ID) associated this Qiita job.';

ALTER TABLE qiita.processing_job ADD external_job_id varchar;
COMMENT ON COLUMN qiita.processing_job.external_job_id IS 'Store an external job ID (e.g. Torque job ID) associated this Qiita job.';

