CREATE TABLE settings ( 
	test                 bool DEFAULT True NOT NULL,
	base_data_dir        varchar  NOT NULL,
	base_work_dir        varchar NOT NULL,
	current_patch        varchar DEFAULT 'unpatched' NOT NULL
);
