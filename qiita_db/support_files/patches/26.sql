CREATE TABLE qiita.antibiotic ( 
	antibiotic_id        bigserial  NOT NULL,
	name                 varchar  NOT NULL,
	description          varchar  NOT NULL,
	CONSTRAINT pk_antibiotic PRIMARY KEY ( antibiotic_id )
 ) ;

CREATE TABLE qiita.conditions ( 
	conditions_id        bigserial  NOT NULL,
	name                 varchar  NOT NULL,
	temperature          real  NOT NULL,
	atmoshpere           varchar  NOT NULL,
	agitation            bool  NOT NULL,
	CONSTRAINT pk_conditions PRIMARY KEY ( conditions_id )
 ) ;

CREATE TABLE qiita.ingredient ( 
	ingredient_id        bigserial  NOT NULL,
	name                 varchar  NOT NULL,
	lot_number           varchar  NOT NULL,
	CONSTRAINT pk_ingredients PRIMARY KEY ( ingredient_id )
 ) ;

CREATE TABLE qiita.media ( 
	media_id             bigint  NOT NULL,
	name                 varchar  NOT NULL,
	protocol             varchar  NOT NULL,
	type                 varchar  NOT NULL,
	CONSTRAINT pk_media PRIMARY KEY ( media_id )
 ) ;

CREATE TABLE qiita.media_ingredients ( 
	media_id             bigint  NOT NULL,
	ingredient_id        bigint  NOT NULL,
	quantity             varchar  NOT NULL,
	CONSTRAINT idx_media_ingredients PRIMARY KEY ( media_id, ingredient_id )
 ) ;

CREATE INDEX idx_media_ingredients_0 ON qiita.media_ingredients ( media_id ) ;

CREATE INDEX idx_media_ingredients_1 ON qiita.media_ingredients ( ingredient_id ) ;

CREATE TABLE qiita.morphology ( 
	morphology_id        bigserial  NOT NULL,
	form                 varchar  NOT NULL,
	elevation            varchar  NOT NULL,
	margin               varchar  NOT NULL,
	surface              varchar  NOT NULL,
	opacity              varchar  ,
	pigmentation         varchar  NOT NULL,
	CONSTRAINT pk_morphology PRIMARY KEY ( morphology_id )
 ) ;

CREATE TABLE qiita.software ( 
	software_id          bigserial  NOT NULL,
	name                 varchar  NOT NULL,
	version              varchar  NOT NULL,
	parameters_table     varchar  NOT NULL,
	type                 varchar  NOT NULL,
	CONSTRAINT pk_software PRIMARY KEY ( software_id )
 ) ;

CREATE TABLE qiita.storage ( 
	storage_id           bigserial  NOT NULL,
	name                 varchar  NOT NULL,
	media_id             bigint  NOT NULL,
	additives            varchar  ,
	temperature          float8  ,
	CONSTRAINT pk_storage PRIMARY KEY ( storage_id )
 ) ;

CREATE INDEX idx_storage ON qiita.storage ( media_id ) ;

CREATE TABLE qiita.annotation ( 
	annotation_id        bigserial  NOT NULL,
	cds_count            integer  NOT NULL,
	rrna_count           integer  NOT NULL,
	trna_count           integer  NOT NULL,
	tmrna_count          integer  NOT NULL,
	ncrna_count          integer  NOT NULL,
	cripr_count          integer  NOT NULL,
	cazymes_count        integer  NOT NULL,
	peptidases_count     integer  NOT NULL,
	annotator_id         bigint  NOT NULL,
	annotator_params_id  bigint  NOT NULL,
	CONSTRAINT pk_annotation PRIMARY KEY ( annotation_id )
 ) ;

CREATE INDEX idx_annotation ON qiita.annotation ( annotator_id ) ;

CREATE TABLE qiita.annotation_filepath ( 
	annotation_id        bigint  NOT NULL,
	filepath_id          bigint  NOT NULL,
	CONSTRAINT idx_annotation_filepath PRIMARY KEY ( annotation_id, filepath_id )
 ) ;

CREATE INDEX idx_annotation_filepath_0 ON qiita.annotation_filepath ( annotation_id ) ;

CREATE INDEX idx_annotation_filepath_1 ON qiita.annotation_filepath ( filepath_id ) ;

CREATE TABLE qiita.assembly ( 
	assembly_id          bigserial  NOT NULL,
	n50                  integer  NOT NULL,
	n90                  integer  NOT NULL,
	num_contigs          integer  NOT NULL,
	acum_length          integer  NOT NULL,
	max_contig_length    integer  NOT NULL,
	min_contig_length    integer  NOT NULL,
	avg_contig_length    real  NOT NULL,
	gc_content           integer  NOT NULL,
	assembler_id         bigint  NOT NULL,
	assembler_parameters_id bigint  NOT NULL,
	CONSTRAINT pk_assembly PRIMARY KEY ( assembly_id )
 ) ;

CREATE INDEX idx_assembly ON qiita.assembly ( assembler_id ) ;

CREATE TABLE qiita.assembly_annotation ( 
	assembly_id          bigint  NOT NULL,
	annotation_id        bigint  NOT NULL,
	CONSTRAINT idx_assembly_annotation PRIMARY KEY ( assembly_id, annotation_id )
 ) ;

CREATE INDEX idx_assembly_annotation_0 ON qiita.assembly_annotation ( assembly_id ) ;

CREATE INDEX idx_assembly_annotation_1 ON qiita.assembly_annotation ( annotation_id ) ;

CREATE TABLE qiita.assembly_filepath ( 
	assembly_id          bigint  NOT NULL,
	filepath_id          bigint  NOT NULL,
	CONSTRAINT idx_assembly_filepath_0 PRIMARY KEY ( assembly_id, filepath_id )
 ) ;

CREATE INDEX idx_assembly_filepath_1 ON qiita.assembly_filepath ( assembly_id ) ;

CREATE INDEX idx_assembly_filepath_2 ON qiita.assembly_filepath ( filepath_id ) ;

CREATE TABLE qiita.assembly_preprocessed_data ( 
	preprocessed_data_id bigint  NOT NULL,
	assembly_id          bigint  NOT NULL,
	CONSTRAINT idx_assembly_preprocessed_data PRIMARY KEY ( preprocessed_data_id, assembly_id )
 ) ;

CREATE INDEX idx_assembly_preprocessed_data_0 ON qiita.assembly_preprocessed_data ( preprocessed_data_id ) ;

CREATE INDEX idx_assembly_preprocessed_data_1 ON qiita.assembly_preprocessed_data ( assembly_id ) ;

CREATE TABLE qiita.isolate ( 
	isolate_id           bigserial  NOT NULL,
	alias                varchar  NOT NULL,
	parent_id            bigint  ,
	sample_id            varchar  NOT NULL,
	isolation_date       timestamp  NOT NULL,
	CONSTRAINT pk_isolate PRIMARY KEY ( isolate_id )
 ) ;

CREATE INDEX idx_isolate ON qiita.isolate ( sample_id ) ;

CREATE INDEX idx_isolate_0 ON qiita.isolate ( parent_id ) ;

CREATE TABLE qiita.isolate_antibiotic_resistance ( 
	isolate_id           bigint  NOT NULL,
	antibiotic_id        bigint  NOT NULL,
	mic                  real  NOT NULL,
	description          varchar  NOT NULL,
	CONSTRAINT idx_table_0 PRIMARY KEY ( isolate_id, antibiotic_id )
 ) ;

CREATE INDEX idx_isolate_antibiotic_resistance ON qiita.isolate_antibiotic_resistance ( isolate_id ) ;

CREATE INDEX idx_isolate_antibiotic_resistance_0 ON qiita.isolate_antibiotic_resistance ( antibiotic_id ) ;

COMMENT ON COLUMN qiita.isolate_antibiotic_resistance.mic IS 'Minimum inhibitory concentration';

COMMENT ON COLUMN qiita.isolate_antibiotic_resistance.description IS 'Description of the experiment conducted to perform antibiotic resistance testing';

CREATE TABLE qiita.isolate_antibiotic_sensitivity ( 
	isolate_id           bigint  NOT NULL,
	antibiotic_id        bigint  NOT NULL,
	mic                  real  NOT NULL,
	description          varchar  NOT NULL,
	CONSTRAINT idx_isolate_antibiotic_sensitivity PRIMARY KEY ( isolate_id, antibiotic_id )
 ) ;

CREATE INDEX idx_isolate_antibiotic_sensitivity_0 ON qiita.isolate_antibiotic_sensitivity ( antibiotic_id ) ;

CREATE INDEX idx_isolate_antibiotic_sensitivity_1 ON qiita.isolate_antibiotic_sensitivity ( isolate_id ) ;

COMMENT ON COLUMN qiita.isolate_antibiotic_sensitivity.mic IS 'minimum inhibitory concentration';

COMMENT ON COLUMN qiita.isolate_antibiotic_sensitivity.description IS 'Description of the experiment conducted to perform antibiotic sensitivity testing';

CREATE TABLE qiita.isolate_growth ( 
	isolate_growth_id    bigserial  NOT NULL,
	isolate_id           bigint  NOT NULL,
	media_id             bigint  NOT NULL,
	conditions_id        bigint  NOT NULL,
	has_grown            bool  NOT NULL,
	time_to_grow         varchar  NOT NULL,
	max_od               real  ,
	comments             varchar  ,
	morpholgy_id         bigint  ,
	CONSTRAINT pk_isolate_growth PRIMARY KEY ( isolate_growth_id )
 ) ;

CREATE INDEX idx_isolate_growth ON qiita.isolate_growth ( morpholgy_id ) ;

CREATE TABLE qiita.isolate_growth_filepath ( 
	isolate_growth_id    bigint  NOT NULL,
	filepath_id          bigint  NOT NULL,
	CONSTRAINT idx_isolate_growth_filepath PRIMARY KEY ( isolate_growth_id, filepath_id )
 ) ;

CREATE INDEX idx_isolate_growth_filepath_0 ON qiita.isolate_growth_filepath ( isolate_growth_id ) ;

CREATE INDEX idx_isolate_growth_filepath_1 ON qiita.isolate_growth_filepath ( filepath_id ) ;

CREATE TABLE qiita.isolate_storage ( 
	isolate_id           bigint  NOT NULL,
	storage_id           bigserial  NOT NULL,
	issues               varchar  ,
	CONSTRAINT idx_isolate_storage PRIMARY KEY ( isolate_id, storage_id )
 ) ;

CREATE INDEX idx_isolate_storage_0 ON qiita.isolate_storage ( storage_id ) ;

CREATE INDEX idx_isolate_storage_1 ON qiita.isolate_storage ( isolate_id ) ;

CREATE TABLE qiita.strain ( 
	strain_id            bigserial  NOT NULL,
	official_name        varchar  ,
	alias                varchar  NOT NULL,
	representative_assembly_id bigint  NOT NULL,
	representative_isolate_id bigint  NOT NULL,
	taxonomy             varchar  NOT NULL,
	CONSTRAINT pk_strain PRIMARY KEY ( strain_id ),
	CONSTRAINT idx_strain UNIQUE ( representative_assembly_id ) ,
	CONSTRAINT idx_strain_0 UNIQUE ( representative_isolate_id ) ,
	CONSTRAINT idx_strain_1 UNIQUE ( taxonomy ) 
 ) ;

ALTER TABLE qiita.media_ingredients ADD CONSTRAINT fk_media_ingredients_media FOREIGN KEY ( media_id ) REFERENCES qiita.media( media_id )    ;

ALTER TABLE qiita.media_ingredients ADD CONSTRAINT fk_media_ingredients FOREIGN KEY ( ingredient_id ) REFERENCES qiita.ingredient( ingredient_id )    ;

ALTER TABLE qiita.storage ADD CONSTRAINT fk_storage_media FOREIGN KEY ( media_id ) REFERENCES qiita.media( media_id )    ;

ALTER TABLE qiita.annotation ADD CONSTRAINT fk_annotation_software FOREIGN KEY ( annotator_id ) REFERENCES qiita.software( software_id )    ;

ALTER TABLE qiita.annotation_filepath ADD CONSTRAINT fk_annotation_filepath FOREIGN KEY ( annotation_id ) REFERENCES qiita.annotation( annotation_id )    ;

ALTER TABLE qiita.annotation_filepath ADD CONSTRAINT fk_annotation_filepath_fp FOREIGN KEY ( filepath_id ) REFERENCES qiita.filepath( filepath_id )    ;

ALTER TABLE qiita.assembly ADD CONSTRAINT fk_assembly_software FOREIGN KEY ( assembler_id ) REFERENCES qiita.software( software_id )    ;

ALTER TABLE qiita.assembly_annotation ADD CONSTRAINT fk_assembly_annotation FOREIGN KEY ( assembly_id ) REFERENCES qiita.assembly( assembly_id )    ;

ALTER TABLE qiita.assembly_annotation ADD CONSTRAINT fk_assembly_annotation_annotation FOREIGN KEY ( annotation_id ) REFERENCES qiita.annotation( annotation_id )    ;

ALTER TABLE qiita.assembly_filepath ADD CONSTRAINT fk_assembly_filepath_assembly FOREIGN KEY ( assembly_id ) REFERENCES qiita.assembly( assembly_id )    ;

ALTER TABLE qiita.assembly_filepath ADD CONSTRAINT fk_assembly_filepath_filepath FOREIGN KEY ( filepath_id ) REFERENCES qiita.filepath( filepath_id )    ;

ALTER TABLE qiita.assembly_preprocessed_data ADD CONSTRAINT fk_assembly_preprocessed_data FOREIGN KEY ( preprocessed_data_id ) REFERENCES qiita.preprocessed_data( preprocessed_data_id )    ;

ALTER TABLE qiita.assembly_preprocessed_data ADD CONSTRAINT fk_assembly_preprocessed_data_assembly FOREIGN KEY ( assembly_id ) REFERENCES qiita.assembly( assembly_id )    ;

ALTER TABLE qiita.isolate ADD CONSTRAINT fk_isolate_study_sample FOREIGN KEY ( sample_id ) REFERENCES qiita.study_sample( sample_id )    ;

ALTER TABLE qiita.isolate ADD CONSTRAINT fk_isolate_isolate FOREIGN KEY ( parent_id ) REFERENCES qiita.isolate( isolate_id )    ;

ALTER TABLE qiita.isolate_antibiotic_resistance ADD CONSTRAINT fk_table_0_isolate FOREIGN KEY ( isolate_id ) REFERENCES qiita.isolate( isolate_id )    ;

ALTER TABLE qiita.isolate_antibiotic_resistance ADD CONSTRAINT fk_table_0_antibiotic FOREIGN KEY ( antibiotic_id ) REFERENCES qiita.antibiotic( antibiotic_id )    ;

ALTER TABLE qiita.isolate_antibiotic_sensitivity ADD CONSTRAINT fk_isolate_antibiotic_sensitivity FOREIGN KEY ( antibiotic_id ) REFERENCES qiita.antibiotic( antibiotic_id )    ;

ALTER TABLE qiita.isolate_antibiotic_sensitivity ADD CONSTRAINT fk_isolate_antibiotic_sensitivity_isolate FOREIGN KEY ( isolate_id ) REFERENCES qiita.isolate( isolate_id )    ;

ALTER TABLE qiita.isolate_growth ADD CONSTRAINT fk_isolate_growth_isolate FOREIGN KEY ( isolate_id ) REFERENCES qiita.isolate( isolate_id )    ;

ALTER TABLE qiita.isolate_growth ADD CONSTRAINT fk_isolate_growth_media FOREIGN KEY ( media_id ) REFERENCES qiita.media( media_id )    ;

ALTER TABLE qiita.isolate_growth ADD CONSTRAINT fk_isolate_growth_conditions FOREIGN KEY ( conditions_id ) REFERENCES qiita.conditions( conditions_id )    ;

ALTER TABLE qiita.isolate_growth ADD CONSTRAINT fk_isolate_growth_morphology FOREIGN KEY ( morpholgy_id ) REFERENCES qiita.morphology( morphology_id )    ;

ALTER TABLE qiita.isolate_growth_filepath ADD CONSTRAINT fk_isolate_growth_filepath FOREIGN KEY ( isolate_growth_id ) REFERENCES qiita.isolate_growth( isolate_growth_id )    ;

ALTER TABLE qiita.isolate_growth_filepath ADD CONSTRAINT fk_isolate_growth_filepath_fp FOREIGN KEY ( filepath_id ) REFERENCES qiita.filepath( filepath_id )    ;

ALTER TABLE qiita.isolate_storage ADD CONSTRAINT fk_isolate_storage_storage FOREIGN KEY ( storage_id ) REFERENCES qiita.storage( storage_id )    ;

ALTER TABLE qiita.isolate_storage ADD CONSTRAINT fk_isolate_storage_isolate FOREIGN KEY ( isolate_id ) REFERENCES qiita.isolate( isolate_id )    ;

ALTER TABLE qiita.strain ADD CONSTRAINT fk_strain_assembly FOREIGN KEY ( representative_assembly_id ) REFERENCES qiita.assembly( assembly_id )    ;

ALTER TABLE qiita.strain ADD CONSTRAINT fk_strain_isolate FOREIGN KEY ( representative_isolate_id ) REFERENCES qiita.isolate( isolate_id )    ;

