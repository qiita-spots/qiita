-- May 25, 2021
-- Adding max samples in a single preparation
-- we need to do it via a DO because IF NOT EXISTS in ALTER TABLE only exists
-- in PostgreSQL 9.6 or higher and we use 9.5
DO $do$
BEGIN
  IF NOT EXISTS (
    SELECT DISTINCT table_name FROM information_schema.columns
        WHERE table_name = 'settings' AND column_name = 'max_preparation_samples'
     ) THEN
     ALTER TABLE settings ADD COLUMN max_preparation_samples INT DEFAULT 800;
  END IF;
END $do$;

ALTER TABLE qiita.analysis
  DROP CONSTRAINT fk_analysis_user,
  ADD CONSTRAINT fk_analysis_user
    FOREIGN KEY (email)
    REFERENCES qiita.qiita_user(email)
    ON UPDATE CASCADE;

ALTER TABLE qiita.study_users
  DROP CONSTRAINT fk_study_users_user,
  ADD CONSTRAINT fk_study_users_user
    FOREIGN KEY (email)
    REFERENCES qiita.qiita_user(email)
    ON UPDATE CASCADE;

ALTER TABLE qiita.message_user
  DROP CONSTRAINT fk_message_user_0,
  ADD CONSTRAINT fk_message_user_0
    FOREIGN KEY (email)
    REFERENCES qiita.qiita_user(email)
    ON UPDATE CASCADE;

ALTER TABLE qiita.processing_job
  DROP CONSTRAINT fk_processing_job_qiita_user,
  ADD CONSTRAINT fk_processing_job_qiita_user
    FOREIGN KEY (email)
    REFERENCES qiita.qiita_user(email)
    ON UPDATE CASCADE;

ALTER TABLE qiita.processing_job_workflow
  DROP CONSTRAINT fk_processing_job_workflow,
  ADD CONSTRAINT fk_processing_job_workflow
    FOREIGN KEY (email)
    REFERENCES qiita.qiita_user(email)
    ON UPDATE CASCADE;

ALTER TABLE qiita.study
  DROP CONSTRAINT fk_study_user,
  ADD CONSTRAINT fk_study_user
    FOREIGN KEY (email)
    REFERENCES qiita.qiita_user(email)
    ON UPDATE CASCADE;
