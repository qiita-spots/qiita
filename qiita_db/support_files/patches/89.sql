-- Nov 1, 2023
-- add creation_job_id to qiita.prep_template
ALTER TABLE qiita.analysis ADD slurm_reservation VARCHAR DEFAULT '' NOT NULL;
ALTER TABLE qiita.user_level ADD slurm_parameters VARCHAR DEFAULT '' NOT NULL;
