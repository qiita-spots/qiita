-- Nov 1, 2023
-- add slurm/queues changes to support per user_level and analysis parameters
ALTER TABLE qiita.analysis ADD slurm_reservation VARCHAR DEFAULT '' NOT NULL;
ALTER TABLE qiita.user_level ADD slurm_parameters VARCHAR DEFAULT '--nice=10000' NOT NULL;

UPDATE qiita.user_level SET slurm_parameters = '--nice=5000' WHERE name = 'admin';

UPDATE qiita.user_level SET slurm_parameters = '' WHERE name = 'wet-lab admin';

-- Nov 22, 2023
-- add changes to support workflow per sample/prep info specific parameters values
ALTER TABLE qiita.default_workflow ADD parameters JSONB DEFAULT '{"sample": {}, "prep": {}}'::JSONB NOT NULL;
