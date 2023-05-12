-- May 12, 2023
-- add creation_job_id to qiita.prep_template
ALTER TABLE qiita.prep_template ADD creation_job_id UUID DEFAULT NULL;
