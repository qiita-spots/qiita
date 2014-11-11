CREATE SCHEMA qiita;

CREATE TABLE qiita.analysis_status ( 
	analysis_status_id   bigserial  NOT NULL,
	status               varchar  NOT NULL,
	CONSTRAINT pk_analysis_status PRIMARY KEY ( analysis_status_id ),
	CONSTRAINT idx_analysis_status UNIQUE ( status ) 
 );

CREATE TABLE qiita.checksum_algorithm ( 
	checksum_algorithm_id bigserial  NOT NULL,
	name                 varchar  NOT NULL,
	CONSTRAINT pk_checksum_algorithm PRIMARY KEY ( checksum_algorithm_id ),
	CONSTRAINT idx_checksum_algorithm UNIQUE ( name ) 
 );

CREATE TABLE qiita.command ( 
	command_id           bigserial  NOT NULL,
	name                 varchar  NOT NULL,
	command              varchar  NOT NULL,
	input                varchar  NOT NULL,
	required             varchar  NOT NULL,
	optional             varchar  NOT NULL,
	output               varchar  NOT NULL,
	CONSTRAINT pk_command PRIMARY KEY ( command_id )
 );

COMMENT ON TABLE qiita.command IS 'Available commands for jobs';

COMMENT ON COLUMN qiita.command.command_id IS 'Unique identifier for function';

COMMENT ON COLUMN qiita.command.command IS 'What command to call to run this function';

COMMENT ON COLUMN qiita.command.input IS 'JSON of input options for the command';

COMMENT ON COLUMN qiita.command.required IS 'JSON of required options for the command';

COMMENT ON COLUMN qiita.command.optional IS 'JSON of optional options for command';

COMMENT ON COLUMN qiita.command.output IS 'JSON of output options for the command';

CREATE TABLE qiita.controlled_vocab ( 
	controlled_vocab_id  bigserial  NOT NULL,
	controlled_vocab     varchar  NOT NULL,
	CONSTRAINT pk_controlled_vocabularies PRIMARY KEY ( controlled_vocab_id )
 );

CREATE TABLE qiita.controlled_vocab_values ( 
	vocab_value_id       bigserial  NOT NULL,
	controlled_vocab_id  bigint  NOT NULL,
	term                 varchar  NOT NULL,
	order_by             varchar  NOT NULL,
	default_item         varchar  ,
	CONSTRAINT pk_controlled_vocab_values PRIMARY KEY ( vocab_value_id ),
	CONSTRAINT fk_controlled_vocab_values FOREIGN KEY ( controlled_vocab_id ) REFERENCES qiita.controlled_vocab( controlled_vocab_id ) ON DELETE CASCADE ON UPDATE CASCADE
 );

CREATE INDEX idx_controlled_vocab_values ON qiita.controlled_vocab_values ( controlled_vocab_id );

CREATE TABLE qiita.data_directory ( 
	data_directory_id    bigserial  NOT NULL,
	data_type            varchar  NOT NULL,
	mountpoint           varchar  NOT NULL,
	subdirectory         varchar  NOT NULL,
	active               bool  NOT NULL,
	CONSTRAINT pk_data_directory PRIMARY KEY ( data_directory_id )
 );

CREATE TABLE qiita.data_type ( 
	data_type_id         bigserial  NOT NULL,
	data_type            varchar  NOT NULL,
	CONSTRAINT pk_data_type PRIMARY KEY ( data_type_id ),
	CONSTRAINT idx_data_type UNIQUE ( data_type ) 
 );

COMMENT ON COLUMN qiita.data_type.data_type IS 'Data type (16S, metabolome, etc) the job will use';

CREATE TABLE qiita.emp_status ( 
	emp_status_id        bigserial  NOT NULL,
	emp_status           varchar  NOT NULL,
	CONSTRAINT pk_emp_status PRIMARY KEY ( emp_status_id ),
	CONSTRAINT idx_emp_status UNIQUE ( emp_status ) 
 );

COMMENT ON TABLE qiita.emp_status IS 'All possible statuses for projects relating to EMP. Whether they are part of, processed in accordance to, or not part of EMP.';

CREATE TABLE qiita.filepath_type ( 
	filepath_type_id     bigserial  NOT NULL,
	filepath_type        varchar  ,
	CONSTRAINT pk_filepath_type PRIMARY KEY ( filepath_type_id ),
	CONSTRAINT idx_filepath_type UNIQUE ( filepath_type ) 
 );

CREATE TABLE qiita.filetype ( 
	filetype_id          bigserial  NOT NULL,
	type                 varchar  NOT NULL,
	CONSTRAINT pk_filetype PRIMARY KEY ( filetype_id ),
	CONSTRAINT idx_filetype UNIQUE ( type ) 
 );

COMMENT ON TABLE qiita.filetype IS 'Type of file (FASTA, FASTQ, SPECTRA, etc)';

CREATE TABLE qiita.job_status ( 
	job_status_id        bigserial  NOT NULL,
	status               varchar  NOT NULL,
	CONSTRAINT pk_job_status PRIMARY KEY ( job_status_id ),
	CONSTRAINT idx_job_status_0 UNIQUE ( status ) 
 );

CREATE TABLE qiita.mixs_field_description ( 
	column_name          varchar  NOT NULL,
	data_type            varchar  NOT NULL,
	desc_or_value        varchar  NOT NULL,
	definition           varchar  NOT NULL,
	min_length           integer  ,
	active               integer  NOT NULL,
	CONSTRAINT pk_mixs_field_description PRIMARY KEY ( column_name )
 );

CREATE TABLE qiita.ontology ( 
	ontology_id          bigint  NOT NULL,
	ontology             varchar  NOT NULL,
	fully_loaded         bool  NOT NULL,
	fullname             varchar  ,
	query_url            varchar  ,
	source_url           varchar  ,
	definition           text  ,
	load_date            date  NOT NULL,
	CONSTRAINT pk_ontology PRIMARY KEY ( ontology_id ),
	CONSTRAINT idx_ontology UNIQUE ( ontology ) 
 );

CREATE TABLE qiita.portal_type ( 
	portal_type_id       bigserial  NOT NULL,
	portal               varchar  NOT NULL,
	description          varchar  NOT NULL,
	CONSTRAINT pk_portal_type PRIMARY KEY ( portal_type_id )
 );

COMMENT ON TABLE qiita.portal_type IS 'What portals are available to show a study in';

CREATE TABLE qiita.preprocessed_data ( 
	preprocessed_data_id bigserial  NOT NULL,
	preprocessed_params_table varchar  NOT NULL,
	preprocessed_params_id bigint  NOT NULL,
	submitted_to_insdc_status varchar DEFAULT 'not submitted' NOT NULL,
	ebi_submission_accession varchar  ,
	ebi_study_accession  varchar  ,
	data_type_id         bigint  NOT NULL,
	link_filepaths_status varchar DEFAULT 'idle' NOT NULL,
	CONSTRAINT pk_preprocessed_data PRIMARY KEY ( preprocessed_data_id ),
	CONSTRAINT fk_preprocessed_data FOREIGN KEY ( data_type_id ) REFERENCES qiita.data_type( data_type_id )    
 );

CREATE INDEX idx_preprocessed_data ON qiita.preprocessed_data ( data_type_id );

COMMENT ON COLUMN qiita.preprocessed_data.preprocessed_params_table IS 'Name of table holding the params';

CREATE TABLE qiita.preprocessed_sequence_454_params ( 
	preprocessed_params_id bigserial  NOT NULL,
	trim_length          integer  NOT NULL,
	CONSTRAINT pk_preprocessed_sequence_454_params PRIMARY KEY ( preprocessed_params_id )
 );

COMMENT ON TABLE qiita.preprocessed_sequence_454_params IS 'Parameters used for processing sequence data.';

CREATE TABLE qiita.preprocessed_sequence_illumina_params ( 
	preprocessed_params_id bigserial  NOT NULL,
	max_bad_run_length   integer DEFAULT 3 NOT NULL,
	min_per_read_length_fraction real DEFAULT 0.75 NOT NULL,
	sequence_max_n       integer DEFAULT 0 NOT NULL,
	rev_comp_barcode     bool DEFAULT FALSE NOT NULL,
	rev_comp_mapping_barcodes bool DEFAULT FALSE NOT NULL,
	rev_comp             bool DEFAULT FALSE NOT NULL,
	phred_quality_threshold integer DEFAULT 3 NOT NULL,
	barcode_type         varchar DEFAULT 'golay_12' NOT NULL,
	max_barcode_errors   real DEFAULT 1.5 NOT NULL,
	CONSTRAINT pk_preprocessed_sequence_illumina_params PRIMARY KEY ( preprocessed_params_id )
 );

COMMENT ON TABLE qiita.preprocessed_sequence_illumina_params IS 'Parameters used for processing illumina sequence data.';

CREATE TABLE qiita.preprocessed_spectra_params ( 
	preprocessed_params_id bigserial  NOT NULL,
	col                  varchar  ,
	CONSTRAINT pk_preprocessed_spectra_params PRIMARY KEY ( preprocessed_params_id )
 );

COMMENT ON TABLE qiita.preprocessed_spectra_params IS 'Parameters used for processing spectra data.';

CREATE TABLE qiita.processed_data ( 
	processed_data_id    bigserial  NOT NULL,
	processed_params_table varchar  NOT NULL,
	processed_params_id  bigint  NOT NULL,
	processed_date       timestamp  NOT NULL,
	data_type_id         bigint  NOT NULL,
	link_filepaths_status varchar DEFAULT 'idle' NOT NULL,
	CONSTRAINT pk_processed_data PRIMARY KEY ( processed_data_id ),
	CONSTRAINT fk_processed_data FOREIGN KEY ( data_type_id ) REFERENCES qiita.data_type( data_type_id )    
 );

CREATE INDEX idx_processed_data ON qiita.processed_data ( data_type_id );

COMMENT ON COLUMN qiita.processed_data.processed_params_table IS 'Name of table holding processing params';

COMMENT ON COLUMN qiita.processed_data.processed_params_id IS 'Link to a table with the parameters used to generate processed data';

CREATE TABLE qiita.raw_data ( 
	raw_data_id          bigserial  NOT NULL,
	filetype_id          bigint  NOT NULL,
	link_filepaths_status varchar DEFAULT 'idle' NOT NULL,
	CONSTRAINT pk_raw_data UNIQUE ( raw_data_id ) ,
	CONSTRAINT pk_raw_data_0 PRIMARY KEY ( raw_data_id ),
	CONSTRAINT fk_raw_data_filetype FOREIGN KEY ( filetype_id ) REFERENCES qiita.filetype( filetype_id )    
 );

CREATE INDEX idx_raw_data ON qiita.raw_data ( filetype_id );

CREATE TABLE qiita.required_sample_info_status ( 
	required_sample_info_status_id bigserial  NOT NULL,
	status               varchar  ,
	CONSTRAINT pk_sample_status PRIMARY KEY ( required_sample_info_status_id ),
	CONSTRAINT idx_required_sample_info_status UNIQUE ( status ) 
 );

CREATE TABLE qiita.severity ( 
	severity_id          serial  NOT NULL,
	severity             varchar  NOT NULL,
	CONSTRAINT pk_severity PRIMARY KEY ( severity_id ),
	CONSTRAINT idx_severity UNIQUE ( severity ) 
 );

CREATE TABLE qiita.study_person ( 
	study_person_id      bigserial  NOT NULL,
	name                 varchar  NOT NULL,
	email                varchar  NOT NULL,
	affiliation          varchar  NOT NULL,
	address              varchar(100)  ,
	phone                varchar  ,
	CONSTRAINT pk_study_person PRIMARY KEY ( study_person_id ),
	CONSTRAINT idx_study_person UNIQUE ( name, affiliation ) 
 );

COMMENT ON TABLE qiita.study_person IS 'Contact information for the various people involved in a study';

COMMENT ON COLUMN qiita.study_person.affiliation IS 'The institution with which this person is affiliated';

CREATE TABLE qiita.study_status ( 
	study_status_id      bigserial  NOT NULL,
	status               varchar  NOT NULL,
	description          varchar  NOT NULL,
	CONSTRAINT pk_study_status PRIMARY KEY ( study_status_id ),
	CONSTRAINT idx_study_status UNIQUE ( status ) 
 );

CREATE TABLE qiita.term ( 
	term_id              bigserial  NOT NULL,
	ontology_id          bigint  NOT NULL,
	old_term_id          bigint DEFAULT NULL ,
	term                 varchar  NOT NULL,
	identifier           varchar  ,
	definition           varchar  ,
	namespace            varchar  ,
	is_obsolete          bool DEFAULT 'false' ,
	is_root_term         bool  ,
	is_leaf              bool  ,
	user_defined         bool DEFAULT False NOT NULL,
	CONSTRAINT pk_term PRIMARY KEY ( term_id ),
	CONSTRAINT fk_term_ontology FOREIGN KEY ( ontology_id ) REFERENCES qiita.ontology( ontology_id )    
 );

CREATE INDEX idx_term ON qiita.term ( ontology_id );

COMMENT ON COLUMN qiita.term.old_term_id IS 'Identifier used in the old system, we are keeping this for consistency';

COMMENT ON COLUMN qiita.term.user_defined IS 'Whether or not this term was defined by a user';

CREATE TABLE qiita.timeseries_type ( 
	timeseries_type_id   bigserial  NOT NULL,
	timeseries_type      varchar  NOT NULL,
	CONSTRAINT pk_timeseries_type PRIMARY KEY ( timeseries_type_id ),
	CONSTRAINT idx_timeseries_type UNIQUE ( timeseries_type ) 
 );

CREATE TABLE qiita.user_level ( 
	user_level_id        serial  NOT NULL,
	name                 varchar  NOT NULL,
	description          text  NOT NULL,
	CONSTRAINT pk_user_level PRIMARY KEY ( user_level_id ),
	CONSTRAINT idx_user_level UNIQUE ( name ) 
 );

COMMENT ON TABLE qiita.user_level IS 'Holds available user levels';

COMMENT ON COLUMN qiita.user_level.name IS 'One of the user levels (admin, user, guest, etc)';

CREATE TABLE qiita.column_controlled_vocabularies ( 
	controlled_vocab_id  bigserial  NOT NULL,
	column_name          varchar  NOT NULL,
	CONSTRAINT idx_column_controlled_vocabularies PRIMARY KEY ( controlled_vocab_id, column_name ),
	CONSTRAINT fk_column_controlled_vocabularies FOREIGN KEY ( column_name ) REFERENCES qiita.mixs_field_description( column_name )    ,
	CONSTRAINT fk_column_controlled_vocab2 FOREIGN KEY ( controlled_vocab_id ) REFERENCES qiita.controlled_vocab( controlled_vocab_id )    
 );

CREATE INDEX idx_column_controlled_vocabularies_0 ON qiita.column_controlled_vocabularies ( column_name );

CREATE INDEX idx_column_controlled_vocabularies_1 ON qiita.column_controlled_vocabularies ( controlled_vocab_id );

COMMENT ON TABLE qiita.column_controlled_vocabularies IS 'Table relates a column with a controlled vocabulary.';

CREATE TABLE qiita.column_ontology ( 
	column_name          varchar  NOT NULL,
	ontology_short_name  varchar  NOT NULL,
	bioportal_id         integer  NOT NULL,
	ontology_branch_id   varchar  ,
	CONSTRAINT idx_column_ontology PRIMARY KEY ( column_name, ontology_short_name ),
	CONSTRAINT fk_column_ontology FOREIGN KEY ( column_name ) REFERENCES qiita.mixs_field_description( column_name )    
 );

CREATE INDEX idx_column_ontology_0 ON qiita.column_ontology ( column_name );

COMMENT ON TABLE qiita.column_ontology IS 'This table relates a column with an ontology.';

CREATE TABLE qiita.command_data_type ( 
	command_id           bigint  NOT NULL,
	data_type_id         bigint  NOT NULL,
	CONSTRAINT idx_command_data_type PRIMARY KEY ( command_id, data_type_id ),
	CONSTRAINT fk_command_data_type FOREIGN KEY ( command_id ) REFERENCES qiita.command( command_id )    ,
	CONSTRAINT fk_command_data_type_0 FOREIGN KEY ( data_type_id ) REFERENCES qiita.data_type( data_type_id )    
 );

CREATE INDEX idx_command_data_type_0 ON qiita.command_data_type ( command_id );

CREATE INDEX idx_command_data_type_1 ON qiita.command_data_type ( data_type_id );

CREATE TABLE qiita.filepath ( 
	filepath_id          bigserial  NOT NULL,
	filepath             varchar  NOT NULL,
	filepath_type_id     bigint  NOT NULL,
	checksum             varchar  NOT NULL,
	checksum_algorithm_id bigint  NOT NULL,
	data_directory_id    bigserial  ,
	CONSTRAINT pk_filepath PRIMARY KEY ( filepath_id ),
	CONSTRAINT fk_filepath FOREIGN KEY ( filepath_type_id ) REFERENCES qiita.filepath_type( filepath_type_id )    ,
	CONSTRAINT fk_filepath_0 FOREIGN KEY ( checksum_algorithm_id ) REFERENCES qiita.checksum_algorithm( checksum_algorithm_id )    ,
	CONSTRAINT fk_filepath_data_directory FOREIGN KEY ( data_directory_id ) REFERENCES qiita.data_directory( data_directory_id ) ON DELETE RESTRICT ON UPDATE RESTRICT
 );

CREATE INDEX idx_filepath ON qiita.filepath ( filepath_type_id );

CREATE INDEX idx_filepath_0 ON qiita.filepath ( data_directory_id );

CREATE TABLE qiita.investigation ( 
	investigation_id     bigserial  NOT NULL,
	name                 varchar  NOT NULL,
	description          varchar  NOT NULL,
	contact_person_id    bigint  ,
	CONSTRAINT pk_investigation PRIMARY KEY ( investigation_id ),
	CONSTRAINT fk_investigation_study_person FOREIGN KEY ( contact_person_id ) REFERENCES qiita.study_person( study_person_id )    
 );

CREATE INDEX idx_investigation ON qiita.investigation ( contact_person_id );

COMMENT ON TABLE qiita.investigation IS 'Overarching investigation information.An investigation comprises one or more individual studies.';

COMMENT ON COLUMN qiita.investigation.description IS 'Describes the overarching goal of the investigation';

CREATE TABLE qiita.logging ( 
	logging_id           bigserial  NOT NULL,
	time                 timestamp  NOT NULL,
	severity_id          integer  NOT NULL,
	msg                  varchar  NOT NULL,
	information          varchar  ,
	CONSTRAINT pk_logging PRIMARY KEY ( logging_id ),
	CONSTRAINT fk_logging_severity FOREIGN KEY ( severity_id ) REFERENCES qiita.severity( severity_id )    
 );

CREATE INDEX idx_logging_0 ON qiita.logging ( severity_id );

COMMENT ON COLUMN qiita.logging.time IS 'Time the error was thrown';

COMMENT ON COLUMN qiita.logging.msg IS 'Error message thrown';

COMMENT ON COLUMN qiita.logging.information IS 'Other applicable information (depending on error)';

CREATE TABLE qiita.prep_template ( 
	prep_template_id     bigserial  NOT NULL,
	data_type_id         bigint  NOT NULL,
	raw_data_id          bigint  NOT NULL,
	preprocessing_status varchar DEFAULT 'not_preprocessed' NOT NULL,
	investigation_type   varchar  ,
	CONSTRAINT pk_prep_template PRIMARY KEY ( prep_template_id ),
	CONSTRAINT fk_prep_template_data_type FOREIGN KEY ( data_type_id ) REFERENCES qiita.data_type( data_type_id )    ,
	CONSTRAINT fk_prep_template_raw_data FOREIGN KEY ( raw_data_id ) REFERENCES qiita.raw_data( raw_data_id )    
 );

CREATE INDEX idx_prep_template ON qiita.prep_template ( data_type_id );

CREATE INDEX idx_prep_template_0 ON qiita.prep_template ( raw_data_id );

COMMENT ON COLUMN qiita.prep_template.investigation_type IS 'The investigation type (e.g., one of the values from EBI`s set of known types)';

CREATE TABLE qiita.prep_template_preprocessed_data ( 
	prep_template_id     bigint  NOT NULL,
	preprocessed_data_id bigint  NOT NULL,
	CONSTRAINT idx_prep_template_preprocessed_data PRIMARY KEY ( prep_template_id, preprocessed_data_id ),
	CONSTRAINT fk_prep_template_id FOREIGN KEY ( prep_template_id ) REFERENCES qiita.prep_template( prep_template_id )    ,
	CONSTRAINT fk_prep_template_preprocessed_data FOREIGN KEY ( preprocessed_data_id ) REFERENCES qiita.preprocessed_data( preprocessed_data_id )    
 );

CREATE INDEX idx_prep_template_preprocessed_data_0 ON qiita.prep_template_preprocessed_data ( prep_template_id );

CREATE INDEX idx_prep_template_preprocessed_data_1 ON qiita.prep_template_preprocessed_data ( preprocessed_data_id );

CREATE TABLE qiita.preprocessed_filepath ( 
	preprocessed_data_id bigint  NOT NULL,
	filepath_id          bigint  NOT NULL,
	CONSTRAINT idx_preprocessed_filepath PRIMARY KEY ( preprocessed_data_id, filepath_id ),
	CONSTRAINT fk_preprocessed_filepath FOREIGN KEY ( preprocessed_data_id ) REFERENCES qiita.preprocessed_data( preprocessed_data_id )    ,
	CONSTRAINT fk_preprocessed_filepath_0 FOREIGN KEY ( filepath_id ) REFERENCES qiita.filepath( filepath_id )    
 );

CREATE INDEX idx_preprocessed_filepath_0 ON qiita.preprocessed_filepath ( preprocessed_data_id );

CREATE INDEX idx_preprocessed_filepath_1 ON qiita.preprocessed_filepath ( filepath_id );

CREATE TABLE qiita.preprocessed_processed_data ( 
	preprocessed_data_id bigint  NOT NULL,
	processed_data_id    bigint  NOT NULL,
	CONSTRAINT idx_preprocessed_processed_data PRIMARY KEY ( preprocessed_data_id, processed_data_id ),
	CONSTRAINT fk_preprocessed_processed_data FOREIGN KEY ( preprocessed_data_id ) REFERENCES qiita.preprocessed_data( preprocessed_data_id )    ,
	CONSTRAINT fk_preprocessed_processed_data_0 FOREIGN KEY ( processed_data_id ) REFERENCES qiita.processed_data( processed_data_id )    
 );

CREATE INDEX idx_preprocessed_processed_data_0 ON qiita.preprocessed_processed_data ( preprocessed_data_id );

CREATE INDEX idx_preprocessed_processed_data_1 ON qiita.preprocessed_processed_data ( processed_data_id );

CREATE TABLE qiita.processed_filepath ( 
	processed_data_id    bigint  NOT NULL,
	filepath_id          bigint  NOT NULL,
	CONSTRAINT idx_processed_filepath PRIMARY KEY ( processed_data_id, filepath_id ),
	CONSTRAINT fk_processed_data_filepath FOREIGN KEY ( processed_data_id ) REFERENCES qiita.processed_data( processed_data_id )    ,
	CONSTRAINT fk_processed_data_filepath_0 FOREIGN KEY ( filepath_id ) REFERENCES qiita.filepath( filepath_id )    
 );

CREATE TABLE qiita.qiita_user ( 
	email                varchar  NOT NULL,
	user_level_id        integer DEFAULT 5 NOT NULL,
	password             varchar  NOT NULL,
	name                 varchar  ,
	affiliation          varchar  ,
	address              varchar  ,
	phone                varchar  ,
	user_verify_code     varchar  ,
	pass_reset_code      varchar  ,
	pass_reset_timestamp timestamp  ,
	CONSTRAINT pk_user PRIMARY KEY ( email ),
	CONSTRAINT fk_user_user_level FOREIGN KEY ( user_level_id ) REFERENCES qiita.user_level( user_level_id )   ON UPDATE RESTRICT
 );

CREATE INDEX idx_user ON qiita.qiita_user ( user_level_id );

COMMENT ON TABLE qiita.qiita_user IS 'Holds all user information';

COMMENT ON COLUMN qiita.qiita_user.user_level_id IS 'user level';

COMMENT ON COLUMN qiita.qiita_user.user_verify_code IS 'Code for initial user email verification';

COMMENT ON COLUMN qiita.qiita_user.pass_reset_code IS 'Randomly generated code for password reset';

COMMENT ON COLUMN qiita.qiita_user.pass_reset_timestamp IS 'Time the reset code was generated';

CREATE TABLE qiita.raw_filepath ( 
	raw_data_id          bigint  NOT NULL,
	filepath_id          bigint  NOT NULL,
	CONSTRAINT idx_raw_filepath PRIMARY KEY ( raw_data_id, filepath_id ),
	CONSTRAINT fk_raw_filepath FOREIGN KEY ( filepath_id ) REFERENCES qiita.filepath( filepath_id )    ,
	CONSTRAINT fk_raw_filepath_0 FOREIGN KEY ( raw_data_id ) REFERENCES qiita.raw_data( raw_data_id )    
 );

CREATE INDEX idx_raw_filepath_0 ON qiita.raw_filepath ( filepath_id );

CREATE INDEX idx_raw_filepath_1 ON qiita.raw_filepath ( raw_data_id );

CREATE TABLE qiita.reference ( 
	reference_id         bigserial  NOT NULL,
	reference_name       varchar  NOT NULL,
	reference_version    varchar  ,
	sequence_filepath    bigint  NOT NULL,
	taxonomy_filepath    bigint  ,
	tree_filepath        bigint  ,
	CONSTRAINT pk_reference PRIMARY KEY ( reference_id ),
	CONSTRAINT fk_reference_sequence_filepath FOREIGN KEY ( sequence_filepath ) REFERENCES qiita.filepath( filepath_id )    ,
	CONSTRAINT fk_reference_taxonomy_filepath FOREIGN KEY ( taxonomy_filepath ) REFERENCES qiita.filepath( filepath_id )    ,
	CONSTRAINT fk_reference_tree_filepath FOREIGN KEY ( tree_filepath ) REFERENCES qiita.filepath( filepath_id )    
 );

CREATE INDEX idx_reference ON qiita.reference ( sequence_filepath );

CREATE INDEX idx_reference_0 ON qiita.reference ( taxonomy_filepath );

CREATE INDEX idx_reference_1 ON qiita.reference ( tree_filepath );

CREATE TABLE qiita.study ( 
	study_id             bigserial  NOT NULL,
	email                varchar  NOT NULL,
	study_status_id      bigint  NOT NULL,
	emp_person_id        bigint  ,
	first_contact        timestamp DEFAULT current_timestamp NOT NULL,
	funding              varchar  ,
	timeseries_type_id   bigint  NOT NULL,
	lab_person_id        bigint  ,
	metadata_complete    bool  NOT NULL,
	mixs_compliant       bool  NOT NULL,
	most_recent_contact  timestamp  ,
	number_samples_collected integer  ,
	number_samples_promised integer  ,
	portal_type_id       bigint  NOT NULL,
	principal_investigator_id bigint  NOT NULL,
	reprocess            bool  NOT NULL,
	spatial_series       bool  ,
	study_title          varchar  NOT NULL,
	study_alias          varchar  NOT NULL,
	study_description    text  NOT NULL,
	study_abstract       text  NOT NULL,
	vamps_id             varchar  ,
	CONSTRAINT pk_study PRIMARY KEY ( study_id ),
	CONSTRAINT unique_study_title UNIQUE ( study_title ) ,
	CONSTRAINT fk_study_user FOREIGN KEY ( email ) REFERENCES qiita.qiita_user( email )    ,
	CONSTRAINT fk_study_study_status FOREIGN KEY ( study_status_id ) REFERENCES qiita.study_status( study_status_id )    ,
	CONSTRAINT fk_study_study_emp_person FOREIGN KEY ( emp_person_id ) REFERENCES qiita.study_person( study_person_id )    ,
	CONSTRAINT fk_study_study_lab_person FOREIGN KEY ( lab_person_id ) REFERENCES qiita.study_person( study_person_id )    ,
	CONSTRAINT fk_study_study_pi_person FOREIGN KEY ( principal_investigator_id ) REFERENCES qiita.study_person( study_person_id )    ,
	CONSTRAINT fk_study_timeseries_type FOREIGN KEY ( timeseries_type_id ) REFERENCES qiita.timeseries_type( timeseries_type_id )    ,
	CONSTRAINT fk_study FOREIGN KEY ( portal_type_id ) REFERENCES qiita.portal_type( portal_type_id )    
 );

CREATE INDEX idx_study ON qiita.study ( email );

CREATE INDEX idx_study_0 ON qiita.study ( study_status_id );

CREATE INDEX idx_study_1 ON qiita.study ( emp_person_id );

CREATE INDEX idx_study_2 ON qiita.study ( lab_person_id );

CREATE INDEX idx_study_3 ON qiita.study ( principal_investigator_id );

CREATE INDEX idx_study_4 ON qiita.study ( timeseries_type_id );

CREATE INDEX idx_study_5 ON qiita.study ( portal_type_id );

COMMENT ON COLUMN qiita.study.study_id IS 'Unique name for study';

COMMENT ON COLUMN qiita.study.email IS 'Email of study owner';

COMMENT ON COLUMN qiita.study.timeseries_type_id IS 'What type of timeseries this study is (or is not)
Controlled Vocabulary';

CREATE TABLE qiita.study_experimental_factor ( 
	study_id             bigint  NOT NULL,
	efo_id               bigint  NOT NULL,
	CONSTRAINT idx_study_experimental_factor PRIMARY KEY ( study_id, efo_id ),
	CONSTRAINT fk_study_experimental_factor FOREIGN KEY ( study_id ) REFERENCES qiita.study( study_id )    
 );

CREATE INDEX idx_study_experimental_factor_0 ON qiita.study_experimental_factor ( study_id );

COMMENT ON TABLE qiita.study_experimental_factor IS 'EFO ontological link of experimental factors to studies';

CREATE TABLE qiita.study_pmid ( 
	study_id             bigint  NOT NULL,
	pmid                 varchar  NOT NULL,
	CONSTRAINT idx_study_pmid PRIMARY KEY ( study_id, pmid ),
	CONSTRAINT fk_study_pmid_study FOREIGN KEY ( study_id ) REFERENCES qiita.study( study_id )    
 );

CREATE INDEX idx_study_pmid_0 ON qiita.study_pmid ( study_id );

COMMENT ON TABLE qiita.study_pmid IS 'Links a study to all PMIDs for papers created from study';

CREATE TABLE qiita.study_preprocessed_data ( 
	study_id             bigint  NOT NULL,
	preprocessed_data_id bigint  NOT NULL,
	CONSTRAINT idx_study_preprocessed_data PRIMARY KEY ( study_id, preprocessed_data_id ),
	CONSTRAINT fk_study_preprocessed_data FOREIGN KEY ( study_id ) REFERENCES qiita.study( study_id )    ,
	CONSTRAINT fk_study_preprocessed_data_0 FOREIGN KEY ( preprocessed_data_id ) REFERENCES qiita.preprocessed_data( preprocessed_data_id )    
 );

CREATE INDEX idx_study_preprocessed_data_0 ON qiita.study_preprocessed_data ( study_id );

CREATE INDEX idx_study_preprocessed_data_1 ON qiita.study_preprocessed_data ( preprocessed_data_id );

CREATE TABLE qiita.study_processed_data ( 
	study_id             bigint  NOT NULL,
	processed_data_id    bigint  NOT NULL,
	CONSTRAINT idx_study_processed_data PRIMARY KEY ( study_id, processed_data_id ),
	CONSTRAINT pk_study_processed_data UNIQUE ( processed_data_id ) ,
	CONSTRAINT fk_study_processed_data FOREIGN KEY ( study_id ) REFERENCES qiita.study( study_id )    ,
	CONSTRAINT fk_study_processed_data_0 FOREIGN KEY ( processed_data_id ) REFERENCES qiita.processed_data( processed_data_id )    
 );

CREATE INDEX idx_study_processed_data_0 ON qiita.study_processed_data ( study_id );

CREATE TABLE qiita.study_raw_data ( 
	study_id             bigint  NOT NULL,
	raw_data_id          bigint  NOT NULL,
	CONSTRAINT idx_study_raw_data_0 PRIMARY KEY ( study_id, raw_data_id ),
	CONSTRAINT fk_study_raw_data_study FOREIGN KEY ( study_id ) REFERENCES qiita.study( study_id )    ,
	CONSTRAINT fk_study_raw_data_raw_data FOREIGN KEY ( raw_data_id ) REFERENCES qiita.raw_data( raw_data_id )    
 );

CREATE INDEX idx_study_raw_data ON qiita.study_raw_data ( study_id );

COMMENT ON TABLE qiita.study_raw_data IS 'links study to its raw data';

CREATE TABLE qiita.study_sample_columns ( 
	study_id             bigint  NOT NULL,
	column_name          varchar(100)  NOT NULL,
	column_type          varchar  NOT NULL,
	CONSTRAINT idx_study_mapping_columns PRIMARY KEY ( study_id, column_name, column_type ),
	CONSTRAINT fk_study_mapping_columns_study FOREIGN KEY ( study_id ) REFERENCES qiita.study( study_id )    
 );

CREATE INDEX idx_study_mapping_columns_study_id ON qiita.study_sample_columns ( study_id );

COMMENT ON TABLE qiita.study_sample_columns IS 'Holds information on which metadata columns are available for the study sample template';

CREATE TABLE qiita.study_users ( 
	study_id             bigint  NOT NULL,
	email                varchar  NOT NULL,
	CONSTRAINT idx_study_users PRIMARY KEY ( study_id, email ),
	CONSTRAINT fk_study_users_study FOREIGN KEY ( study_id ) REFERENCES qiita.study( study_id )    ,
	CONSTRAINT fk_study_users_user FOREIGN KEY ( email ) REFERENCES qiita.qiita_user( email )    
 );

CREATE INDEX idx_study_users_0 ON qiita.study_users ( study_id );

CREATE INDEX idx_study_users_1 ON qiita.study_users ( email );

COMMENT ON TABLE qiita.study_users IS 'Links shared studies to users they are shared with';

CREATE TABLE qiita.analysis ( 
	analysis_id          bigserial  NOT NULL,
	email                varchar  NOT NULL,
	name                 varchar  NOT NULL,
	description          varchar  NOT NULL,
	analysis_status_id   bigint  NOT NULL,
	pmid                 varchar  ,
	timestamp            timestamptz DEFAULT current_timestamp ,
	CONSTRAINT pk_analysis PRIMARY KEY ( analysis_id ),
	CONSTRAINT fk_analysis_user FOREIGN KEY ( email ) REFERENCES qiita.qiita_user( email )    ,
	CONSTRAINT fk_analysis_analysis_status FOREIGN KEY ( analysis_status_id ) REFERENCES qiita.analysis_status( analysis_status_id )    
 );

CREATE INDEX idx_analysis_email ON qiita.analysis ( email );

CREATE INDEX idx_analysis_status_id ON qiita.analysis ( analysis_status_id );

COMMENT ON TABLE qiita.analysis IS 'hHolds analysis information';

COMMENT ON COLUMN qiita.analysis.analysis_id IS 'Unique identifier for analysis';

COMMENT ON COLUMN qiita.analysis.email IS 'Email for user who owns the analysis';

COMMENT ON COLUMN qiita.analysis.name IS 'Name of the analysis';

COMMENT ON COLUMN qiita.analysis.pmid IS 'PMID of paper from the analysis';

CREATE TABLE qiita.analysis_chain ( 
	parent_id            bigint  NOT NULL,
	child_id             bigint  NOT NULL,
	CONSTRAINT idx_analysis_chain_1 PRIMARY KEY ( parent_id, child_id ),
	CONSTRAINT fk_analysis_chain FOREIGN KEY ( parent_id ) REFERENCES qiita.analysis( analysis_id )    ,
	CONSTRAINT fk_analysis_chain_0 FOREIGN KEY ( child_id ) REFERENCES qiita.analysis( analysis_id )    
 );

CREATE INDEX idx_analysis_chain ON qiita.analysis_chain ( parent_id );

CREATE INDEX idx_analysis_chain_0 ON qiita.analysis_chain ( child_id );

COMMENT ON TABLE qiita.analysis_chain IS 'Keeps track of the chain of analysis edits. Tracks what previous analysis a given analysis came from.If a given analysis is not in child_id, it is the root of the chain. ';

CREATE TABLE qiita.analysis_filepath ( 
	analysis_id          bigint  NOT NULL,
	filepath_id          bigint  NOT NULL,
	data_type_id         bigint  ,
	CONSTRAINT idx_analysis_filepath_1 PRIMARY KEY ( analysis_id, filepath_id ),
	CONSTRAINT fk_analysis_filepath FOREIGN KEY ( analysis_id ) REFERENCES qiita.analysis( analysis_id )    ,
	CONSTRAINT fk_analysis_filepath_0 FOREIGN KEY ( filepath_id ) REFERENCES qiita.filepath( filepath_id )    ,
	CONSTRAINT fk_analysis_filepath_1 FOREIGN KEY ( data_type_id ) REFERENCES qiita.data_type( data_type_id )    
 );

CREATE INDEX idx_analysis_filepath ON qiita.analysis_filepath ( analysis_id );

CREATE INDEX idx_analysis_filepath_0 ON qiita.analysis_filepath ( filepath_id );

CREATE INDEX idx_analysis_filepath_2 ON qiita.analysis_filepath ( data_type_id );

COMMENT ON TABLE qiita.analysis_filepath IS 'Stores link between analysis and the data file used for the analysis.';

CREATE TABLE qiita.analysis_users ( 
	analysis_id          bigint  NOT NULL,
	email                varchar  NOT NULL,
	CONSTRAINT idx_analysis_users PRIMARY KEY ( analysis_id, email ),
	CONSTRAINT fk_analysis_users_analysis FOREIGN KEY ( analysis_id ) REFERENCES qiita.analysis( analysis_id ) ON DELETE CASCADE ON UPDATE CASCADE,
	CONSTRAINT fk_analysis_users_user FOREIGN KEY ( email ) REFERENCES qiita.qiita_user( email ) ON DELETE CASCADE ON UPDATE CASCADE
 );

CREATE INDEX idx_analysis_users_analysis ON qiita.analysis_users ( analysis_id );

CREATE INDEX idx_analysis_users_email ON qiita.analysis_users ( email );

COMMENT ON TABLE qiita.analysis_users IS 'Links analyses to the users they are shared with';

CREATE TABLE qiita.analysis_workflow ( 
	analysis_id          bigint  NOT NULL,
	step                 integer  NOT NULL,
	CONSTRAINT pk_analysis_workflow PRIMARY KEY ( analysis_id ),
	CONSTRAINT fk_analysis_workflow FOREIGN KEY ( analysis_id ) REFERENCES qiita.analysis( analysis_id )    
 );

COMMENT ON TABLE qiita.analysis_workflow IS 'Stores what step in_production analyses are on.';

CREATE TABLE qiita.investigation_study ( 
	investigation_id     bigint  NOT NULL,
	study_id             bigint  NOT NULL,
	CONSTRAINT idx_investigation_study PRIMARY KEY ( investigation_id, study_id ),
	CONSTRAINT fk_investigation_study FOREIGN KEY ( investigation_id ) REFERENCES qiita.investigation( investigation_id )    ,
	CONSTRAINT fk_investigation_study_study FOREIGN KEY ( study_id ) REFERENCES qiita.study( study_id )    
 );

CREATE INDEX idx_investigation_study_investigation ON qiita.investigation_study ( investigation_id );

CREATE INDEX idx_investigation_study_study ON qiita.investigation_study ( study_id );

CREATE TABLE qiita.job ( 
	job_id               bigserial  NOT NULL,
	data_type_id         bigint  NOT NULL,
	job_status_id        bigint  NOT NULL,
	command_id           bigint  NOT NULL,
	options              varchar  ,
	log_id               bigint  ,
	CONSTRAINT pk_job PRIMARY KEY ( job_id ),
	CONSTRAINT fk_job_function FOREIGN KEY ( command_id ) REFERENCES qiita.command( command_id )    ,
	CONSTRAINT fk_job_job_status_id FOREIGN KEY ( job_status_id ) REFERENCES qiita.job_status( job_status_id )    ,
	CONSTRAINT fk_job_data_type FOREIGN KEY ( data_type_id ) REFERENCES qiita.data_type( data_type_id )    ,
	CONSTRAINT fk_job FOREIGN KEY ( log_id ) REFERENCES qiita.logging( logging_id )    
 );

CREATE INDEX idx_job_command ON qiita.job ( command_id );

CREATE INDEX idx_job_status ON qiita.job ( job_status_id );

CREATE INDEX idx_job_type ON qiita.job ( data_type_id );

CREATE INDEX idx_job ON qiita.job ( log_id );

COMMENT ON COLUMN qiita.job.job_id IS 'Unique identifier for job';

COMMENT ON COLUMN qiita.job.data_type_id IS 'What datatype (16s, metabolome, etc) job is run on.';

COMMENT ON COLUMN qiita.job.command_id IS 'The Qiime or other function being run (alpha diversity, etc)';

COMMENT ON COLUMN qiita.job.options IS 'Holds all options set for the job as a json string';

COMMENT ON COLUMN qiita.job.log_id IS 'Reference to error if status is error';

CREATE TABLE qiita.job_results_filepath ( 
	job_id               bigint  NOT NULL,
	filepath_id          bigint  NOT NULL,
	CONSTRAINT idx_job_results_filepath PRIMARY KEY ( job_id, filepath_id ),
	CONSTRAINT fk_job_results_filepath FOREIGN KEY ( job_id ) REFERENCES qiita.job( job_id )    ,
	CONSTRAINT fk_job_results_filepath_0 FOREIGN KEY ( filepath_id ) REFERENCES qiita.filepath( filepath_id )    
 );

CREATE INDEX idx_job_results_filepath_0 ON qiita.job_results_filepath ( job_id );

CREATE INDEX idx_job_results_filepath_1 ON qiita.job_results_filepath ( filepath_id );

COMMENT ON TABLE qiita.job_results_filepath IS 'Holds connection between jobs and the result filepaths';

CREATE TABLE qiita.prep_columns ( 
	prep_template_id     bigint  NOT NULL,
	column_name          varchar  NOT NULL,
	column_type          varchar  NOT NULL,
	CONSTRAINT idx_prep_columns_0 PRIMARY KEY ( prep_template_id, column_name, column_type ),
	CONSTRAINT fk_prep_columns_prep_template FOREIGN KEY ( prep_template_id ) REFERENCES qiita.prep_template( prep_template_id )    
 );

CREATE INDEX idx_prep_columns_1 ON qiita.prep_columns ( prep_template_id );

CREATE TABLE qiita.processed_params_sortmerna ( 
	processed_params_id  bigserial  NOT NULL,
	reference_id         bigint  NOT NULL,
	evalue               float8  NOT NULL,
	max_pos              integer  NOT NULL,
	similarity           float8  NOT NULL,
	coverage             float8  NOT NULL,
	threads              integer  NOT NULL,
	CONSTRAINT pk_processed_params_sortmerna PRIMARY KEY ( processed_params_id ),
	CONSTRAINT fk_processed_params_sortmerna FOREIGN KEY ( reference_id ) REFERENCES qiita.reference( reference_id )    
 );

CREATE INDEX idx_processed_params_sortmerna ON qiita.processed_params_sortmerna ( reference_id );

COMMENT ON TABLE qiita.processed_params_sortmerna IS 'Parameters used for processing data using method sortmerna';

COMMENT ON COLUMN qiita.processed_params_sortmerna.reference_id IS 'What version of reference or type of reference used';

CREATE TABLE qiita.processed_params_uclust ( 
	processed_params_id  bigserial  NOT NULL,
	reference_id         bigint  NOT NULL,
	similarity           float8 DEFAULT 0.97 NOT NULL,
	enable_rev_strand_match bool DEFAULT TRUE NOT NULL,
	suppress_new_clusters bool DEFAULT TRUE NOT NULL,
	CONSTRAINT pk_processed_params_uclust PRIMARY KEY ( processed_params_id ),
	CONSTRAINT fk_processed_params_uclust FOREIGN KEY ( reference_id ) REFERENCES qiita.reference( reference_id )    
 );

CREATE INDEX idx_processed_params_uclust ON qiita.processed_params_uclust ( reference_id );

COMMENT ON TABLE qiita.processed_params_uclust IS 'Parameters used for processing data using method uclust';

COMMENT ON COLUMN qiita.processed_params_uclust.reference_id IS 'What version of reference or type of reference used';

CREATE TABLE qiita.required_sample_info ( 
	sample_id            varchar  NOT NULL,
	study_id             bigint  NOT NULL,
	physical_location    varchar  NOT NULL,
	has_physical_specimen bool  NOT NULL,
	has_extracted_data   bool  NOT NULL,
	sample_type          varchar  NOT NULL,
	required_sample_info_status_id bigint  NOT NULL,
	collection_timestamp timestamp  NOT NULL,
	host_subject_id      varchar  NOT NULL,
	description          varchar  NOT NULL,
	latitude             float8  NOT NULL,
	longitude            float8  NOT NULL,
	CONSTRAINT idx_required_sample_info_1 PRIMARY KEY ( sample_id ),
	CONSTRAINT fk_required_sample_info FOREIGN KEY ( required_sample_info_status_id ) REFERENCES qiita.required_sample_info_status( required_sample_info_status_id )    ,
	CONSTRAINT fk_required_sample_info_study FOREIGN KEY ( study_id ) REFERENCES qiita.study( study_id )    
 );

CREATE INDEX idx_required_sample_info_0 ON qiita.required_sample_info ( required_sample_info_status_id );

CREATE INDEX idx_required_sample_info ON qiita.required_sample_info ( study_id );

COMMENT ON TABLE qiita.required_sample_info IS 'Required info for each sample. One row is one sample.';

COMMENT ON COLUMN qiita.required_sample_info.physical_location IS 'Where the sample itself is stored';

COMMENT ON COLUMN qiita.required_sample_info.has_physical_specimen IS 'Whether we have the full speciment or just DNA';

COMMENT ON COLUMN qiita.required_sample_info.sample_type IS 'Controlled vocabulary of sample types';

COMMENT ON COLUMN qiita.required_sample_info.required_sample_info_status_id IS 'What step of the pipeline the samples are in';

COMMENT ON COLUMN qiita.required_sample_info.latitude IS 'Latitude of the collection site';

COMMENT ON COLUMN qiita.required_sample_info.longitude IS 'Longitude of the collection site';

CREATE TABLE qiita.analysis_job ( 
	analysis_id          bigint  NOT NULL,
	job_id               bigint  NOT NULL,
	CONSTRAINT idx_analysis_jobs PRIMARY KEY ( analysis_id, job_id ),
	CONSTRAINT fk_analysis_job_analysis FOREIGN KEY ( analysis_id ) REFERENCES qiita.analysis( analysis_id ) ON DELETE CASCADE ON UPDATE CASCADE,
	CONSTRAINT fk_analysis_job_job FOREIGN KEY ( job_id ) REFERENCES qiita.job( job_id )    
 );

CREATE INDEX idx_analysis_job ON qiita.analysis_job ( analysis_id );

CREATE INDEX idx_analysis_job_0 ON qiita.analysis_job ( job_id );

COMMENT ON TABLE qiita.analysis_job IS 'Holds information for a one-to-many relation of analysis to the jobs in it';

COMMENT ON COLUMN qiita.analysis_job.analysis_id IS 'Id of the analysis';

COMMENT ON COLUMN qiita.analysis_job.job_id IS 'Id for a job that is part of the analysis';

CREATE TABLE qiita.analysis_sample ( 
	analysis_id          bigint  NOT NULL,
	processed_data_id    bigint  NOT NULL,
	sample_id            varchar  NOT NULL,
	CONSTRAINT fk_analysis_sample_analysis FOREIGN KEY ( analysis_id ) REFERENCES qiita.analysis( analysis_id )    ,
	CONSTRAINT fk_analysis_processed_data FOREIGN KEY ( processed_data_id ) REFERENCES qiita.processed_data( processed_data_id )    ,
	CONSTRAINT fk_analysis_sample FOREIGN KEY ( sample_id ) REFERENCES qiita.required_sample_info( sample_id )    
 );

CREATE INDEX idx_analysis_sample ON qiita.analysis_sample ( analysis_id );

CREATE INDEX idx_analysis_sample_0 ON qiita.analysis_sample ( processed_data_id );

CREATE INDEX idx_analysis_sample_1 ON qiita.analysis_sample ( sample_id );

CREATE TABLE qiita.common_prep_info ( 
	prep_template_id     bigint  NOT NULL,
	sample_id            varchar  NOT NULL,
	center_name          varchar  ,
	center_project_name  varchar  ,
	emp_status_id        bigint  NOT NULL,
	CONSTRAINT idx_common_prep_info PRIMARY KEY ( prep_template_id, sample_id ),
	CONSTRAINT fk_required_prep_info_emp_status FOREIGN KEY ( emp_status_id ) REFERENCES qiita.emp_status( emp_status_id )    ,
	CONSTRAINT fk_common_prep_info FOREIGN KEY ( sample_id ) REFERENCES qiita.required_sample_info( sample_id )    ,
	CONSTRAINT fk_prep_template FOREIGN KEY ( prep_template_id ) REFERENCES qiita.prep_template( prep_template_id )    
 );

CREATE INDEX idx_required_prep_info_0 ON qiita.common_prep_info ( emp_status_id );

CREATE INDEX idx_required_prep_info_2 ON qiita.common_prep_info ( sample_id );

CREATE INDEX idx_common_prep_info_0 ON qiita.common_prep_info ( sample_id );

CREATE INDEX idx_common_prep_info_1 ON qiita.common_prep_info ( prep_template_id );

COMMENT ON COLUMN qiita.common_prep_info.prep_template_id IS 'The prep template identifier';

