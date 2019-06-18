-- Jun 17 2019
-- Drop the study_person table and connect tables related to study_person with qiita_user

-- Drop the PK in qiita_user
ALTER TABLE qiita_user DROP CONSTRAINT qiita_user_pk CASCADE;

-- Add new PK qiita_user_id in qiita_user
ALTER TABLE qiita_user ADD COLUMN qiita_user_id BIGSERIAL PRIMARY KEY;

-- Reconnect tables with qiita _user_id
ALTER TABLE analysis ADD COLUMN user_id BIGINT REFERENCES qiita_user(qiita_user_id);
ALTER TABLE analysis_users ADD COLUMN user_id BIGINT REFERENCES qiita_user(qiita_user_id);
ALTER TABLE study_tags ADD COLUMN user_id BIGINT REFERENCES qiita_user(qiita_user_id);
ALTER TABLE processing_job ADD COLUMN user_id BIGINT REFERENCES qiita_user(qiita_user_id);
ALTER TABLE study ADD COLUMN user_id BIGINT REFERENCES qiita_user(qiita_user_id);
ALTER TABLE study_users ADD COLUMN user_id BIGINT REFERENCES qiita_user(qiita_user_id);

-- Drop table study_person
DROP TABLE study_person CASCADE;

-- Connect to qiita_user
ALTER TABLE study ADD CONSTRAINT fk_study FOREIGN KEY(principal_investigator_id) REFERENCES qiita_user(qiita_user_id);
ALTER TABLE study ADD CONSTRAINT fk_study FOREIGN KEY(lab_person_id) REFERENCES qiita_user(qiita_user_id);
ALTER TABLE investigation ADD CONSTRAINT fk_investigation FOREIGN KEY(contact_person_id) REFERENCES qiita_user(qiita_user_id);

