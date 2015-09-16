-- September 4, 2015
-- Change the database structure to remove the RawData, PreprocessedData and
-- ProcessedData division to unify it into the Artifact object

-- We start by creating the new tables
-- Artifact table - holds an abstract data object from the system
CREATE TABLE qiita.artifact (
    artifact_id          bigserial  NOT NULL,
    generated_timestamp  timestamp  NOT NULL,
    command_id           bigint  ,
    command_parameters_id bigint  ,
    visibility_id        bigint  NOT NULL,
    file_status          bigint  NOT NULL,
    filetype_id          integer  ,
    CONSTRAINT pk_artifact PRIMARY KEY ( artifact_id )
 ) ;
CREATE INDEX idx_artifact_0 ON qiita.artifact ( visibility_id ) ;
CREATE INDEX idx_artifact_1 ON qiita.artifact ( filetype_id ) ;
CREATE INDEX idx_artifact ON qiita.artifact ( command_id ) ;
COMMENT ON TABLE qiita.artifact IS 'Represents data in the system';
COMMENT ON COLUMN qiita.artifact.visibility_id IS 'If the artifact is sandbox, awaiting_for_approval, private or public';
COMMENT ON COLUMN qiita.artifact.file_status IS 'If it is linking, unlinking or idle';

-- Artifact filepath table - relates an artifact with its files
CREATE TABLE qiita.artifact_filepath (
    artifact_id          bigint  NOT NULL,
    filepath_id          bigint  NOT NULL,
    CONSTRAINT idx_artifact_filepath PRIMARY KEY ( artifact_id, filepath_id )
 ) ;
CREATE INDEX idx_artifact_filepath ON qiita.artifact_filepath ( artifact_id ) ;
CREATE INDEX idx_artifact_filepath ON qiita.artifact_filepath ( filepath_id ) ;
ALTER TABLE qiita.artifact_filepath ADD CONSTRAINT fk_artifact_filepath_artifact FOREIGN KEY ( artifact_id ) REFERENCES qiita.artifact( artifact_id )    ;
ALTER TABLE qiita.artifact_filepath ADD CONSTRAINT fk_artifact_filepath_filepath FOREIGN KEY ( filepath_id ) REFERENCES qiita.filepath( filepath_id )    ;

-- Parent artifact table - keeps track of the procenance of a given artifact.
-- If an artifact doesn't have a parent it means that it was uploaded by the user.
CREATE TABLE qiita.parent_artifact (
    artifact_id          bigint  NOT NULL,
    parent_id            bigint  NOT NULL,
    CONSTRAINT idx_parent_artifact PRIMARY KEY ( artifact_id, parent_id )
 ) ;
CREATE INDEX idx_parent_artifact ON qiita.parent_artifact ( artifact_id ) ;
CREATE INDEX idx_parent_artifact ON qiita.parent_artifact ( parent_id ) ;
ALTER TABLE qiita.parent_artifact ADD CONSTRAINT fk_parent_artifact_artifact FOREIGN KEY ( artifact_id ) REFERENCES qiita.artifact( artifact_id )    ;
ALTER TABLE qiita.parent_artifact ADD CONSTRAINT fk_parent_artifact_parent FOREIGN KEY ( parent_id ) REFERENCES qiita.artifact( artifact_id )    ;

-- Study artifact table - relates each artifact with its study
CREATE TABLE qiita.study_artifact (
    study_id             bigint  NOT NULL,
    artifact_id          bigint  NOT NULL,
    CONSTRAINT idx_study_artifact PRIMARY KEY ( study_id, artifact_id )
 ) ;
CREATE INDEX idx_study_artifact ON qiita.study_artifact ( study_id ) ;
CREATE INDEX idx_study_artifact ON qiita.study_artifact ( artifact_id ) ;
ALTER TABLE qiita.study_artifact ADD CONSTRAINT fk_study_artifact_study FOREIGN KEY ( study_id ) REFERENCES qiita.study( study_id )    ;
ALTER TABLE qiita.study_artifact ADD CONSTRAINT fk_study_artifact_artifact FOREIGN KEY ( artifact_id ) REFERENCES qiita.artifact( artifact_id )    ;

-- Visibility table - keeps track of the possible values for the artifact visibility
-- e.g. sandbox, public, private...
CREATE TABLE qiita.visibility (
	visibility_id        bigserial  NOT NULL,
	visibility           varchar  NOT NULL,
	visibility_description varchar  NOT NULL,
	CONSTRAINT pk_visibility PRIMARY KEY ( visibility_id ),
	CONSTRAINT idx_visibility UNIQUE ( visibility )
 );

-- EBI submission table - holds the ebi submission for the artifacts
-- If an artifact cannot be submitted to EBI (e.g. an OTU table) it will not be
-- present in this table. However, if it is not submitted but it can be, it Will
-- have a row in this table with the correspondent status and null accession
-- numbers
CREATE TABLE qiita.ebi_submission (
    artifact_id          bigint  NOT NULL,
    ebi_status_id        bigint  NOT NULL,
    ebi_study_accession  varchar  ,
    ebi_submission_accession varchar  ,
    CONSTRAINT pk_ebi_submission PRIMARY KEY ( artifact_id )
 ) ;
CREATE INDEX idx_ebi_submission ON qiita.ebi_submission ( ebi_status_id ) ;
ALTER TABLE qiita.ebi_submission ADD CONSTRAINT fk_ebi_submission_artifact FOREIGN KEY ( artifact_id ) REFERENCES qiita.artifact( artifact_id )    ;

-- EBI status table - holds the different status that an EBI submission can be
-- e.g. not_submitted, submitted, etc..
CREATE TABLE qiita.ebi_status (
    ebi_status_id        bigint  NOT NULL,
    ebi_status           varchar  NOT NULL,
    ebi_status_description varchar  NOT NULL,
    CONSTRAINT pk_ebi_status PRIMARY KEY ( ebi_status_id )
 ) ;
 ALTER TABLE qiita.ebi_submission ADD CONSTRAINT fk_ebi_submission_ebi_status FOREIGN KEY ( ebi_status_id ) REFERENCES qiita.ebi_status( ebi_status_id )    ;

-- Software table - holds the information og a given software package present
-- in the system and can be used to process an artifact
CREATE TABLE qiita.software (
    software_id          bigserial  NOT NULL,
    name                 varchar  NOT NULL,
    version              varchar  NOT NULL,
    description          varchar  NOT NULL,
    CONSTRAINT pk_software PRIMARY KEY ( software_id )
 ) ;

-- soft_command table - holds the information of a command in a given software
-- this table should be renamed to command once the command table in the
-- analysis table is merged with this one
CREATE TABLE qiita.soft_command (
    command_id           bigserial  NOT NULL,
    software_id          bigint  NOT NULL,
    description          varchar  NOT NULL,
    cli_cmd              varchar  ,
    parameters_table     varchar  NOT NULL,
    CONSTRAINT pk_soft_command PRIMARY KEY ( command_id )
 ) ;
CREATE INDEX idx_soft_command ON qiita.soft_command ( software_id ) ;
ALTER TABLE qiita.soft_command ADD CONSTRAINT fk_soft_command_software FOREIGN KEY ( software_id ) REFERENCES qiita.software( software_id )    ;

-- Publication table - holds the minimum information for a given publication
-- It is useful to keep track of the publication of the studies and the software
-- used for processing artifacts
CREATE TABLE qiita.publication (
    doi                  varchar  NOT NULL,
    pubmed_id            integer  ,
    CONSTRAINT pk_publication PRIMARY KEY ( doi )
 ) ;

-- Software publictation table - relates each software package with the lists of
-- its related publciations
CREATE TABLE qiita.software_publication (
    software_id          bigint  NOT NULL,
    publication_doi      varchar  NOT NULL,
    CONSTRAINT idx_software_publication_0 PRIMARY KEY ( software_id, publication_doi )
 ) ;
CREATE INDEX idx_software_publication ON qiita.software_publication ( software_id ) ;
CREATE INDEX idx_software_publication ON qiita.software_publication ( publication_doi ) ;
ALTER TABLE qiita.software_publication ADD CONSTRAINT fk_software_publication FOREIGN KEY ( software_id ) REFERENCES qiita.software( software_id )    ;
ALTER TABLE qiita.software_publication ADD CONSTRAINT fk_software_publication_0 FOREIGN KEY ( publication_doi ) REFERENCES qiita.publication( doi )    ;

-- Add remaining FK to the artifact table. Creating here since the target tables
-- do not exist when the artifact table was created
ALTER TABLE qiita.artifact ADD CONSTRAINT fk_artifact_visibility FOREIGN KEY ( visibility_id ) REFERENCES qiita.visibility( visibility_id )    ;
ALTER TABLE qiita.artifact ADD CONSTRAINT fk_artifact_filetype FOREIGN KEY ( filetype_id ) REFERENCES qiita.filetype( filetype_id )    ;
ALTER TABLE qiita.artifact ADD CONSTRAINT fk_artifact_soft_command FOREIGN KEY ( command_id ) REFERENCES qiita.soft_command( command_id )    ;

-- Once we have created the new table structure, we can start moving data
-- from the old structure to the new one

-- Populate the visibility table
WITH pd_status as (SELECT processed_data_status_id, processed_data_status, processed_data_status_description)
	INSERT INTO qiita.visibility (visibility_id, visibility, visibility_description)
		VALUES (pd_status.processed_data_status_id, pd_status.processed_data_status,
				pd_status.processed_data_status_description);
UPDATE qiita.visibility
	SET visibility_description = 'Only visible to the owner and shared users'
	WHERE visibility = 'private';
UPDATE qiita.visibility
		SET visibility_description = 'Visible to everybody'
		WHERE visibility = 'public';

-- Moving RawData
-- We need a temp table to store the relations between the old raw data id
-- and the new artifact id, so we can keep track of the parent relationships
CREATE TEMP TABLE raw_data_artifact (
	raw_data_id		bigint NOT NULL,
	artifact_id		bigint NOT NULL,
	CONSTRAINT idx_raw_data_artifact PRIMARY KEY (raw_data_id, artifact_id)
) ON COMMIT drop;

-- We also need to infer the visibility of the artifact, since the raw data
-- object does not have a status attribute. We will use a function to do so:
CREATE FUNCTION infer_rd_status(rd_id bigint) RETURNS bigint AS $$
    BEGIN
        CREATE TEMP TABLE irds_temp
            ON COMMIT drop AS
                SELECT DISTINCT processed_data_status_id
                    FROM qiita.processed_data
                        JOIN qiita.preprocessed_processed_data USING (processed_data_id)
                        JOIN qiita.prep_template_preprocessed_data USING (preprocessed_data_id)
                        JOIN qiita.prep_template USING (prep_template_id)
                    WHERE raw_data_id = rd_id;
            IF EXISTS(SELECT * FROM irds_temp WHERE processed_data_status_id = 2) THEN
                RETURN 2;
            ELSIF EXISTS(SELECT * FROM irds_temp WHERE processed_data_status_id = 3) THEN
                RETURN 3;
            ELSIF EXISTS(SELECT * FROM irds_temp WHERE processed_data_status_id = 1) THEN
                RETURN 1;
            ELSE
                RETURN 4;
            END IF;
    END;
$$ LANGUAGE plpgsql;

DO $do$
DECLARE
	rd_vals	RECORD;
	study	RECORD;
	a_id 	bigint;
	vis_id	bigint;
BEGIN
FOR rd_vals IN
	SELECT raw_data_id, filetype_id, link_filepath_status
	FROM qiita.raw_data
LOOP
	-- Get the visibility of the current raw data
	SELECT infer_rd_status(rd_vals.raw_data_id) INTO vis_id;
	-- Insert the RawData in the artifact table
	INSERT INTO qiita.artifact (generated_timestamp, visibility_id, file_status, filetype_id)
		VALUES (now(), vis_id, rd_vals.link_filepath_status, rd_vals.filetype_id)
		RETURNING artifact_id INTO a_id;
	-- Relate the artifact with their studes
	FOR study IN
		SELECT study_id
		FROM qiita.study_prep_template
			JOIN qiita.prep_template USING (prep_template_id)
		WHERE raw_data_id = rd_vals.raw_data_id
	LOOP
		INSERT INTO qiita.study_artifact (study_id, artifact_id) VALUES (study.study_id, a_id);
	END LOOP;
	-- Relate the artifact with their filepaths
	FOR filepath IN
		SELECT 
END LOOP;
END $do$;

-- Drop the function that we use to infer the status of the artifacts
DROP FUNCTION infer_rd_status(bigint);

-- Prep table
ALTER TABLE qiita.prep_template ADD artifact_id bigint  ;
CREATE INDEX idx_prep_template_0 ON qiita.prep_template ( artifact_id ) ;
ALTER TABLE qiita.prep_template ADD CONSTRAINT fk_prep_template_artifact FOREIGN KEY ( artifact_id ) REFERENCES qiita.artifact( artifact_id )    ;






















-- Drop the old tables of the schema
ALTER TABLE qiita.analysis_sample DROP COLUMN processed_data_id;
DROP INDEX qiita.idx_analysis_sample_0;
ALTER TABLE qiita.analysis_sample DROP CONSTRAINT pk_analysis_sample;
ALTER TABLE qiita.analysis_sample DROP CONSTRAINT fk_analysis_processed_data;
ALTER TABLE qiita.prep_template DROP COLUMN raw_data_id;
DROP INDEX qiita.idx_prep_template_0;
ALTER TABLE qiita.prep_template DROP CONSTRAINT fk_prep_template_raw_data;
DROP TABLE qiita.preprocessed_data;
DROP TABLE qiita.preprocessed_filepath;
DROP TABLE qiita.processed_data_status;
DROP TABLE qiita.raw_data;
DROP TABLE qiita.raw_filepath;
DROP TABLE qiita.study_preprocessed_data;
DROP TABLE qiita.prep_template_preprocessed_data;
DROP TABLE qiita.processed_data;
DROP TABLE qiita.processed_filepath;
DROP TABLE qiita.study_processed_data;
DROP TABLE qiita.preprocessed_processed_data;


-- Analysis table
ALTER TABLE qiita.analysis_sample ADD artifact_id bigint  NOT NULL;
CREATE INDEX idx_analysis_sample_0 ON qiita.analysis_sample ( artifact_id ) ;
ALTER TABLE qiita.analysis_sample ADD CONSTRAINT pk_analysis_sample PRIMARY KEY ( analysis_id, artifact_id, sample_id ) ;
ALTER TABLE qiita.analysis_sample ADD CONSTRAINT fk_analysis_sample_artifact FOREIGN KEY ( artifact_id ) REFERENCES qiita.artifact( artifact_id )    ;


ALTER INDEX idx_common_prep_info_0 RENAME TO idx_required_prep_info_2;
