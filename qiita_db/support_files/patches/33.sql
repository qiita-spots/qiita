-- September 4, 2015
-- Change the database structure to remove the RawData, PreprocessedData and
-- ProcessedData division to unify it into the Artifact object

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
    cli_cmd              varchar  ,
    parameters_table     varchar  NOT NULL,
    CONSTRAINT pk_software_command PRIMARY KEY ( command_id )
 ) ;
CREATE INDEX idx_software_command ON qiita.software_command ( software_id ) ;
ALTER TABLE qiita.software_command ADD CONSTRAINT fk_software_command_software FOREIGN KEY ( software_id ) REFERENCES qiita.software( software_id );

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
    command_parameters_id               bigint  ,
    visibility_id                       bigint  NOT NULL,
    artifact_type_id                    integer  ,
    can_be_submitted_to_ebi             bool DEFAULT 'FALSE' NOT NULL,
	can_be_submitted_to_vamps           bool DEFAULT 'FALSE' NOT NULL,
    submitted_to_vamps                  bool DEFAULT 'FALSE' NOT NULL,
    CONSTRAINT pk_artifact PRIMARY KEY ( artifact_id )
 ) ;
CREATE INDEX idx_artifact_0 ON qiita.artifact ( visibility_id ) ;
CREATE INDEX idx_artifact_1 ON qiita.artifact ( artifact_type_id ) ;
CREATE INDEX idx_artifact ON qiita.artifact ( command_id ) ;
COMMENT ON TABLE qiita.artifact IS 'Represents data in the system';
COMMENT ON COLUMN qiita.artifact.visibility_id IS 'If the artifact is sandbox, awaiting_for_approval, private or public';
ALTER TABLE qiita.artifact ADD CONSTRAINT fk_artifact_type FOREIGN KEY ( artifact_type_id ) REFERENCES qiita.artifact_type( artifact_type_id )    ;
ALTER TABLE qiita.artifact ADD CONSTRAINT fk_artifact_visibility FOREIGN KEY ( visibility_id ) REFERENCES qiita.visibility( visibility_id )    ;
ALTER TABLE qiita.artifact ADD CONSTRAINT fk_artifact_software_command FOREIGN KEY ( command_id ) REFERENCES qiita.software_command( command_id )    ;

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
INSERT INTO qiita.software (name, version, description) VALUES
    ('QIIME', '1.9.1', 'Quantitative Insights Into Microbial Ecology (QIIME) is an open-source bioinformatics pipeline for performing microbiome analysis from raw DNA sequencing data');
INSERT INTO qiita.publication (doi, pubmed_id) VALUES ('10.1038/nmeth.f.303', '20383131');
INSERT INTO qiita.software_publication (software_id, publication_doi) VALUES (1, '10.1038/nmeth.f.303');
-- Magic number 1: be just created the software table and inserted the QIIME
-- software, which will receive the ID 1
INSERT INTO qiita.software_command (software_id, name, description, cli_cmd, parameters_table) VALUES
    (1, 'Split libraries FASTQ', 'Demultiplexes and applies quality control to FASTQ data', 'split_libraries_fastq.py', 'preprocessed_sequence_illumina_params'),
    (1, 'Split libraries', 'Demultiplexes and applies quality control to FASTA data', 'split_libraries.py', 'preprocessed_sequence_454_params'),
    (1, 'Pick closed-reference OTUs', 'OTU picking using a closed reference approach', 'pick_closed_reference_otus.py', 'processed_params_sortmerna');

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
    rd_vis_id       bigint;
    ppd_vis_id      bigint;
    rd_a_id         bigint;
    ppd_a_id        bigint;
    pd_a_id         bigint;
    demux_type_id   bigint;
    biom_type_id    bigint;
    ppd_cmd_id      bigint;
BEGIN
    -- We need a new artifact type for representing demultiplexed data (the
    -- only type of preprocessed data that we have at this point) and
    -- OTU table (the only type of processed data that we have at this point)
    INSERT INTO qiita.artifact_type (artifact_type, description)
        VALUES ('Demultiplexed', 'Demultiplexed and QC sequeneces')
        RETURNING artifact_type_id INTO demux_type_id;
    INSERT INTO qiita.artifact_type (artifact_type, description)
        VALUES ('BIOM table', 'Biom table')
        RETURNING artifact_type_id INTO biom_type_id;

    -- Loop through all the prep templates. We are going to transfer all the data
    -- using the following schema (->* means 1 to N relationship)
    -- prep_template -> raw_data ->* preprocessed_data ->* processed_data ->* analysis_sample
    -- Using this approach will duplicate the raw data objects. However, this is
    -- intentional as the raw data sharing should be done at filepath level rather
    -- than at raw data level. See issue #1459.
    FOR pt_vals IN
        SELECT prep_template_id, raw_data_id, filetype_id, study_id
        FROM qiita.prep_template
            JOIN qiita.raw_data USING (raw_data_id)
            JOIN qiita.study_prep_template USING (prep_template_id)
        WHERE raw_data_id IS NOT NULL
    LOOP
        -- Move the raw_data
        -- Get the visibility of the current raw data
        SELECT infer_rd_status(pt_vals.raw_data_id, pt_vals.study_id) INTO rd_vis_id;

        -- Insert the raw data in the artifact table
        INSERT INTO qiita.artifact (generated_timestamp, visibility_id, artifact_type_id)
            VALUES (now(), rd_vis_id, pt_vals.filetype_id)
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
                   data_type_id, submitted_to_vamps_status, processing_status
            FROM qiita.preprocessed_data
                JOIN qiita.prep_template_preprocessed_data USING (preprocessed_data_id)
            WHERE prep_template_id = pt_vals.prep_template_id
        LOOP
            -- Get the visibility of the current raw data
            SELECT infer_ppd_status(ppd_vals.preprocessed_data_id) INTO ppd_vis_id;

            -- Get the correct command id
            SELECT choose_command_id(ppd_vals.preprocessed_params_table) INTO ppd_cmd_id;

            -- Insert the preprocessed data in the artifact table
            INSERT INTO qiita.artifact (generated_timestamp, visibility_id,
                                        artifact_type_id, command_id,
                                        command_parameters_id, can_be_submitted_to_ebi,
                                        can_be_submitted_to_vamps)
                VALUES (now(), ppd_vis_id, demux_type_id, ppd_cmd_id,
                        ppd_vals.preprocessed_params_id, TRUE, TRUE)
                RETURNING artifact_id INTO ppd_a_id;

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
                       processed_date, data_type_id, processed_data_status_id
                FROM qiita.processed_data
                    JOIN qiita.preprocessed_processed_data USING (processed_data_id)
                WHERE preprocessed_data_id = ppd_vals.preprocessed_data_id
            LOOP
                -- Insert the processed data in the artifact table
                -- Magic number 3: we've created the software_command table here
                -- and we know the order that we inserted the commands. The
                -- OTU pickking command is the number 3
                INSERT INTO qiita.artifact (generated_timestamp, visibility_id,
                                            artifact_type_id, command_id,
                                            command_parameters_id)
                    VALUES (pd_vals.processed_date, pd_vals.processed_data_status_id,
                            biom_type_id, 3, pd_vals.processed_params_id)
                    RETURNING artifact_id into pd_a_id;

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
            VALUES (study_pmids.pmid, study_pmids.pmid);

        INSERT INTO qiita.study_publication (study_id, publication_doi)
            VALUES (study_pmids.study_id, study_pmids.pmid);
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
