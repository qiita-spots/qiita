-- Jun 17 2019
-- Drop the study_person table and connect tables related to study_person with qiita_user

-- Drop the PK in qiita_user
ALTER TABLE qiita.qiita_user DROP CONSTRAINT pk_user CASCADE;

-- Add new PK qiita_user_id in qiita_user
ALTER TABLE qiita.qiita_user ADD COLUMN qiita_user_id BIGSERIAL PRIMARY KEY;

-- Reconnect tables with qiita _user_id
ALTER TABLE qiita.analysis ADD COLUMN user_id BIGINT REFERENCES qiita.qiita_user(qiita_user_id);
UPDATE qiita.analysis SET user_id = qiita.qiita_user.qiita_user_id FROM qiita.qiita_user WHERE qiita.analysis.email = qiita.qiita_user.email;
-- ALTER TABLE qiita.analysis DROP COLUMN email CASCADE;

ALTER TABLE qiita.analysis_users ADD COLUMN user_id BIGINT REFERENCES qiita.qiita_user(qiita_user_id);
UPDATE qiita.analysis_users SET user_id = qiita.qiita_user.qiita_user_id FROM qiita.qiita_user WHERE qiita.analysis_users.email = qiita.qiita_user.email;
-- ALTER TABLE qiita.analysis_users DROP COLUMN email CASCADE;

ALTER TABLE qiita.study_tags ADD COLUMN user_id BIGINT REFERENCES qiita.qiita_user(qiita_user_id);
UPDATE qiita.study_tags SET user_id = qiita.qiita_user.qiita_user_id FROM qiita.qiita_user WHERE qiita.study_tags.email = qiita.qiita_user.email;
-- ALTER TABLE qiita.study_tags DROP COLUMN email CASCADE;

ALTER TABLE qiita.processing_job_workflow ADD COLUMN user_id BIGINT REFERENCES qiita.qiita_user(qiita_user_id);
UPDATE qiita.processing_job_workflow SET user_id = qiita.qiita_user.qiita_user_id FROM qiita.qiita_user WHERE qiita.processing_job_workflow.email = qiita.qiita_user.email;
-- ALTER TABLE qiita.processing_job_workflow DROP COLUMN email CASCADE;

ALTER TABLE qiita.study ADD COLUMN user_id BIGINT REFERENCES qiita.qiita_user(qiita_user_id);
UPDATE qiita.study SET user_id = qiita.qiita_user.qiita_user_id FROM qiita.qiita_user WHERE qiita.study.email = qiita.qiita_user.email;
-- ALTER TABLE qiita.study DROP COLUMN email CASCADE;

ALTER TABLE qiita.study_users ADD COLUMN user_id BIGINT REFERENCES qiita.qiita_user(qiita_user_id);
UPDATE qiita.study_users SET user_id = qiita.qiita_user.qiita_user_id FROM qiita.qiita_user WHERE qiita.study_users.email = qiita.qiita_user.email;
-- ALTER TABLE qiita.study_users DROP COLUMN email CASCADE;

-- Drop table study_person
DROP TABLE qiita.study_person CASCADE;
