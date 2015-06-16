ALTER TABLE qiita.processed_params_sortmerna ADD param_set_name varchar(100) DEFAULT 'Default' NOT NULL;

COMMENT ON COLUMN qiita.processed_params_sortmerna.param_set_name IS 'The name of the parameter set';
