-- Nov 1, 2023
-- add creation_job_id to qiita.prep_template
ALTER TABLE qiita.analysis ADD slurm_reservation VARCHAR DEFAULT '' NOT NULL;
ALTER TABLE qiita.user_level ADD slurm_parameters VARCHAR DEFAULT '--nice=10000' NOT NULL;

UPDATE qiita.user_level SET slurm_parameters = '--nice=5000' WHERE name = 'admin';

UPDATE qiita.user_level SET slurm_parameters = '' WHERE name = 'wet-lab admin';
