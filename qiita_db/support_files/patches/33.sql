-- September 4, 2015
-- Change the database structure to remove the RawData, PreprocessedData and
-- ProcessedData division to unify it into the Artifact object

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Rename the id columns from the parameters tables
ALTER TABLE qiita.processed_params_sortmerna RENAME COLUMN processed_params_id TO parameters_id;
ALTER TABLE qiita.processed_params_uclust RENAME COLUMN processed_params_id TO parameters_id;
ALTER TABLE qiita.preprocessed_sequence_454_params RENAME COLUMN preprocessed_params_id TO parameters_id;
ALTER TABLE qiita.preprocessed_sequence_illumina_params RENAME COLUMN preprocessed_params_id TO parameters_id;
ALTER TABLE qiita.preprocessed_spectra_params RENAME COLUMN preprocessed_params_id TO parameters_id;

-- Rename the table filetype
ALTER TABLE qiita.filetype RENAME TO artifact_type;
ALTER TABLE qiita.artifact_type RENAME COLUMN filetype_id TO artifact_type_id;
ALTER TABLE qiita.artifact_type RENAME COLUMN type TO artifact_type;
ALTER TABLE qiita.artifact_type ADD description varchar;

-- Rename the processed_data_status table
ALTER TABLE qiita.processed_data_status RENAME TO visibility;
ALTER TABLE qiita.visibility RENAME COLUMN processed_data_status_id TO visibility_id;
ALTER TABLE qiita.visibility RENAME COLUMN processed_data_status TO visibility;
ALTER TABLE qiita.visibility RENAME COLUMN processed_data_status_description TO visibility_description;
UPDATE qiita.visibility
    SET visibility_description = 'Only visible to the owner and shared users'
    WHERE visibility = 'private';
UPDATE qiita.visibility
    SET visibility_description = 'Visible to everybody'
    WHERE visibility = 'public';

-- Software table - holds the information of a given software package present
-- in the system and can be used to process an artifact
CREATE TABLE qiita.software (
    software_id          bigserial  NOT NULL,
    name                 varchar  NOT NULL,
    version              varchar  NOT NULL,
    description          varchar  NOT NULL,
    environment_script   varchar  NOT NULL,
    start_script         varchar  NOT NULL,
    CONSTRAINT pk_software PRIMARY KEY ( software_id )
 ) ;

-- software_command table - holds the information of a command in a given software
-- this table should be renamed to command once the command table in the
-- analysis table is merged with this one
CREATE TABLE qiita.software_command (
    command_id           bigserial  NOT NULL,
    name                 varchar  NOT NULL,
    software_id          bigint  NOT NULL,
    description          varchar  NOT NULL,
    CONSTRAINT pk_software_command PRIMARY KEY ( command_id )
 ) ;
CREATE INDEX idx_software_command ON qiita.software_command ( software_id ) ;
ALTER TABLE qiita.software_command ADD CONSTRAINT fk_software_command_software FOREIGN KEY ( software_id ) REFERENCES qiita.software( software_id );

-- command_parameter table - holds the parameters that a command accepts
CREATE TABLE qiita.command_parameter (
	command_id           bigint    NOT NULL,
	parameter_name       varchar   NOT NULL,
	parameter_type       varchar   NOT NULL,
	required             bool      NOT NULL,
	default_value        varchar  ,
	CONSTRAINT idx_command_parameter_0 PRIMARY KEY ( command_id, parameter_name )
 ) ;
CREATE INDEX idx_command_parameter ON qiita.command_parameter ( command_id ) ;
ALTER TABLE qiita.command_parameter ADD CONSTRAINT fk_command_parameter FOREIGN KEY ( command_id ) REFERENCES qiita.software_command( command_id )    ;

-- default_parameter_set tables - holds the default parameter sets defined by
-- the system. If no arbitrary parameters are allowed in the system only the
-- ones listed here will be shown. Note that the only parameters that are listed
-- here are the ones that are not required, since the ones required do not
-- have a default
CREATE TABLE qiita.default_parameter_set (
	default_parameter_set_id   bigserial   NOT NULL,
	command_id                 bigint      NOT NULL,
	parameter_set_name         varchar     NOT NULL,
	parameter_set              JSON        NOT NULL,
	CONSTRAINT pk_default_parameter_set PRIMARY KEY ( default_parameter_set_id ),
	CONSTRAINT idx_default_parameter_set_0 UNIQUE ( command_id, parameter_set_name )
 ) ;
CREATE INDEX idx_default_parameter_set ON qiita.default_parameter_set ( command_id ) ;
ALTER TABLE qiita.default_parameter_set ADD CONSTRAINT fk_default_parameter_set FOREIGN KEY ( command_id ) REFERENCES qiita.software_command( command_id )    ;

-- Publication table - holds the minimum information for a given publication
-- It is useful to keep track of the publication of the studies and the software
-- used for processing artifacts
CREATE TABLE qiita.publication (
    doi                  varchar  NOT NULL,
    pubmed_id            varchar  ,
    CONSTRAINT pk_publication PRIMARY KEY ( doi )
 ) ;

-- Software publictation table - relates each software package with the list of
-- its related publciations
CREATE TABLE qiita.software_publication (
    software_id          bigint  NOT NULL,
    publication_doi      varchar  NOT NULL,
    CONSTRAINT idx_software_publication_0 PRIMARY KEY ( software_id, publication_doi )
 ) ;
CREATE INDEX idx_software_publication_software ON qiita.software_publication ( software_id ) ;
CREATE INDEX idx_software_publication_publication ON qiita.software_publication ( publication_doi ) ;
ALTER TABLE qiita.software_publication ADD CONSTRAINT fk_software_publication FOREIGN KEY ( software_id ) REFERENCES qiita.software( software_id )    ;
ALTER TABLE qiita.software_publication ADD CONSTRAINT fk_software_publication_0 FOREIGN KEY ( publication_doi ) REFERENCES qiita.publication( doi )    ;

-- Study publication table - relates each study with the list of its related
-- publication
CREATE TABLE qiita.study_publication (
	study_id             bigint  NOT NULL,
	publication_doi      varchar  NOT NULL,
	CONSTRAINT idx_study_publication_0 PRIMARY KEY ( study_id, publication_doi )
 ) ;
CREATE INDEX idx_study_publication_study ON qiita.study_publication ( study_id ) ;
CREATE INDEX idx_study_publication_doi ON qiita.study_publication ( publication_doi ) ;
ALTER TABLE qiita.study_publication ADD CONSTRAINT fk_study_publication_study FOREIGN KEY ( study_id ) REFERENCES qiita.study( study_id )    ;
ALTER TABLE qiita.study_publication ADD CONSTRAINT fk_study_publication FOREIGN KEY ( publication_doi ) REFERENCES qiita.publication( doi )    ;

-- Artifact table - holds an abstract data object from the system
CREATE TABLE qiita.artifact (
    artifact_id                         bigserial  NOT NULL,
    generated_timestamp                 timestamp  NOT NULL,
    command_id                          bigint  ,
    command_parameters                  json  ,
    visibility_id                       bigint  NOT NULL,
    artifact_type_id                    integer  ,
    data_type_id                        bigint  NOT NULL,
    can_be_submitted_to_ebi             bool DEFAULT 'FALSE' NOT NULL,
	can_be_submitted_to_vamps           bool DEFAULT 'FALSE' NOT NULL,
    submitted_to_vamps                  bool DEFAULT 'FALSE' NOT NULL,
    CONSTRAINT pk_artifact PRIMARY KEY ( artifact_id )
 ) ;
CREATE INDEX idx_artifact_0 ON qiita.artifact ( visibility_id ) ;
CREATE INDEX idx_artifact_1 ON qiita.artifact ( artifact_type_id ) ;
CREATE INDEX idx_artifact_2 ON qiita.artifact ( data_type_id ) ;
CREATE INDEX idx_artifact ON qiita.artifact ( command_id ) ;
COMMENT ON TABLE qiita.artifact IS 'Represents data in the system';
COMMENT ON COLUMN qiita.artifact.visibility_id IS 'If the artifact is sandbox, awaiting_for_approval, private or public';
ALTER TABLE qiita.artifact ADD CONSTRAINT fk_artifact_type FOREIGN KEY ( artifact_type_id ) REFERENCES qiita.artifact_type( artifact_type_id )    ;
ALTER TABLE qiita.artifact ADD CONSTRAINT fk_artifact_visibility FOREIGN KEY ( visibility_id ) REFERENCES qiita.visibility( visibility_id )    ;
ALTER TABLE qiita.artifact ADD CONSTRAINT fk_artifact_software_command FOREIGN KEY ( command_id ) REFERENCES qiita.software_command( command_id )    ;
ALTER TABLE qiita.artifact ADD CONSTRAINT fk_artifact_data_type FOREIGN KEY ( data_type_id ) REFERENCES qiita.data_type( data_type_id )    ;

-- We need to keep the old preprocessed data id for the artifact id due
-- to EBI reasons. In order to make sure that none of the raw data or processed
-- data taht we are going to transfer to the artifact table gets and id needed
-- by the preprocessed data, we are going to set the autoincrementing
-- artifact_id column to start at 10,000
SELECT setval('qiita.artifact_artifact_id_seq', 10000, false);


-- Artifact filepath table - relates an artifact with its files
CREATE TABLE qiita.artifact_filepath (
    artifact_id          bigint  NOT NULL,
    filepath_id          bigint  NOT NULL,
    CONSTRAINT idx_artifact_filepath PRIMARY KEY ( artifact_id, filepath_id )
 ) ;
CREATE INDEX idx_artifact_filepath_artifact ON qiita.artifact_filepath ( artifact_id ) ;
CREATE INDEX idx_artifact_filepath_filepath ON qiita.artifact_filepath ( filepath_id ) ;
ALTER TABLE qiita.artifact_filepath ADD CONSTRAINT fk_artifact_filepath_artifact FOREIGN KEY ( artifact_id ) REFERENCES qiita.artifact( artifact_id )    ;
ALTER TABLE qiita.artifact_filepath ADD CONSTRAINT fk_artifact_filepath_filepath FOREIGN KEY ( filepath_id ) REFERENCES qiita.filepath( filepath_id )    ;

-- Parent artifact table - keeps track of the procenance of a given artifact.
-- If an artifact doesn't have a parent it means that it was uploaded by the user.
CREATE TABLE qiita.parent_artifact (
    artifact_id          bigint  NOT NULL,
    parent_id            bigint  NOT NULL,
    CONSTRAINT idx_parent_artifact PRIMARY KEY ( artifact_id, parent_id )
 ) ;
CREATE INDEX idx_parent_artifact_artifact ON qiita.parent_artifact ( artifact_id ) ;
CREATE INDEX idx_parent_artifact_parent ON qiita.parent_artifact ( parent_id ) ;
ALTER TABLE qiita.parent_artifact ADD CONSTRAINT fk_parent_artifact_artifact FOREIGN KEY ( artifact_id ) REFERENCES qiita.artifact( artifact_id )    ;
ALTER TABLE qiita.parent_artifact ADD CONSTRAINT fk_parent_artifact_parent FOREIGN KEY ( parent_id ) REFERENCES qiita.artifact( artifact_id )    ;

-- Study artifact table - relates each artifact with its study
CREATE TABLE qiita.study_artifact (
    study_id             bigint  NOT NULL,
    artifact_id          bigint  NOT NULL,
    CONSTRAINT idx_study_artifact PRIMARY KEY ( study_id, artifact_id )
 ) ;
CREATE INDEX idx_study_artifact_study ON qiita.study_artifact ( study_id ) ;
CREATE INDEX idx_study_artifact_artifact ON qiita.study_artifact ( artifact_id ) ;
ALTER TABLE qiita.study_artifact ADD CONSTRAINT fk_study_artifact_study FOREIGN KEY ( study_id ) REFERENCES qiita.study( study_id )    ;
ALTER TABLE qiita.study_artifact ADD CONSTRAINT fk_study_artifact_artifact FOREIGN KEY ( artifact_id ) REFERENCES qiita.artifact( artifact_id )    ;

-- Create a function to infer the visibility of the artifact from the
-- raw data
CREATE FUNCTION infer_rd_status(rd_id bigint, st_id bigint) RETURNS bigint AS $$
    DECLARE
        result bigint;
    BEGIN
        CREATE TEMP TABLE irds_temp
            ON COMMIT DROP AS
                SELECT DISTINCT processed_data_status_id
                    FROM qiita.processed_data
                        JOIN qiita.preprocessed_processed_data USING (processed_data_id)
                        JOIN qiita.prep_template_preprocessed_data USING (preprocessed_data_id)
                        JOIN qiita.prep_template USING (prep_template_id)
                        JOIN qiita.study_processed_data USING (processed_data_id)
                    WHERE raw_data_id = rd_id AND study_id = st_id;
        IF EXISTS(SELECT * FROM irds_temp WHERE processed_data_status_id = 2) THEN
            result := 2;
        ELSIF EXISTS(SELECT * FROM irds_temp WHERE processed_data_status_id = 3) THEN
            result := 3;
        ELSIF EXISTS(SELECT * FROM irds_temp WHERE processed_data_status_id = 1) THEN
            result := 1;
        ELSE
            result := 4;
        END IF;
        DROP TABLE irds_temp;
        RETURN result;
    END;
$$ LANGUAGE plpgsql;

-- Create a function to infer the visibility of the artifact from the
-- preprocessed data
CREATE FUNCTION infer_ppd_status(ppd_id bigint) RETURNS bigint AS $$
    DECLARE
        result bigint;
    BEGIN
        CREATE TEMP TABLE ippds_temp
            ON COMMIT DROP AS
                SELECT DISTINCT processed_data_status_id
                    FROM qiita.processed_data
                        JOIN qiita.preprocessed_processed_data USING (processed_data_id)
                    WHERE preprocessed_data_id = ppd_id;
        IF EXISTS(SELECT * FROM ippds_temp WHERE processed_data_status_id = 2) THEN
            result := 2;
        ELSIF EXISTS(SELECT * FROM ippds_temp WHERE processed_data_status_id = 3) THEN
            result := 3;
        ELSEIF EXISTS(SELECT * FROM ippds_temp WHERE processed_data_status_id = 3) THEN
            result := 1;
        ELSE
            result := 4;
        END IF;
        DROP TABLE ippds_temp;
        RETURN result;
    END;
$$ LANGUAGE plpgsql;

-- Populate the software and software_command tables so we can assignt the
-- correct values to the preprocessed and processed tables
INSERT INTO qiita.software (name, version, description, environment_script, start_script) VALUES
    ('QIIME', '1.9.1', 'Quantitative Insights Into Microbial Ecology (QIIME) is an open-source bioinformatics pipeline for performing microbiome analysis from raw DNA sequencing data', 'source activate qiita', 'start_target_gene');
INSERT INTO qiita.publication (doi, pubmed_id) VALUES ('10.1038/nmeth.f.303', '20383131');
INSERT INTO qiita.software_publication (software_id, publication_doi) VALUES (1, '10.1038/nmeth.f.303');
-- Magic number 1: we just created the software table and inserted the QIIME
-- software, which will receive the ID 1
INSERT INTO qiita.software_command (software_id, name, description) VALUES
    (1, 'Split libraries FASTQ', 'Demultiplexes and applies quality control to FASTQ data'),
    (1, 'Split libraries', 'Demultiplexes and applies quality control to FASTA data'),
    (1, 'Pick closed-reference OTUs', 'OTU picking using a closed reference approach');
-- Populate the command_parameter table
-- Magic numbers: we just created the software command table and inserted 3 commands, so we know their ids
--  1: Split libraries FASTQ - preprocessed_sequence_illumina_params
--  2: Split libraries - preprocessed_sequence_454_params
--  3: Pick closed-reference OTUs - processed_params_sortmerna
INSERT INTO qiita.command_parameter (command_id, parameter_name, parameter_type, required, default_value) VALUES
    (1, 'input_data', 'artifact', True, NULL),
    (1, 'max_bad_run_length', 'integer', False, '3'),
    (1, 'min_per_read_length_fraction', 'float', False, '0.75'),
    (1, 'sequence_max_n', 'integer', False, '0'),
    (1, 'rev_comp_barcode', 'bool', False, 'False'),
    (1, 'rev_comp_mapping_barcodes', 'bool', False, 'False'),
    (1, 'rev_comp', 'bool', False, 'False'),
    (1, 'phred_quality_threshold', 'integer', False, '3'),
    (1, 'barcode_type', 'string', False, 'golay_12'),
    (1, 'max_barcode_errors', 'float', False, '1.5'),
    (2, 'input_data', 'artifact', True, NULL),
    (2, 'min_seq_len', 'integer', False, '200'),
    (2, 'max_seq_len', 'integer', False, '1000'),
    (2, 'trim_seq_length', 'bool', False, 'False'),
    (2, 'min_qual_score', 'integer', False, '25'),
    (2, 'max_ambig', 'integer', False, '6'),
    (2, 'max_homopolymer', 'integer', False, '6'),
    (2, 'max_primer_mismatch', 'integer', False, '0'),
    (2, 'barcode_type', 'string', False, 'golay_12'),
    (2, 'max_barcode_errors', 'float', False, '1.5'),
    (2, 'disable_bc_correction', 'bool', False, 'False'),
    (2, 'qual_score_window', 'integer', False, '0'),
    (2, 'disable_primers', 'bool', False, 'False'),
    (2, 'reverse_primers', 'choice:["disable", "truncate_only", "truncate_remove"]', False, 'disable'),
    (2, 'reverse_primer_mismatches', 'integer', False, '0'),
    (2, 'truncate_ambi_bases', 'bool', False, 'False'),
    (3, 'input_data', 'artifact', True, NULL),
    (3, 'reference', 'reference', False, '1'),
    (3, 'sortmerna_e_value', 'float', False, '1'),
    (3, 'sortmerna_max_pos', 'integer', False, '10000'),
    (3, 'similarity', 'float', False, '0.97'),
    (3, 'sortmerna_coverage', 'float', False, '0.97'),
    (3, 'threads', 'integer', False, '1');

-- Populate the default_parameter_set table
DO $do$
DECLARE
    rec     RECORD;
    val     JSON;
BEGIN
    -- Transfer the default parameters from the preprocessed_sequence_illumina_params table
    IF EXISTS(SELECT * FROM qiita.preprocessed_sequence_illumina_params) THEN
        FOR rec IN
            SELECT *
            FROM qiita.preprocessed_sequence_illumina_params
            ORDER BY parameters_id
        LOOP
            val := ('{"max_bad_run_length":' || rec.max_bad_run_length || ','
                    '"min_per_read_length_fraction":' || rec.min_per_read_length_fraction || ','
                    '"sequence_max_n":' || rec.sequence_max_n || ','
                    '"rev_comp_barcode":' || rec.rev_comp_barcode || ','
                    '"rev_comp_mapping_barcodes":' || rec.rev_comp_mapping_barcodes || ','
                    '"rev_comp":' || rec.rev_comp || ','
                    '"phred_quality_threshold":' || rec.phred_quality_threshold || ','
                    '"barcode_type":"' || rec.barcode_type || '",'
                    '"max_barcode_errors":' || rec.max_barcode_errors || '}')::json;
            INSERT INTO qiita.default_parameter_set (command_id, parameter_set_name, parameter_set)
                VALUES (1, rec.param_set_name, val);
        END LOOP;
    ELSE
        INSERT INTO qiita.default_parameter_set (command_id, parameter_set_name, parameter_set)
            VALUES (1, 'Defaults', '{"max_bad_run_length":3,"min_per_read_length_fraction":0.75,"sequence_max_n":0,"rev_comp_barcode":false,"rev_comp_mapping_barcodes":false,"rev_comp":false,"phred_quality_threshold":3,"barcode_type":"golay_12","max_barcode_errors":1.5}'::json);
    END IF;

    -- Transfer the default parameters from the preprocessed_sequence_454_params table
    IF EXISTS(SELECT * FROM qiita.preprocessed_sequence_454_params) THEN
        FOR rec IN
            SELECT *
            FROM qiita.preprocessed_sequence_454_params
            ORDER BY parameters_id
        LOOP
            val := ('{"min_seq_len":' || rec.min_seq_len || ','
                    '"max_seq_len":' || rec.max_seq_len || ','
                    '"trim_seq_length":' || rec.trim_seq_length || ','
                    '"min_qual_score":' || rec.min_qual_score || ','
                    '"max_ambig":' || rec.max_ambig || ','
                    '"max_homopolymer":' || rec.max_homopolymer || ','
                    '"max_primer_mismatch":' || rec.max_primer_mismatch || ','
                    '"barcode_type":"' || rec.barcode_type || '",'
                    '"max_barcode_errors":' || rec.max_barcode_errors || ','
                    '"disable_bc_correction":' || rec.disable_bc_correction || ','
                    '"qual_score_window":' || rec.qual_score_window || ','
                    '"disable_primers":' || rec.disable_primers || ','
                    '"reverse_primers":"' || rec.reverse_primers || '",'
                    '"reverse_primer_mismatches":' || rec.reverse_primer_mismatches || ','
                    '"truncate_ambi_bases":' || rec.truncate_ambig_bases || '}')::json;
            INSERT INTO qiita.default_parameter_set (command_id, parameter_set_name, parameter_set)
                VALUES (2, rec.param_set_name, val);
        END LOOP;
    ELSE
        INSERT INTO qiita.default_parameter_set (command_id, parameter_set_name, parameter_set)
            VALUES (2, 'Defaults', '{"min_seq_len":200,"max_seq_len":1000,"trim_seq_length":false,"min_qual_score":25,"max_ambig":6,"max_homopolymer":6,"max_primer_mismatch":0,"barcode_type":"golay_12","max_barcode_errors":1.5,"disable_bc_correction":false,"qual_score_window":0,"disable_primers":false,"reverse_primers":"disable","reverse_primer_mismatches":0,"truncate_ambi_bases":false}'::json);
    END IF;

    -- Transfer the default parameters from the processed_params_sortmerna table
    IF EXISTS(SELECT * FROM qiita.processed_params_sortmerna) THEN
        FOR rec IN
            SELECT *
            FROM qiita.processed_params_sortmerna
            ORDER BY parameters_id
        LOOP
            val := ('{"reference":' || rec.reference_id || ','
                    '"sortmerna_e_value":' || rec.sortmerna_e_value || ','
                    '"sortmerna_max_pos":' || rec.sortmerna_max_pos || ','
                    '"similarity":' || rec.similarity || ','
                    '"sortmerna_coverage":' || rec.sortmerna_coverage || ','
                    '"threads":' || rec.threads || '}')::json;
            INSERT INTO qiita.default_parameter_set (command_id, parameter_set_name, parameter_set)
                VALUES (3, rec.param_set_name, val);
        END LOOP;
    ELSE
        INSERT INTO qiita.default_parameter_set (command_id, parameter_set_name, parameter_set)
            VALUES (3, 'Defaults', '{"reference":1,"sortmerna_e_value":1,"sortmerna_max_pos":10000,"similarity":0.97,"sortmerna_coverage":0.97,"threads":1}'::json);
    END IF;
END $do$;

-- Create tables to keep track of the processing jobs
CREATE TABLE qiita.processing_job_status (
	processing_job_status_id           bigserial  NOT NULL,
	processing_job_status              varchar    NOT NULL,
	processing_job_status_description  varchar    NOT NULL,
	CONSTRAINT pk_processing_job_status PRIMARY KEY ( processing_job_status_id )
 ) ;

INSERT INTO qiita.processing_job_status
        (processing_job_status, processing_job_status_description)
    VALUES ('queued', 'The job is waiting to be run'),
           ('running', 'The job is running'),
           ('success', 'The job completed successfully'),
           ('error', 'The job failed');

CREATE TABLE qiita.processing_job (
	processing_job_id          UUID     DEFAULT uuid_generate_v4(),
	email                      varchar  NOT NULL,
	command_id                 bigint   NOT NULL,
	command_parameters         json     NOT NULL,
	processing_job_status_id   bigint   NOT NULL,
	logging_id                 bigint  ,
	heartbeat                  timestamp  ,
	step                       varchar  ,
	CONSTRAINT pk_processing_job PRIMARY KEY ( processing_job_id )
 ) ;
CREATE INDEX idx_processing_job_email ON qiita.processing_job ( email ) ;
CREATE INDEX idx_processing_job_command_id ON qiita.processing_job ( command_id ) ;
CREATE INDEX idx_processing_job_status_id ON qiita.processing_job ( processing_job_status_id ) ;
CREATE INDEX idx_processing_job_logging ON qiita.processing_job ( logging_id ) ;
COMMENT ON COLUMN qiita.processing_job.email IS 'The user that launched the job';
COMMENT ON COLUMN qiita.processing_job.command_id IS 'The command launched';
COMMENT ON COLUMN qiita.processing_job.command_parameters IS 'The parameters used in the command';
COMMENT ON COLUMN qiita.processing_job.logging_id IS 'In case of failure, point to the log entry that holds more information about the error';
COMMENT ON COLUMN qiita.processing_job.heartbeat IS 'The last heartbeat received by this job';
ALTER TABLE qiita.processing_job ADD CONSTRAINT fk_processing_job_qiita_user FOREIGN KEY ( email ) REFERENCES qiita.qiita_user( email )    ;
ALTER TABLE qiita.processing_job ADD CONSTRAINT fk_processing_job FOREIGN KEY ( command_id ) REFERENCES qiita.software_command( command_id )    ;
ALTER TABLE qiita.processing_job ADD CONSTRAINT fk_processing_job_status FOREIGN KEY ( processing_job_status_id ) REFERENCES qiita.processing_job_status( processing_job_status_id )    ;
ALTER TABLE qiita.processing_job ADD CONSTRAINT fk_processing_job_logging FOREIGN KEY ( logging_id ) REFERENCES qiita.logging( logging_id )    ;

CREATE TABLE qiita.artifact_processing_job (
	artifact_id          bigint  NOT NULL,
	processing_job_id    UUID    NOT NULL,
	CONSTRAINT idx_artifact_processing_job PRIMARY KEY ( artifact_id, processing_job_id )
 ) ;
CREATE INDEX idx_artifact_processing_job_artifact ON qiita.artifact_processing_job ( artifact_id ) ;
CREATE INDEX idx_artifact_processing_job_job ON qiita.artifact_processing_job ( processing_job_id ) ;
ALTER TABLE qiita.artifact_processing_job ADD CONSTRAINT fk_artifact_processing_job FOREIGN KEY ( artifact_id ) REFERENCES qiita.artifact( artifact_id )    ;
ALTER TABLE qiita.artifact_processing_job ADD CONSTRAINT fk_artifact_processing_job_0 FOREIGN KEY ( processing_job_id ) REFERENCES qiita.processing_job( processing_job_id )    ;

-- Create a function to correctly choose the commnad id for the preprocessed
-- data
CREATE FUNCTION choose_command_id(ppd_params_table varchar) RETURNS bigint AS $$
    BEGIN
        IF ppd_params_table = 'preprocessed_sequence_illumina_params' THEN
            RETURN 1;
        ELSE
            RETURN 2;
        END IF;
    END;
$$ LANGUAGE plpgsql;

-- Create a function to correctly generate the parameters used to generate the artifact
CREATE FUNCTION generate_params(command_id bigint, params_id bigint, parent_id bigint) RETURNS json AS $$
    DECLARE
        c1_rec      qiita.preprocessed_sequence_illumina_params%ROWTYPE;
        c2_rec      qiita.preprocessed_sequence_454_params%ROWTYPE;
        c3_rec      qiita.processed_params_sortmerna%ROWTYPE;
        val         json;
    BEGIN
        IF command_id = 1 THEN
            SELECT * INTO c1_rec
            FROM qiita.preprocessed_sequence_illumina_params
            WHERE parameters_id = params_id;
            val := ('{"max_bad_run_length":' || c1_rec.max_bad_run_length || ','
                    '"min_per_read_length_fraction":' || c1_rec.min_per_read_length_fraction || ','
                    '"sequence_max_n":' || c1_rec.sequence_max_n || ','
                    '"rev_comp_barcode":' || c1_rec.rev_comp_barcode || ','
                    '"rev_comp_mapping_barcodes":' || c1_rec.rev_comp_mapping_barcodes || ','
                    '"rev_comp":' || c1_rec.rev_comp || ','
                    '"phred_quality_threshold":' || c1_rec.phred_quality_threshold || ','
                    '"barcode_type":"' || c1_rec.barcode_type || '",'
                    '"max_barcode_errors":' || c1_rec.max_barcode_errors || ','
                    '"input_data":' || parent_id || '}')::json;
        ELSIF command_id = 2 THEN
            SELECT * INTO c2_rec
            FROM qiita.preprocessed_sequence_454_params
            WHERE parameters_id = params_id;
            val := ('{"min_seq_len":' || c2_rec.min_seq_len || ','
                    '"max_seq_len":' || c2_rec.max_seq_len || ','
                    '"trim_seq_length":' || c2_rec.trim_seq_length || ','
                    '"min_qual_score":' || c2_rec.min_qual_score || ','
                    '"max_ambig":' || c2_rec.max_ambig || ','
                    '"max_homopolymer":' || c2_rec.max_homopolymer || ','
                    '"max_primer_mismatch":' || c2_rec.max_primer_mismatch || ','
                    '"barcode_type":"' || c2_rec.barcode_type || '",'
                    '"max_barcode_errors":' || c2_rec.max_barcode_errors || ','
                    '"disable_bc_correction":' || c2_rec.disable_bc_correction || ','
                    '"qual_score_window":' || c2_rec.qual_score_window || ','
                    '"disable_primers":' || c2_rec.disable_primers || ','
                    '"reverse_primers":"' || c2_rec.reverse_primers || '",'
                    '"reverse_primer_mismatches":' || c2_rec.reverse_primer_mismatches || ','
                    '"truncate_ambi_bases":' || c2_rec.truncate_ambig_bases || ','
                    '"input_data":' || parent_id || '}')::json;
        ELSE
            SELECT * INTO c3_rec
            FROM qiita.processed_params_sortmerna
            WHERE parameters_id = params_id;
            val := ('{"reference":' || c3_rec.reference_id || ','
                    '"sortmerna_e_value":' || c3_rec.sortmerna_e_value || ','
                    '"sortmerna_max_pos":' || c3_rec.sortmerna_max_pos || ','
                    '"similarity":' || c3_rec.similarity || ','
                    '"sortmerna_coverage":' || c3_rec.sortmerna_coverage || ','
                    '"threads":' || c3_rec.threads || ','
                    '"input_data":' || parent_id || '}')::json;
        END IF;
        RETURN val;
    END;
$$ LANGUAGE plpgsql;

-- We need to modify the prep template table to point to the artifact table
-- rather than to the raw data table
ALTER TABLE qiita.prep_template ADD artifact_id bigint;
CREATE INDEX idx_prep_template_artifact_id ON qiita.prep_template (artifact_id);
ALTER TABLE qiita.prep_template ADD CONSTRAINT fk_prep_template_artifact
    FOREIGN KEY ( artifact_id ) REFERENCES qiita.artifact(artifact_id);

-- We need to modify the ebi run accession table to point to the artifact table
-- rather than to the preprocessed data table
ALTER TABLE qiita.ebi_run_accession ADD artifact_id bigint;
CREATE INDEX idx_ebi_run_accession_artifact_id ON qiita.ebi_run_accession (artifact_id);
ALTER TABLE qiita.ebi_run_accession ADD CONSTRAINT fk_ebi_run_accesion_artifact
    FOREIGN KEY ( artifact_id ) REFERENCES qiita.artifact(artifact_id);

-- We need to modify the analysis_sample table to point to the artifact table
-- rather than to the processed data table
ALTER TABLE qiita.analysis_sample ADD artifact_id bigint;
CREATE INDEX idx_analysis_sample_artifact_id ON qiita.analysis_sample ( artifact_id ) ;
ALTER TABLE qiita.analysis_sample ADD CONSTRAINT fk_analysis_sample_artifact FOREIGN KEY ( artifact_id ) REFERENCES qiita.artifact( artifact_id )    ;

-- Move the data!
DO $do$
DECLARE
    pt_vals         RECORD;
    ppd_vals        RECORD;
    pd_vals         RECORD;
    rd_fp_vals      RECORD;
    ppd_fp_vals     RECORD;
    pd_fp_vals      RECORD;
    study_pmids     RECORD;
    a_type          RECORD;
    rd_vis_id       bigint;
    ppd_vis_id      bigint;
    rd_a_id         bigint;
    ppd_a_id        bigint;
    pd_a_id         bigint;
    demux_type_id   bigint;
    biom_type_id    bigint;
    ppd_cmd_id      bigint;
    job_id          UUID;
    params          json;
BEGIN
    -- We need a new artifact type for representing demultiplexed data (the
    -- only type of preprocessed data that we have at this point) and
    -- OTU table (the only type of processed data that we have at this point)
    INSERT INTO qiita.artifact_type (artifact_type, description)
        VALUES ('Demultiplexed', 'Demultiplexed and QC sequeneces')
        RETURNING artifact_type_id INTO demux_type_id;
    INSERT INTO qiita.artifact_type (artifact_type, description)
        VALUES ('BIOM', 'BIOM table')
        RETURNING artifact_type_id INTO biom_type_id;

    -- Loop through all the prep templates. We are going to transfer all the data
    -- using the following schema (->* means 1 to N relationship)
    -- prep_template -> raw_data ->* preprocessed_data ->* processed_data ->* analysis_sample
    -- Using this approach will duplicate the raw data objects. However, this is
    -- intentional as the raw data sharing should be done at filepath level rather
    -- than at raw data level. See issue #1459.
    FOR pt_vals IN
        SELECT prep_template_id, raw_data_id, filetype_id, study_id, data_type_id, email
        FROM qiita.prep_template
            JOIN qiita.raw_data USING (raw_data_id)
            JOIN qiita.study_prep_template USING (prep_template_id)
            JOIN qiita.study USING (study_id)
        WHERE raw_data_id IS NOT NULL
    LOOP
        -- Move the raw_data
        -- Get the visibility of the current raw data
        SELECT infer_rd_status(pt_vals.raw_data_id, pt_vals.study_id) INTO rd_vis_id;

        -- Insert the raw data in the artifact table
        INSERT INTO qiita.artifact (generated_timestamp, visibility_id, artifact_type_id, data_type_id)
            VALUES (now(), rd_vis_id, pt_vals.filetype_id, pt_vals.data_type_id)
            RETURNING artifact_id INTO rd_a_id;

        -- Relate the artifact with their studies
        INSERT INTO qiita.study_artifact (study_id, artifact_id)
            VALUES (pt_vals.study_id, rd_a_id);

        -- Relate the artifact with their filepaths
        FOR rd_fp_vals IN
            SELECT filepath_id
            FROM qiita.raw_filepath
            WHERE raw_data_id = pt_vals.raw_data_id
        LOOP
            INSERT INTO qiita.artifact_filepath (filepath_id, artifact_id)
                VALUES (rd_fp_vals.filepath_id, rd_a_id);
        END LOOP;

        -- Update the prep template table to point to the newly created artifact
        UPDATE qiita.prep_template
            SET artifact_id = rd_a_id
            WHERE prep_template_id = pt_vals.prep_template_id;

        -- Move the preprocessed data that has been generated from this prep template
        -- and, by extension, by the current raw data
        FOR ppd_vals IN
            SELECT preprocessed_data_id, preprocessed_params_table, preprocessed_params_id,
                   data_type_id, submitted_to_vamps_status, processing_status, data_type_id
            FROM qiita.preprocessed_data
                JOIN qiita.prep_template_preprocessed_data USING (preprocessed_data_id)
            WHERE prep_template_id = pt_vals.prep_template_id
        LOOP
            -- Get the visibility of the current raw data
            SELECT infer_ppd_status(ppd_vals.preprocessed_data_id) INTO ppd_vis_id;

            -- Get the correct command id
            SELECT choose_command_id(ppd_vals.preprocessed_params_table) INTO ppd_cmd_id;

            -- Get the correct parameters
            SELECT generate_params(ppd_cmd_id, ppd_vals.preprocessed_params_id, rd_a_id) INTO params;

            -- Insert the preprocessed data in the artifact table
            INSERT INTO qiita.artifact (artifact_id, generated_timestamp, visibility_id,
                                        artifact_type_id, data_type_id, command_id,
                                        command_parameters, can_be_submitted_to_ebi,
                                        can_be_submitted_to_vamps)
                VALUES (ppd_vals.preprocessed_data_id, now(), ppd_vis_id,
                        demux_type_id, ppd_vals.data_type_id, ppd_cmd_id,
                        params, TRUE, TRUE)
                RETURNING artifact_id INTO ppd_a_id;

            -- Insert the job that created this preprocessed data
            -- Magic number 3: success status - if we have an artifact
            -- is because the job completed successfully
            INSERT INTO qiita.processing_job (email, command_id, command_parameters,
                                              processing_job_status_id)
                VALUES (pt_vals.email, ppd_cmd_id, params, 3)
                RETURNING processing_job_id INTO job_id;

            -- Link the parent with the job
            INSERT INTO qiita.artifact_processing_job (artifact_id, processing_job_id)
                VALUES (rd_a_id, job_id);

            -- Relate the artifact with the study
            INSERT INTO qiita.study_artifact (study_id, artifact_id)
                VALUES (pt_vals.study_id, ppd_a_id);

            -- Relate the artifact with their filepaths
            FOR ppd_fp_vals IN
                SELECT filepath_id
                FROM qiita.preprocessed_filepath
                WHERE preprocessed_data_id = ppd_vals.preprocessed_data_id
            LOOP
                INSERT INTO qiita.artifact_filepath (filepath_id, artifact_id)
                    VALUES (ppd_fp_vals.filepath_id, ppd_a_id);
            END LOOP;

            -- Relate the artifact with its parent
            INSERT INTO qiita.parent_artifact (artifact_id, parent_id)
                VALUES (ppd_a_id, rd_a_id);

            -- Update the run ebi accession table so it point to the correct
            -- artifact rather than the preprocessed data
            UPDATE qiita.ebi_run_accession
                SET artifact_id = ppd_a_id
                WHERE preprocessed_data_id = ppd_vals.preprocessed_data_id;

            -- Update VAMPS value in case that it was submitted to VAMPS
            IF ppd_vals.submitted_to_vamps_status = 'submitted' THEN
                UPDATE qiita.artifact
                    SET submitted_to_vamps = TRUE
                    WHERE artifact_id = ppd_a_id;
            END IF;

            -- Move the processed data that has been generated from this
            -- preprocessed data
            FOR pd_vals IN
                SELECT processed_data_id, processed_params_table, processed_params_id,
                       processed_date, data_type_id, processed_data_status_id, data_type_id
                FROM qiita.processed_data
                    JOIN qiita.preprocessed_processed_data USING (processed_data_id)
                WHERE preprocessed_data_id = ppd_vals.preprocessed_data_id
            LOOP
                -- Get the correct parameters
                SELECT generate_params(3, pd_vals.processed_params_id, ppd_a_id) INTO params;

                -- Insert the processed data in the artifact table
                -- Magic number 3: we've created the software_command table here
                -- and we know the order that we inserted the commands. The
                -- OTU pickking command is the number 3
                INSERT INTO qiita.artifact (generated_timestamp, visibility_id,
                                            artifact_type_id, data_type_id, command_id,
                                            command_parameters)
                    VALUES (pd_vals.processed_date, pd_vals.processed_data_status_id,
                            biom_type_id, ppd_vals.data_type_id, 3, params)
                    RETURNING artifact_id into pd_a_id;

                -- Insert the job that created this processed data
                -- Magic number 3: success status - if we have an artifact
                -- is because the job completed successfully
                INSERT INTO qiita.processing_job (email, command_id, command_parameters,
                                                  processing_job_status_id)
                    VALUES (pt_vals.email, 3, params, 3)
                    RETURNING processing_job_id INTO job_id;

                -- Link the parent with the job
                INSERT INTO qiita.artifact_processing_job (artifact_id, processing_job_id)
                    VALUES (ppd_a_id, job_id);

                -- Relate the artifact with the study
                INSERT INTO qiita.study_artifact (study_id, artifact_id)
                    VALUES (pt_vals.study_id, pd_a_id);

                -- Relate the artifact with their filepaths
                FOR pd_fp_vals IN
                    SELECT filepath_id
                    FROM qiita.processed_filepath
                    WHERE processed_data_id = pd_vals.processed_data_id
                LOOP
                    INSERT INTO qiita.artifact_filepath (filepath_id, artifact_id)
                        VALUES (pd_fp_vals.filepath_id, pd_a_id);
                END LOOP;

                -- Relate the artifact with its parent
                INSERT INTO qiita.parent_artifact (artifact_id, parent_id)
                    VALUES (pd_a_id, ppd_a_id);

                -- Update the analysis sample table so it points to the correct
                -- artifact
                UPDATE qiita.analysis_sample
                    SET artifact_id = pd_a_id
                    WHERE processed_data_id = pd_vals.processed_data_id;
            END LOOP;
        END LOOP;
    END LOOP;

    -- Move the study_pmid information to the publication and study_publication
    -- tables
    FOR study_pmids IN
        SELECT study_id, pmid
        FROM qiita.study_pmid
    LOOP
        INSERT INTO qiita.publication (doi, pubmed_id)
            SELECT study_pmids.pmid, study_pmids.pmid
            WHERE NOT EXISTS(
                SELECT doi FROM qiita.publication WHERE doi = study_pmids.pmid);

        INSERT INTO qiita.study_publication (study_id, publication_doi)
            VALUES (study_pmids.study_id, study_pmids.pmid);
    END LOOP;

    -- The column subdirectory in the data_directory was unused
    -- We are going to "recycle" it so we can indicate which mountpoints use the
    -- new file structure in which a subdirectory for the artifact is created and
    -- the files are stored under such subdirectory, rather than just prefixing
    -- the files with the artifact_id
    ALTER TABLE qiita.data_directory ALTER COLUMN subdirectory SET DATA TYPE bool USING FALSE;
    ALTER TABLE qiita.data_directory ALTER COLUMN subdirectory SET DEFAULT FALSE;
    ALTER TABLE qiita.data_directory ALTER COLUMN subdirectory SET NOT NULL;

    -- The artifacts will be stored now based on the artifact type
    -- Add the new mountpoints to the qiita.data_directory table
    FOR a_type IN
        SELECT artifact_type
        FROM qiita.artifact_type
    LOOP
        INSERT INTO qiita.data_directory (data_type, mountpoint, subdirectory, active)
            VALUES (a_type.artifact_type, a_type.artifact_type, true, true);
    END LOOP;
END $do$;

-- Set the NOT NULL constraints that we couldn't set before because we were
-- transferring the data from the old structure
ALTER TABLE qiita.ebi_run_accession ALTER COLUMN artifact_id SET NOT NULL;
ALTER TABLE qiita.analysis_sample ALTER COLUMN artifact_id SET NOT NULL;

ALTER TABLE qiita.analysis_sample DROP CONSTRAINT pk_analysis_sample;
ALTER TABLE qiita.analysis_sample ADD CONSTRAINT pk_analysis_sample PRIMARY KEY ( analysis_id, artifact_id, sample_id ) ;

-- Drop the function that we use to infer the status of the raw data and
-- preprocessed artifact, as well as the function to get the correct parameter
DROP FUNCTION infer_rd_status(bigint, bigint);
DROP FUNCTION infer_ppd_status(bigint);
DROP FUNCTION choose_command_id(varchar);
DROP FUNCTION generate_params(bigint, bigint, bigint);

-- Drop the old SQL structure from the schema
ALTER TABLE qiita.prep_template DROP COLUMN raw_data_id;
ALTER TABLE qiita.ebi_run_accession DROP COLUMN preprocessed_data_id;
ALTER TABLE qiita.analysis_sample DROP COLUMN processed_data_id;
DROP TABLE qiita.preprocessed_processed_data;
DROP TABLE qiita.study_processed_data;
DROP TABLE qiita.processed_filepath;
DROP TABLE qiita.processed_data;
DROP TABLE qiita.preprocessed_filepath;
DROP TABLE qiita.study_preprocessed_data;
DROP TABLE qiita.prep_template_preprocessed_data;
DROP TABLE qiita.preprocessed_data;
DROP TABLE qiita.raw_filepath;
DROP TABLE qiita.raw_data;
DROP TABLE qiita.study_pmid;
DROP TABLE qiita.processed_params_uclust;
DROP TABLE qiita.processed_params_sortmerna;
DROP TABLE qiita.preprocessed_sequence_454_params;
DROP TABLE qiita.preprocessed_sequence_illumina_params;
DROP TABLE qiita.preprocessed_spectra_params;

-- Create a function to return the roots of an artifact, i.e. the source artifacts
CREATE FUNCTION qiita.find_artifact_roots(a_id bigint) RETURNS SETOF bigint AS $$
BEGIN
    IF EXISTS(SELECT * FROM qiita.parent_artifact WHERE artifact_id = a_id) THEN
        RETURN QUERY WITH RECURSIVE root AS (
            SELECT artifact_id, parent_id
            FROM qiita.parent_artifact
            WHERE artifact_id = a_id
          UNION
            SELECT p.artifact_id, p.parent_id
            FROM qiita.parent_artifact p
            JOIN root r ON (r.parent_id = p.artifact_id)
        )
        SELECT DISTINCT parent_id
            FROM root
            WHERE parent_id NOT IN (SELECT artifact_id
                                    FROM qiita.parent_artifact);
    ELSE
        RETURN QUERY SELECT a_id;
    END IF;
END
$$ LANGUAGE plpgsql;
