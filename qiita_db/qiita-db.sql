CREATE SCHEMA qiita;

CREATE TABLE qiita.analysis_status ( 
	analysis_status_id   bigserial  NOT NULL,
	status               varchar  NOT NULL,
	CONSTRAINT pk_analysis_status PRIMARY KEY ( analysis_status_id )
 );

CREATE TABLE qiita.command ( 
	command_id           bigserial  NOT NULL,
	name                 varchar  NOT NULL,
	command              varchar  NOT NULL,
	CONSTRAINT pk_function PRIMARY KEY ( command_id )
 );

COMMENT ON TABLE qiita.command IS 'Available commands for jobs';

COMMENT ON COLUMN qiita.command.command_id IS 'Unique identifier for function';

COMMENT ON COLUMN qiita.command.command IS 'what command to call to run this function';

CREATE TABLE qiita.controlled_vocabularies ( 
	controlled_vocab_id  bigserial  NOT NULL,
	vocab_name           varchar(100)  NOT NULL,
	CONSTRAINT pk_controlled_vocabularies PRIMARY KEY ( controlled_vocab_id )
 );

CREATE TABLE qiita.data_type ( 
	data_type_id         bigserial  NOT NULL,
	data_type            varchar  NOT NULL,
	CONSTRAINT pk_data_type PRIMARY KEY ( data_type_id )
 );

COMMENT ON COLUMN qiita.data_type.data_type IS 'what datatype (16s, metabolome, etc) job is run on.';

CREATE TABLE qiita.filetype ( 
	filetype_id          bigserial  NOT NULL,
	type                 varchar  NOT NULL,
	CONSTRAINT pk_filetype PRIMARY KEY ( filetype_id )
 );

CREATE TABLE qiita.investigation ( 
	investigation_id     bigserial  NOT NULL,
	description          bigserial  NOT NULL,
	contact_person_id    integer  ,
	CONSTRAINT pk_investigation PRIMARY KEY ( investigation_id )
 );

COMMENT ON TABLE qiita.investigation IS 'Overarching investigation information
One investigation can have multiple studies under it';

COMMENT ON COLUMN qiita.investigation.description IS 'describes the overarching goal of the investigation';

CREATE TABLE qiita.job_status ( 
	job_status_id        bigserial  NOT NULL,
	status               varchar  NOT NULL,
	CONSTRAINT pk_job_status PRIMARY KEY ( job_status_id )
 );

CREATE TABLE qiita.mixs_field_description ( 
	column_name          varchar(100)  NOT NULL,
	data_type            varchar(100)  ,
	desc_or_value        varchar(100)  ,
	definition           varchar(100)  ,
	min_length           integer  ,
	active               integer  ,
	CONSTRAINT pk_column_dictionary UNIQUE ( column_name ) ,
	CONSTRAINT pk_column_dictionary_0 PRIMARY KEY ( column_name )
 );

CREATE TABLE qiita.ontology ( 
	ontology_id          bigserial  NOT NULL,
	shortname            varchar(100)  NOT NULL,
	fully_loaded         bool  NOT NULL,
	fullname             varchar(255)  ,
	query_url            varchar(255)  ,
	source_url           varchar(255)  ,
	definition           text  ,
	load_date            date  NOT NULL,
	version              varchar(128)  ,
	CONSTRAINT pk_ontology PRIMARY KEY ( ontology_id )
 );

CREATE TABLE qiita.picking_params ( 
	picking_params_id    bigserial  NOT NULL,
	similarity           float8  NOT NULL,
	picking_type         float8  NOT NULL,
	CONSTRAINT pk_picking_params PRIMARY KEY ( picking_params_id )
 );

CREATE TABLE qiita.preprocessed_sequence_454_params ( 
	preprocessed_params_id bigserial  NOT NULL,
	trim_length          integer  NOT NULL,
	CONSTRAINT pk_preprocessed_sequence_454_params PRIMARY KEY ( preprocessed_params_id )
 );

COMMENT ON TABLE qiita.preprocessed_sequence_454_params IS 'Parameters used for processing sequence data.';

CREATE TABLE qiita.preprocessed_sequence_illumina_params ( 
	preprocessed_params_id bigserial  NOT NULL,
	trim_length          integer  NOT NULL,
	max_bad_run_length   integer DEFAULT 3 NOT NULL,
	min_per_read_length_fraction real DEFAULT 0.75 NOT NULL,
	sequence_max_n       integer DEFAULT 0 NOT NULL,
	CONSTRAINT pk_preprocessed_sequence_illumina_params PRIMARY KEY ( preprocessed_params_id )
 );

COMMENT ON TABLE qiita.preprocessed_sequence_illumina_params IS 'Parameters used for processing illumina sequence data.';

CREATE TABLE qiita.preprocessed_spectra_params ( 
	preprocessed_params_id bigserial  NOT NULL,
	col                  varchar  ,
	CONSTRAINT pk_preprocessed_spectra_params PRIMARY KEY ( preprocessed_params_id )
 );

COMMENT ON TABLE qiita.preprocessed_spectra_params IS 'Parameters used for processing spectra data.';

CREATE TABLE qiita.processed_params_uclust ( 
	processed_params_id  bigserial  NOT NULL,
	col                  bigserial  ,
	CONSTRAINT pk_processed_params_uclust PRIMARY KEY ( processed_params_id )
 );

COMMENT ON TABLE qiita.processed_params_uclust IS 'Parameters used for processing data using method x';

CREATE TABLE qiita.raw_data ( 
	raw_data_id          bigserial  NOT NULL,
	filetype_id          bigint  NOT NULL,
	filepath             varchar  NOT NULL,
	submit_to_insdc      bool  NOT NULL,
	CONSTRAINT pk_raw_data UNIQUE ( raw_data_id ) ,
	CONSTRAINT fk_raw_data_filetype FOREIGN KEY ( filetype_id ) REFERENCES qiita.filetype( filetype_id )    
 );

CREATE INDEX idx_raw_data ON qiita.raw_data ( filetype_id );

COMMENT ON COLUMN qiita.raw_data.filepath IS 'filepath to raw data hdf5';

CREATE TABLE qiita.raw_data_prep_columns ( 
	raw_data_id          bigint  NOT NULL,
	column_name          varchar  NOT NULL,
	column_type          varchar  NOT NULL,
	CONSTRAINT idx_raw_data_prep_columns PRIMARY KEY ( raw_data_id, column_name, column_type ),
	CONSTRAINT fk_prep_columns_raw_data FOREIGN KEY ( raw_data_id ) REFERENCES qiita.raw_data( raw_data_id )    
 );

CREATE INDEX idx_prep_columns ON qiita.raw_data_prep_columns ( raw_data_id );

COMMENT ON TABLE qiita.raw_data_prep_columns IS 'Holds the columns available for a given raw data prep';

CREATE TABLE qiita.relationship_type ( 
	relationship_type_id bigserial  NOT NULL,
	relationship_type    varchar(128)  ,
	CONSTRAINT pk_relationship_type PRIMARY KEY ( relationship_type_id )
 );

CREATE TABLE qiita.required_prep_info ( 
	raw_data_id          bigserial  NOT NULL,
	center_name          varchar  NOT NULL,
	center_project_name  varchar  NOT NULL,
	ebi_submission_accession varchar  ,
	ebi_study_accession  varchar  ,
	emp_status_id        integer  ,
	investigation_type   varchar  NOT NULL,
	CONSTRAINT fk_required_prep_info_raw_data FOREIGN KEY ( raw_data_id ) REFERENCES qiita.raw_data( raw_data_id )    
 );

CREATE INDEX idx_required_prep_info ON qiita.required_prep_info ( raw_data_id );

CREATE TABLE qiita.term ( 
	term_id              bigserial  NOT NULL,
	ontology_id          bigint  NOT NULL,
	term_name            varchar(255)  NOT NULL,
	identifier           varchar(255)  ,
	definition           text  ,
	namespace            varchar(255)  ,
	is_obsolete          bool DEFAULT 'false' NOT NULL,
	is_root_term         bool  NOT NULL,
	is_leaf              bool  NOT NULL,
	CONSTRAINT pk_term PRIMARY KEY ( term_id ),
	CONSTRAINT fk_term_ontology FOREIGN KEY ( ontology_id ) REFERENCES qiita.ontology( ontology_id )    
 );

CREATE INDEX idx_term ON qiita.term ( ontology_id );

CREATE TABLE qiita.term_path ( 
	term_path_id         bigserial  NOT NULL,
	subject_term_id      bigint  NOT NULL,
	predicate_term_id    bigint  NOT NULL,
	object_term_id       bigint  NOT NULL,
	ontology_id          bigint  NOT NULL,
	relationship_type_id integer  NOT NULL,
	distance             integer  ,
	CONSTRAINT pk_term_path PRIMARY KEY ( term_path_id ),
	CONSTRAINT fk_term_path_ontology FOREIGN KEY ( ontology_id ) REFERENCES qiita.ontology( ontology_id )    ,
	CONSTRAINT fk_term_path_relationship_type FOREIGN KEY ( relationship_type_id ) REFERENCES qiita.relationship_type( relationship_type_id )    
 );

CREATE INDEX idx_term_path ON qiita.term_path ( ontology_id );

CREATE INDEX idx_term_path_0 ON qiita.term_path ( relationship_type_id );

CREATE TABLE qiita.term_relationship ( 
	term_relationship_id bigserial  NOT NULL,
	subject_term_id      bigint  NOT NULL,
	predicate_term_id    bigint  NOT NULL,
	object_term_id       bigint  NOT NULL,
	ontology_id          bigint  NOT NULL,
	CONSTRAINT pk_term_relationship PRIMARY KEY ( term_relationship_id ),
	CONSTRAINT fk_term_relationship_subj_term FOREIGN KEY ( subject_term_id ) REFERENCES qiita.term( term_id )    ,
	CONSTRAINT fk_term_relationship_pred_term FOREIGN KEY ( predicate_term_id ) REFERENCES qiita.term( term_id )    ,
	CONSTRAINT fk_term_relationship_obj_term FOREIGN KEY ( object_term_id ) REFERENCES qiita.term( term_id )    ,
	CONSTRAINT fk_term_relationship_ontology FOREIGN KEY ( ontology_id ) REFERENCES qiita.ontology( ontology_id )    
 );

CREATE INDEX idx_term_relationship ON qiita.term_relationship ( subject_term_id );

CREATE INDEX idx_term_relationship ON qiita.term_relationship ( predicate_term_id );

CREATE INDEX idx_term_relationship ON qiita.term_relationship ( object_term_id );

CREATE INDEX idx_term_relationship ON qiita.term_relationship ( ontology_id );

CREATE TABLE qiita.term_synonym ( 
	synonym_id           bigserial  NOT NULL,
	term_id              bigint  NOT NULL,
	synonym_value        varchar(100)  NOT NULL,
	synonym_type_id      bigint  NOT NULL,
	CONSTRAINT pk_term_synonym PRIMARY KEY ( synonym_id ),
	CONSTRAINT fk_term_synonym_term FOREIGN KEY ( term_id ) REFERENCES qiita.term( term_id )    ,
	CONSTRAINT fk_term_synonym_type_term FOREIGN KEY ( synonym_id ) REFERENCES qiita.term( term_id )    
 );

CREATE INDEX idx_term_synonym ON qiita.term_synonym ( term_id );

CREATE TABLE qiita.user_level ( 
	id_user_level        smallint  NOT NULL,
	name                 varchar  NOT NULL,
	description          text  NOT NULL,
	CONSTRAINT pk_user_level PRIMARY KEY ( id_user_level )
 );

COMMENT ON TABLE qiita.user_level IS 'Holds restricted text for user levels';

COMMENT ON COLUMN qiita.user_level.name IS 'One of the user levels (admin, user, guest, etc)';

CREATE TABLE qiita.annotation ( 
	annotation_id        bigserial  NOT NULL,
	term_id              bigint  NOT NULL,
	annotation_name      varchar(255)  NOT NULL,
	annotation_num_value float8  ,
	annotation_str_value varchar(255)  ,
	CONSTRAINT pk_annotation PRIMARY KEY ( annotation_id ),
	CONSTRAINT fk_annotation_term FOREIGN KEY ( term_id ) REFERENCES qiita.term( term_id )    
 );

CREATE INDEX idx_annotation ON qiita.annotation ( term_id );

CREATE TABLE qiita.column_controlled_vocabularies ( 
	controlled_vocab_id  bigserial  NOT NULL,
	column_name          varchar(100)  NOT NULL,
	CONSTRAINT idx_column_controlled_vocabularies PRIMARY KEY ( controlled_vocab_id, column_name ),
	CONSTRAINT fk_column_controlled_vocabularies FOREIGN KEY ( column_name ) REFERENCES qiita.mixs_field_description( column_name )    ,
	CONSTRAINT fk_column_controlled_vocab2 FOREIGN KEY ( controlled_vocab_id ) REFERENCES qiita.controlled_vocabularies( controlled_vocab_id )    
 );

CREATE INDEX idx_column_controlled_vocabularies_0 ON qiita.column_controlled_vocabularies ( column_name );

CREATE INDEX idx_column_controlled_vocabularies_1 ON qiita.column_controlled_vocabularies ( controlled_vocab_id );

CREATE TABLE qiita.column_ontology ( 
	column_name          varchar(200)  NOT NULL,
	ontology_short_name  varchar(50)  NOT NULL,
	bioportal_id         integer  NOT NULL,
	ontology_branch_id   integer  NOT NULL,
	CONSTRAINT idx_column_ontology PRIMARY KEY ( column_name, ontology_short_name ),
	CONSTRAINT fk_column_ontology FOREIGN KEY ( column_name ) REFERENCES qiita.mixs_field_description( column_name )    
 );

CREATE INDEX idx_column_ontology_0 ON qiita.column_ontology ( column_name );

CREATE TABLE qiita.controlled_vocab_values ( 
	vocab_value_id       bigserial  NOT NULL,
	controlled_vocab_id  bigint  NOT NULL,
	term                 varchar  NOT NULL,
	order_by             varchar  NOT NULL,
	default_item         varchar  ,
	CONSTRAINT pk_controlled_vocab_values PRIMARY KEY ( vocab_value_id ),
	CONSTRAINT fk_controlled_vocab_values FOREIGN KEY ( controlled_vocab_id ) REFERENCES qiita.controlled_vocabularies( controlled_vocab_id ) ON DELETE CASCADE ON UPDATE CASCADE
 );

CREATE INDEX idx_controlled_vocab_values ON qiita.controlled_vocab_values ( controlled_vocab_id );

CREATE TABLE qiita.dbxref ( 
	dbxref_id            bigserial  NOT NULL,
	term_id              bigint  NOT NULL,
	dbname               varchar(100)  NOT NULL,
	accession            varchar(255)  NOT NULL,
	description          text  NOT NULL,
	xref_type            text  NOT NULL,
	CONSTRAINT pk_dbxref PRIMARY KEY ( dbxref_id ),
	CONSTRAINT fk_dbxref_term FOREIGN KEY ( term_id ) REFERENCES qiita.term( term_id )    
 );

CREATE INDEX idx_dbxref ON qiita.dbxref ( term_id );

CREATE TABLE qiita.job ( 
	job_id               bigserial  NOT NULL,
	data_type_id         bigint  NOT NULL,
	job_status_id        bigint  NOT NULL,
	command_id           bigint  NOT NULL,
	options              varchar  NOT NULL,
	results              varchar  ,
	error_msg_text       varchar  ,
	CONSTRAINT pk_job PRIMARY KEY ( job_id ),
	CONSTRAINT fk_job_function FOREIGN KEY ( command_id ) REFERENCES qiita.command( command_id )    ,
	CONSTRAINT fk_job_job_status_id FOREIGN KEY ( job_status_id ) REFERENCES qiita.job_status( job_status_id )    ,
	CONSTRAINT fk_job_data_type FOREIGN KEY ( data_type_id ) REFERENCES qiita.data_type( data_type_id )    
 );

CREATE INDEX idx_job ON qiita.job ( command_id );

CREATE INDEX idx_job ON qiita.job ( job_status_id );

CREATE INDEX idx_job ON qiita.job ( data_type_id );

COMMENT ON COLUMN qiita.job.job_id IS 'unique identifier for job';

COMMENT ON COLUMN qiita.job.data_type_id IS 'what datatype (16s, metabolome, etc) job is run on.';

COMMENT ON COLUMN qiita.job.command_id IS 'The Qiita or other function being run (alpha diversity, etc)';

COMMENT ON COLUMN qiita.job.options IS 'Holds all options set for the job as a json string';

COMMENT ON COLUMN qiita.job.results IS 'list of filepaths to result files for job';

COMMENT ON COLUMN qiita.job.error_msg_text IS 'Holds error message if generated';

CREATE TABLE qiita.preprocessed_data ( 
	preprocessed_data_id bigserial  NOT NULL,
	raw_data_id          integer  ,
	filepath             varchar  NOT NULL,
	preprocessed_params_id bigint  NOT NULL,
	CONSTRAINT pk_preprocessed_data PRIMARY KEY ( preprocessed_data_id ),
	CONSTRAINT fk_preprocessed_data_raw_data FOREIGN KEY ( raw_data_id ) REFERENCES qiita.raw_data( raw_data_id )    
 );

CREATE INDEX idx_preprocessed_data ON qiita.preprocessed_data ( raw_data_id );

CREATE TABLE qiita.processed_data ( 
	processed_data_id    bigserial  NOT NULL,
	preprocessed_data_id bigint  NOT NULL,
	processed_data_filepath varchar  NOT NULL,
	processed_params_id  varchar  NOT NULL,
	processed_date       date  NOT NULL,
	CONSTRAINT pk_processed_data PRIMARY KEY ( processed_data_id ),
	CONSTRAINT fk_processed_data FOREIGN KEY ( preprocessed_data_id ) REFERENCES qiita.preprocessed_data( preprocessed_data_id )    
 );

COMMENT ON COLUMN qiita.processed_data.processed_params_id IS 'link to a table with the parameters used to generate processed data';

CREATE TABLE qiita.qiita_user ( 
	email                varchar  NOT NULL,
	id_user_level        smallint  NOT NULL,
	password             varchar  NOT NULL,
	name                 varchar  ,
	affilliation         varchar  ,
	address              varchar  ,
	phone                varchar  ,
	salt                 varchar  NOT NULL,
	CONSTRAINT pk_user PRIMARY KEY ( email ),
	CONSTRAINT fk_user_user_level FOREIGN KEY ( id_user_level ) REFERENCES qiita.user_level( id_user_level )   ON UPDATE RESTRICT
 );

CREATE INDEX idx_user ON qiita.qiita_user ( id_user_level );

COMMENT ON TABLE qiita.qiita_user IS 'Holds all user information';

COMMENT ON COLUMN qiita.qiita_user.id_user_level IS 'user level';

CREATE TABLE qiita.study ( 
	study_id             bigserial  NOT NULL,
	email                varchar  NOT NULL,
	status               varchar(10)  NOT NULL,
	emp_person           varchar(40)  ,
	first_contact        varchar  NOT NULL,
	funding              varchar  ,
	timeseries_type_id   bigint  NOT NULL,
	lab_person_id        bigint  ,
	metadata_complete    bool  NOT NULL,
	mixs_compliant       bool  NOT NULL,
	most_recent_contact  varchar  ,
	number_samples_collected integer  NOT NULL,
	number_samples_promised integer  NOT NULL,
	portal_type          varchar  NOT NULL,
	principal_investigator_id bigint  NOT NULL,
	reprocess            bool  NOT NULL,
	spatial_series       bool  ,
	study_title          varchar  NOT NULL,
	study_alias          varchar  NOT NULL,
	study_description    text  NOT NULL,
	study_abstract       text  NOT NULL,
	vamps_id             varchar  ,
	CONSTRAINT pk_study PRIMARY KEY ( study_id ),
	CONSTRAINT fk_study_user FOREIGN KEY ( email ) REFERENCES qiita.qiita_user( email )    
 );

CREATE INDEX idx_study ON qiita.study ( email );

COMMENT ON COLUMN qiita.study.study_id IS 'uique name for study';

COMMENT ON COLUMN qiita.study.email IS 'email of study owner';

COMMENT ON COLUMN qiita.study.timeseries_type_id IS 'what type of timeseries this study is (or is not)
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

COMMENT ON TABLE qiita.study_pmid IS 'links a study to all PMIDs for papers created from study';

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

CREATE INDEX idx_study_mapping_columns ON qiita.study_sample_columns ( study_id );

CREATE TABLE qiita.study_users ( 
	study_id             bigserial  NOT NULL,
	email                varchar  NOT NULL,
	CONSTRAINT idx_study_users PRIMARY KEY ( study_id, email ),
	CONSTRAINT fk_study_users_study FOREIGN KEY ( study_id ) REFERENCES qiita.study( study_id )    ,
	CONSTRAINT fk_study_users_user FOREIGN KEY ( email ) REFERENCES qiita.qiita_user( email )    
 );

CREATE INDEX idx_study_users_0 ON qiita.study_users ( study_id );

CREATE INDEX idx_study_users_1 ON qiita.study_users ( email );

COMMENT ON TABLE qiita.study_users IS 'links shared studies to users they are shared with';

CREATE TABLE qiita.analysis ( 
	analysis_id          bigserial  NOT NULL,
	email                varchar  NOT NULL,
	name                 varchar  NOT NULL,
	description          varchar  NOT NULL,
	analysis_status_id   bigint  NOT NULL,
	biom_table_filepath  varchar  NOT NULL,
	pmid                 integer  ,
	CONSTRAINT pk_analysis PRIMARY KEY ( analysis_id ),
	CONSTRAINT fk_analysis_user FOREIGN KEY ( email ) REFERENCES qiita.qiita_user( email )    ,
	CONSTRAINT fk_analysis_analysis_status FOREIGN KEY ( analysis_status_id ) REFERENCES qiita.analysis_status( analysis_status_id )    
 );

CREATE INDEX idx_analysis ON qiita.analysis ( email );

CREATE INDEX idx_analysis ON qiita.analysis ( analysis_status_id );

COMMENT ON TABLE qiita.analysis IS 'holds analysis information';

COMMENT ON COLUMN qiita.analysis.analysis_id IS 'unique identifier for analysis';

COMMENT ON COLUMN qiita.analysis.email IS 'email for user who owns the analysis';

COMMENT ON COLUMN qiita.analysis.name IS 'name of the analysis';

COMMENT ON COLUMN qiita.analysis.pmid IS 'pmid of paper from the analysis';

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

COMMENT ON COLUMN qiita.analysis_job.analysis_id IS 'id of the analysis';

COMMENT ON COLUMN qiita.analysis_job.job_id IS 'id for a job that is part of the analysis';

CREATE TABLE qiita.analysis_sample ( 
	analysis_id          bigint  NOT NULL,
	processed_data_id    bigint  NOT NULL,
	sample_id            bigint  NOT NULL,
	CONSTRAINT fk_analysis_sample_analysis FOREIGN KEY ( analysis_id ) REFERENCES qiita.analysis( analysis_id )    ,
	CONSTRAINT fk_analysis_sample FOREIGN KEY ( processed_data_id ) REFERENCES qiita.processed_data( processed_data_id )    
 );

CREATE INDEX idx_analysis_sample ON qiita.analysis_sample ( analysis_id );

CREATE INDEX idx_analysis_sample_0 ON qiita.analysis_sample ( processed_data_id );

CREATE TABLE qiita.analysis_users ( 
	analysis_id          bigint  NOT NULL,
	email                varchar  NOT NULL,
	CONSTRAINT idx_analysis_users PRIMARY KEY ( analysis_id, email ),
	CONSTRAINT fk_analysis_users_analysis FOREIGN KEY ( analysis_id ) REFERENCES qiita.analysis( analysis_id ) ON DELETE CASCADE ON UPDATE CASCADE,
	CONSTRAINT fk_analysis_users_user FOREIGN KEY ( email ) REFERENCES qiita.qiita_user( email ) ON DELETE CASCADE ON UPDATE CASCADE
 );

CREATE INDEX idx_analysis_users ON qiita.analysis_users ( analysis_id );

CREATE INDEX idx_analysis_users ON qiita.analysis_users ( email );

COMMENT ON TABLE qiita.analysis_users IS 'links analyses to the users they are shared with';

CREATE TABLE qiita.investigation_study ( 
	investigation_id     bigint  NOT NULL,
	study_id             bigint  NOT NULL,
	CONSTRAINT idx_investigation_study PRIMARY KEY ( investigation_id, study_id ),
	CONSTRAINT fk_investigation_study FOREIGN KEY ( investigation_id ) REFERENCES qiita.investigation( investigation_id )    ,
	CONSTRAINT fk_investigation_study_study FOREIGN KEY ( study_id ) REFERENCES qiita.study( study_id )    
 );

CREATE INDEX idx_investigation_study ON qiita.investigation_study ( investigation_id );

CREATE INDEX idx_investigation_study ON qiita.investigation_study ( study_id );

CREATE TABLE qiita.required_sample_info ( 
	study_id             bigint  NOT NULL,
	sample_id            bigint  NOT NULL,
	physical_location    varchar  NOT NULL,
	has_physical_specimen bool  NOT NULL,
	has_extracted_data   bool  NOT NULL,
	sample_type          varchar  NOT NULL,
	CONSTRAINT idx_common_sample_information PRIMARY KEY ( study_id, sample_id ),
	CONSTRAINT fk_required_sample_info_study FOREIGN KEY ( study_id ) REFERENCES qiita.study( study_id )    
 );

CREATE INDEX idx_required_sample_info ON qiita.required_sample_info ( study_id );

COMMENT ON COLUMN qiita.required_sample_info.sample_type IS 'controlled vocabulary of sample types';

