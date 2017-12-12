-- Jan 25, 2016
-- Move the can_be_submitted_to_XX columns to the artifact type

ALTER TABLE qiita.artifact DROP COLUMN can_be_submitted_to_ebi;
ALTER TABLE qiita.artifact DROP COLUMN can_be_submitted_to_vamps;
ALTER TABLE qiita.artifact_type ADD can_be_submitted_to_ebi bool DEFAULT 'FALSE' NOT NULL;
ALTER TABLE qiita.artifact_type ADD can_be_submitted_to_vamps bool DEFAULT 'FALSE' NOT NULL;

UPDATE qiita.artifact_type SET can_be_submitted_to_ebi = TRUE, can_be_submitted_to_vamps = TRUE
    WHERE artifact_type = 'Demultiplexed';

-- Jan 26, 2016
-- Relate the artifact types with the filepath types that they support

CREATE TABLE qiita.artifact_type_filepath_type (
	artifact_type_id     bigint  NOT NULL,
	filepath_type_id     bigint  NOT NULL,
	required             bool DEFAULT 'TRUE' NOT NULL,
	CONSTRAINT idx_artifact_type_filepath_type PRIMARY KEY ( artifact_type_id, filepath_type_id )
 ) ;

CREATE INDEX idx_artifact_type_filepath_type_at ON qiita.artifact_type_filepath_type ( artifact_type_id ) ;
CREATE INDEX idx_artifact_type_filepath_type_ft ON qiita.artifact_type_filepath_type ( filepath_type_id ) ;
ALTER TABLE qiita.artifact_type_filepath_type ADD CONSTRAINT fk_artifact_type_filepath_type_at FOREIGN KEY ( artifact_type_id ) REFERENCES qiita.artifact_type( artifact_type_id )    ;
ALTER TABLE qiita.artifact_type_filepath_type ADD CONSTRAINT fk_artifact_type_filepath_type_ft FOREIGN KEY ( filepath_type_id ) REFERENCES qiita.filepath_type( filepath_type_id )    ;

INSERT INTO qiita.artifact_type_filepath_type (artifact_type_id, filepath_type_id, required) VALUES
    -- Artifact Type: SFF - Filepath Types: raw_sff (required)
    (1, 17, TRUE),
    -- Artifact Type: FASTA_Sanger - Filepath Types: raw_fasta (required)
    (2, 18, TRUE),
    -- Artifact Type: FASTQ - Filepath Types: raw_forward_seqs (required), raw_reverse_seqs (optional), raw_barcodes (required)
    (3, 1, TRUE), (3, 2, FALSE), (3, 3, TRUE),
    -- Artifact Type: FASTA - Filepath Types: raw_fasta (required), raw_qual (required)
    (4, 18, TRUE), (4, 19, TRUE),
    -- Artifact Type: per_sample_FASTQ - Filepath Types: raw_forward_seqs (required), raw_reverse_seqs (optional)
    (5, 1, TRUE), (5, 2, FALSE),
    -- Artifact Type: Demultiplexed - Filepath Types: preprocessed_fasta (required), preprocessed_fastq (required), preprocessed_demux (optional), log (optional)
    (6, 4, TRUE), (6, 5, TRUE), (6, 6, FALSE), (6, 13, FALSE),
    -- Artifact Type: BIOM - Filepath Types: biom (required), directory (optional), log (optional)
    (7, 7, TRUE), (7, 8, FALSE), (7, 13, FALSE);

-- Feb 3, 2016
-- Add default workflows and store user workflows in the DB

-- The table command_parameter had as primary key the tuple (command_id, parameter_name)
-- This was enough previously, but now we need to reference this table so we can
-- link the parameter with the artifact types in case that the type of the
-- parameter is "artifact". Thus, we change the primary key to be a single bigserial
-- for simplicity
ALTER TABLE qiita.command_parameter DROP CONSTRAINT idx_command_parameter_0;
ALTER TABLE qiita.command_parameter ADD command_parameter_id bigserial  NOT NULL;
ALTER TABLE qiita.command_parameter ADD CONSTRAINT pk_command_parameter PRIMARY KEY ( command_parameter_id ) ;
ALTER TABLE qiita.command_parameter ADD CONSTRAINT idx_command_parameter_0 UNIQUE ( command_id, parameter_name ) ;

-- In case that the parameter is of type "artifact" this table holds which
-- specific set of artifact types the command accepts
CREATE TABLE qiita.parameter_artifact_type (
    command_parameter_id bigserial  NOT NULL,
    artifact_type_id     bigint     NOT NULL,
    CONSTRAINT idx_parameter_artifact_type PRIMARY KEY ( command_parameter_id, artifact_type_id )
 ) ;
CREATE INDEX idx_parameter_artifact_type_param_id ON qiita.parameter_artifact_type ( command_parameter_id ) ;
CREATE INDEX idx_parameter_artifact_type_type_id ON qiita.parameter_artifact_type ( artifact_type_id ) ;
ALTER TABLE qiita.parameter_artifact_type ADD CONSTRAINT fk_parameter_artifact_type FOREIGN KEY ( command_parameter_id ) REFERENCES qiita.command_parameter( command_parameter_id )    ;
ALTER TABLE qiita.parameter_artifact_type ADD CONSTRAINT fk_parameter_artifact_type_0 FOREIGN KEY ( artifact_type_id ) REFERENCES qiita.artifact_type( artifact_type_id )    ;

-- In case that the command outputs a set of artifacts (including len(set) = 1),
-- this table holds which are the types of those artifacts
CREATE TABLE qiita.command_output (
    command_output_id    bigserial  NOT NULL,
    name                 varchar    NOT NULL,
    command_id           bigint     NOT NULL,
    artifact_type_id     bigint     NOT NULL,
    CONSTRAINT pk_command_output PRIMARY KEY ( command_output_id ),
    CONSTRAINT idx_command_output UNIQUE ( name, command_id )
 ) ;
CREATE INDEX idx_command_output_cmd_id ON qiita.command_output ( command_id ) ;
CREATE INDEX idx_command_output_type_id ON qiita.command_output ( artifact_type_id ) ;
ALTER TABLE qiita.command_output ADD CONSTRAINT fk_command_output FOREIGN KEY ( command_id ) REFERENCES qiita.software_command( command_id )    ;
ALTER TABLE qiita.command_output ADD CONSTRAINT fk_command_output_0 FOREIGN KEY ( artifact_type_id ) REFERENCES qiita.artifact_type( artifact_type_id )    ;

-- The default workflows of a software (plugin) are represented using a graph in
-- which the nodes are the commands and default parameter set used
-- and edges represent the job dependency.

-- The table default_workflow links each software with its set of default workflows
CREATE TABLE qiita.default_workflow (
    default_workflow_id  bigserial  NOT NULL,
    software_id          bigint     NOT NULL,
    name                 varchar    NOT NULL,
    CONSTRAINT pk_default_workflow PRIMARY KEY ( default_workflow_id ),
    CONSTRAINT idx_default_workflow UNIQUE ( software_id, name )
 ) ;
CREATE INDEX idx_default_workflow_software ON qiita.default_workflow ( software_id ) ;
ALTER TABLE qiita.default_workflow ADD CONSTRAINT fk_default_workflow_software FOREIGN KEY ( software_id ) REFERENCES qiita.software( software_id )    ;

-- The table default_workflow_node stores the nodes information from the
-- workflow graph
CREATE TABLE qiita.default_workflow_node (
    default_workflow_node_id  bigserial  NOT NULL,
    default_workflow_id       bigint     NOT NULL,
    command_id                bigint     NOT NULL,
    default_parameter_set_id  bigint     NOT NULL,
    CONSTRAINT pk_default_workflow_command PRIMARY KEY ( default_workflow_node_id )
 ) ;
CREATE INDEX idx_default_workflow_command_cmd_id ON qiita.default_workflow_node ( command_id ) ;
CREATE INDEX idx_default_workflow_command_dflt_param_id ON qiita.default_workflow_node ( default_parameter_set_id ) ;
CREATE INDEX idx_default_workflow_command_dflt_wf_id ON qiita.default_workflow_node ( default_workflow_id ) ;
ALTER TABLE qiita.default_workflow_node ADD CONSTRAINT fk_default_workflow_command FOREIGN KEY ( command_id ) REFERENCES qiita.software_command( command_id )    ;
ALTER TABLE qiita.default_workflow_node ADD CONSTRAINT fk_default_workflow_command_0 FOREIGN KEY ( default_parameter_set_id ) REFERENCES qiita.default_parameter_set( default_parameter_set_id )    ;
ALTER TABLE qiita.default_workflow_node ADD CONSTRAINT fk_default_workflow_command_1 FOREIGN KEY ( default_workflow_id ) REFERENCES qiita.default_workflow( default_workflow_id )    ;

-- The table default_workflow_edge stores the edge of the workflow graph
CREATE TABLE qiita.default_workflow_edge (
    default_workflow_edge_id  bigserial  NOT NULL,
    parent_id                 bigint     NOT NULL,
    child_id                  bigint     NOT NULL,
    CONSTRAINT pk_default_workflow_edge PRIMARY KEY ( default_workflow_edge_id )
 ) ;
CREATE INDEX idx_default_workflow_edge_parent ON qiita.default_workflow_edge ( parent_id ) ;
CREATE INDEX idx_default_workflow_edge_child ON qiita.default_workflow_edge ( child_id ) ;
ALTER TABLE qiita.default_workflow_edge ADD CONSTRAINT fk_default_workflow_edge FOREIGN KEY ( parent_id ) REFERENCES qiita.default_workflow_node( default_workflow_node_id )    ;
ALTER TABLE qiita.default_workflow_edge ADD CONSTRAINT fk_default_workflow_edge_0 FOREIGN KEY ( child_id ) REFERENCES qiita.default_workflow_node( default_workflow_node_id )    ;

-- The table default_workflow_edge_connections stores the metadata information
-- about the edges. Specifically, it stores which outputs are connected to
-- which inputs across commands in the default workflow command.
CREATE TABLE qiita.default_workflow_edge_connections (
    default_workflow_edge_id  bigint  NOT NULL,
    parent_output_id          bigint  NOT NULL,
    child_input_id            bigint  NOT NULL,
    CONSTRAINT idx_default_workflow_edge_connections PRIMARY KEY ( default_workflow_edge_id, parent_output_id, child_input_id )
 ) ;
CREATE INDEX idx_default_workflow_edge_connections_parent ON qiita.default_workflow_edge_connections ( parent_output_id ) ;
CREATE INDEX idx_default_workflow_edge_connections_child ON qiita.default_workflow_edge_connections ( child_input_id ) ;
CREATE INDEX idx_default_workflow_edge_connections_edge ON qiita.default_workflow_edge_connections ( default_workflow_edge_id ) ;
ALTER TABLE qiita.default_workflow_edge_connections ADD CONSTRAINT fk_default_workflow_edge_connections FOREIGN KEY ( parent_output_id ) REFERENCES qiita.command_output( command_output_id )    ;
ALTER TABLE qiita.default_workflow_edge_connections ADD CONSTRAINT fk_default_workflow_edge_connections_0 FOREIGN KEY ( child_input_id ) REFERENCES qiita.command_parameter( command_parameter_id )    ;
ALTER TABLE qiita.default_workflow_edge_connections ADD CONSTRAINT fk_default_workflow_edge_connections_1 FOREIGN KEY ( default_workflow_edge_id ) REFERENCES qiita.default_workflow_edge( default_workflow_edge_id )    ;

-- The table qiita.processing_job_workflow holds the workflow actually executed
-- by the user. We allow the user to name the workflow for easier reference
CREATE TABLE qiita.processing_job_workflow (
    processing_job_workflow_id     bigserial      NOT NULL,
    email                          varchar      NOT NULL,
    name                           varchar  ,
    CONSTRAINT pk_processing_job_workflow PRIMARY KEY ( processing_job_workflow_id )
 ) ;
CREATE INDEX idx_processing_job_workflow ON qiita.processing_job_workflow ( email ) ;
ALTER TABLE qiita.processing_job_workflow ADD CONSTRAINT fk_processing_job_workflow FOREIGN KEY ( email ) REFERENCES qiita.qiita_user( email )    ;

-- The processing_job_workflow_root connects the processing_job_workflow with
-- it's initial set of jobs. From this jobs, we can trace down the rest of the
-- workflow
CREATE TABLE qiita.processing_job_workflow_root (
    processing_job_workflow_id     bigint    NOT NULL,
    processing_job_id              uuid      NOT NULL,
    CONSTRAINT idx_processing_job_workflow_root_0 PRIMARY KEY ( processing_job_workflow_id, processing_job_id )
 ) ;
CREATE INDEX idx_processing_job_workflow_root_wf ON qiita.processing_job_workflow_root ( processing_job_workflow_id ) ;
CREATE INDEX idx_processing_job_workflow_root_job ON qiita.processing_job_workflow_root ( processing_job_id ) ;
ALTER TABLE qiita.processing_job_workflow_root ADD CONSTRAINT fk_processing_job_workflow_root_job FOREIGN KEY ( processing_job_workflow_id ) REFERENCES qiita.processing_job_workflow( processing_job_workflow_id )    ;
ALTER TABLE qiita.processing_job_workflow_root ADD CONSTRAINT fk_processing_job_workflow_root_wf FOREIGN KEY ( processing_job_id ) REFERENCES qiita.processing_job( processing_job_id )    ;

-- the table parent_processing_job stores the edges between the
-- different processing jobs. The specific connections are encoded in the
-- processing_job's command_parameters attribute (JSON)
CREATE TABLE qiita.parent_processing_job (
    parent_id            uuid  NOT NULL,
    child_id             uuid  NOT NULL,
    CONSTRAINT idx_parent_processing_job PRIMARY KEY ( parent_id, child_id )
 ) ;
CREATE INDEX idx_parent_processing_job_parent ON qiita.parent_processing_job ( parent_id ) ;
CREATE INDEX idx_parent_processing_job_child ON qiita.parent_processing_job ( child_id ) ;
ALTER TABLE qiita.parent_processing_job ADD CONSTRAINT fk_parent_processing_job_parent FOREIGN KEY ( parent_id ) REFERENCES qiita.processing_job( processing_job_id )    ;
ALTER TABLE qiita.parent_processing_job ADD CONSTRAINT fk_parent_processing_job_child FOREIGN KEY ( child_id ) REFERENCES qiita.processing_job( processing_job_id )    ;

-- The workflows need to connect the different outputs of a processing job with
-- the inputs of the next processing job. The following table holds which
-- artifact was generated in each named output. So we can backtrack and perform
-- the correct connections when executing the workflow. Note that this information
-- is only needed for the wokflows, so there is no necessity to populate the
-- table with all the artifacts that has been already generated. Furthermore,
-- there is no way to retrieve this information once the job has been executed
-- and be 100% sure that we are connecting the jobs and the artifacts correctly
CREATE TABLE qiita.artifact_output_processing_job (
    artifact_id          bigint  NOT NULL,
    processing_job_id    uuid    NOT NULL,
    command_output_id    bigint  NOT NULL
 ) ;
CREATE INDEX idx_artifact_output_processing_job_artifact ON qiita.artifact_output_processing_job ( artifact_id ) ;
CREATE INDEX idx_artifact_output_processing_job_job ON qiita.artifact_output_processing_job ( processing_job_id ) ;
CREATE INDEX idx_artifact_output_processing_job_cmd ON qiita.artifact_output_processing_job ( command_output_id ) ;
ALTER TABLE qiita.artifact_output_processing_job ADD CONSTRAINT fk_artifact_output_processing_job_artifact FOREIGN KEY ( artifact_id ) REFERENCES qiita.artifact( artifact_id )    ;
ALTER TABLE qiita.artifact_output_processing_job ADD CONSTRAINT fk_artifact_output_processing_job_job FOREIGN KEY ( processing_job_id ) REFERENCES qiita.processing_job( processing_job_id )    ;
ALTER TABLE qiita.artifact_output_processing_job ADD CONSTRAINT fk_artifact_output_processing_job_cmd FOREIGN KEY ( command_output_id ) REFERENCES qiita.command_output( command_output_id )    ;

-- In order to successfully represent the current status of a job,
-- we need to identify if the job is part of a workflow in construction
-- and if the job is waiting for a previous job to finish in order to be executed
INSERT INTO qiita.processing_job_status (processing_job_status, processing_job_status_description)
    VALUES ('in_construction', 'The job is one of the source nodes of a workflow that is in construction'),
           ('waiting', 'The job is waiting for a previous job in the workflow to be completed in order to be executed.');

-- In order to keep better track of the jobs that we are waiting for
-- we add another json to the processing_job table
ALTER TABLE qiita.processing_job ADD pending json  ;

-- Populate the newly created tables
DO $do$
DECLARE
    in_slq_param_id        bigint;
    in_sl_param_id         bigint;
    in_po_param_id         bigint;
    dflt_slq_id            bigint;
    dflt_sl_id             bigint;
    dflt_per_sample_id     bigint;
    dflt_po_id             bigint;
BEGIN
    -- Add the artifact type information for the input parameters for the commands
    -- command_id = 1 -> Split libraries FASTQ
    SELECT command_parameter_id FROM qiita.command_parameter
        WHERE command_id = 1 AND parameter_name = 'input_data'
        INTO in_slq_param_id;

    -- Split libraries FASTQ supports FASTQ (3) and per_sample_FASTQ (5)
    INSERT INTO qiita.parameter_artifact_type (command_parameter_id, artifact_type_id)
        VALUES (in_slq_param_id, 3), (in_slq_param_id, 5);

    -- command_id = 2 -> Split libraries
    SELECT command_parameter_id FROM qiita.command_parameter
        WHERE command_id = 2 AND parameter_name = 'input_data'
        INTO in_sl_param_id;

    -- Split libraries supports SFF (1), FASTA_Sanger (2), FASTA (4)
    INSERT INTO qiita.parameter_artifact_type (command_parameter_id, artifact_type_id)
        VALUES (in_sl_param_id, 1), (in_sl_param_id, 2), (in_sl_param_id, 4);

    -- command_id = 3 -> Pick closed-reference OTUs
    SELECT command_parameter_id FROM qiita.command_parameter
        WHERE command_id = 3 AND parameter_name = 'input_data'
        INTO in_po_param_id;

    -- Pick closed-reference OTUs supports Demultiplexed (6)
    INSERT INTO qiita.parameter_artifact_type (command_parameter_id, artifact_type_id)
        VALUES (in_po_param_id, 6);


    -- Add the output information for each command
    INSERT INTO qiita.command_output (name, command_id, artifact_type_id)
        VALUES ('demultiplexed', 1, 6), ('demultiplexed', 2, 6), ('OTU table', 3, 7);


    -- Add the default workflow for the target gene pipeline.
    -- We are going to create three different default workflows for the
    -- target gene plugin:
    --   1) FASTQ upstream workflow: split_libraries_fastq.py + OTU picking
    --   2) FASTA upstream workflow: split_libraries.py + OTU picking
    --   3) Per sample FASTQ upstream workflow:
    --      split_libraries_fastq.py + OTU picking using per sample fastq parameters
    -- In order to choose the default parameters set, we are going to choose
    -- the one with minimum id. The reason for this is that in the live system
    -- there are default parameter set that were added manually, so we don't
    -- know the ids for those parameter set. Note that we do know
    -- the command id because they're inserted in patch 33.sql, and that is
    -- the only way of adding commands at this point.

    -- Insert default workflow
    INSERT INTO qiita.default_workflow (software_id, name)
        VALUES (1, 'FASTQ upstream workflow'),
               (1, 'FASTA upstream workflow'),
               (1, 'Per sample FASTQ upstream workflow');

    -- Retrieve all the ids of the default parameter set that we need
    SELECT min(default_parameter_set_id)
        FROM qiita.default_parameter_set
        WHERE command_id = 1
        INTO dflt_slq_id;

    SELECT min(default_parameter_set_id)
        FROM qiita.default_parameter_set
        WHERE command_id = 2
        INTO dflt_sl_id;

    SELECT min(default_parameter_set_id)
        FROM qiita.default_parameter_set
        WHERE command_id = 1 AND parameter_set->>'barcode_type' = 'not-barcoded'
        INTO dflt_per_sample_id;

    SELECT min(default_parameter_set_id)
        FROM qiita.default_parameter_set
        WHERE command_id = 3
        INTO dflt_po_id;

    -- We need 2 nodes per workflow -> 6 nodes
    INSERT INTO qiita.default_workflow_node (default_workflow_id, command_id, default_parameter_set_id)
        VALUES (1, 1, dflt_slq_id), (1, 3, dflt_po_id),
               (2, 2, dflt_sl_id), (2, 3, dflt_po_id),
               (3, 1, dflt_per_sample_id), (3, 3, dflt_po_id);

    -- We need 1 edge per workflow -> 3 edges
    INSERT INTO qiita.default_workflow_edge (parent_id, child_id)
        VALUES (1, 2), (3, 4), (5, 6);

    INSERT INTO qiita.default_workflow_edge_connections (default_workflow_edge_id, parent_output_id, child_input_id)
        VALUES (1, 1, in_po_param_id),
               (2, 2, in_po_param_id),
               (3, 1, in_po_param_id);

END $do$;

-- Create a function to return all the edges of a processing_job_workflow
CREATE FUNCTION qiita.get_processing_workflow_edges(wf_id bigint) RETURNS SETOF qiita.parent_processing_job AS $$
BEGIN
    RETURN QUERY WITH RECURSIVE edges AS (
        SELECT parent_id, child_id
        FROM qiita.parent_processing_job
        WHERE parent_id IN (SELECT processing_job_id
                            FROM qiita.processing_job_workflow_root
                            WHERE processing_job_workflow_id = wf_id)
      UNION
          SELECT p.parent_id, p.child_id
        FROM qiita.parent_processing_job p
            JOIN edges e ON (e.child_id = p.parent_id)
    )
    SELECT DISTINCT parent_id, child_id
        FROM edges;
END
$$ LANGUAGE plpgsql;

-- Mar 7, 2016
-- Add reference_id and command_id of the input file to jobs

-- Changes to tables

ALTER TABLE qiita.job ADD input_file_reference_id bigint;

ALTER TABLE qiita.job ADD input_file_software_command_id bigint;

CREATE INDEX idx_job_0 ON qiita.job ( input_file_reference_id ) ;

CREATE INDEX idx_job_1 ON qiita.job ( input_file_software_command_id ) ;

ALTER TABLE qiita.job ADD CONSTRAINT fk_job_reference FOREIGN KEY ( input_file_reference_id ) REFERENCES qiita.reference( reference_id );

ALTER TABLE qiita.job ADD CONSTRAINT fk_job_software_command FOREIGN KEY ( input_file_software_command_id ) REFERENCES qiita.software_command( command_id );

-- Change values:
-- input_file_reference_id can be = 1 as it's only needed for job processing
-- input_file_software_command_id = 3 as it's close reference picking.

UPDATE qiita.job SET input_file_reference_id = 1;
ALTER TABLE qiita.job ALTER COLUMN input_file_reference_id SET NOT NULL;

UPDATE qiita.job SET input_file_software_command_id = 3;
ALTER TABLE qiita.job ALTER COLUMN input_file_software_command_id SET NOT NULL;

-- Mar 12, 2016
-- Add software_type table. This new table allows us to have different types of
-- plugins. Here, we will introduce a new type, the "type plugin", and define
-- the previous type as the "processing plugin" type. The new group "type plugin"
-- define plugins that do not perform any processing on the artifacts but they
-- are able to validate that they're correct and generate their summary page.
-- These new plugins are special. They are not directly visible by the end Qiita
-- user but they are useful to plugin developers so they do not need to re-define
-- types if they already exist. This way, multiple plugins can share the same
-- type of artifacts without depending in another "processing" plugin.

-- Add the type HTML summary to the list of supported filepath types
-- Note that we are not linking this filepath type with any specific artifact
-- type. The reason is that all artifacts should have it and users are not
-- allowed to upload this file, since it is internally generated
INSERT INTO qiita.filepath_type (filepath_type) VALUES ('html_summary');

-- Create the new table to hold the software types
CREATE TABLE qiita.software_type (
    software_type_id     bigserial   NOT NULL,
    software_type        varchar     NOT NULL,
    description          varchar     NOT NULL,
    CONSTRAINT pk_software_type PRIMARY KEY ( software_type_id )
 ) ;

-- Add the FK to the software table
ALTER TABLE qiita.software ADD software_type_id bigint;
CREATE INDEX idx_software_type ON qiita.software ( software_type_id ) ;
ALTER TABLE qiita.software ADD CONSTRAINT fk_software_software_type FOREIGN KEY ( software_type_id ) REFERENCES qiita.software_type( software_type_id )    ;

-- The software (plugins) of type "type plugin" need to hold which types do they define
CREATE TABLE qiita.software_artifact_type (
    software_id          bigint  NOT NULL,
    artifact_type_id     bigint  NOT NULL,
    CONSTRAINT idx_software_artifact_type PRIMARY KEY ( software_id, artifact_type_id )
 ) ;
CREATE INDEX idx_software_artifact_type_artifact ON qiita.software_artifact_type ( artifact_type_id ) ;
CREATE INDEX idx_software_artifact_type_software ON qiita.software_artifact_type ( software_id ) ;
COMMENT ON TABLE qiita.software_artifact_type IS 'In case that the software is of type "type plugin", it holds the artifact types that such software can validate and generate the summary.';
ALTER TABLE qiita.software_artifact_type ADD CONSTRAINT fk_software_artifact_type_at FOREIGN KEY ( artifact_type_id ) REFERENCES qiita.artifact_type( artifact_type_id )    ;
ALTER TABLE qiita.software_artifact_type ADD CONSTRAINT fk_software_artifact_type_sw FOREIGN KEY ( software_id ) REFERENCES qiita.software( software_id )    ;

-- The new type of plugins have a new command, create-artifact, that given
-- a prep template, the artifact type and the files to be added, validate the
-- files and perform any needed correction to add the files to the system. An
-- example of this processing will be adding new BIOM tables. With the information
-- in the prep template, the plugin can rename the samples in the biom table
-- to match the sample names in the prep template.
CREATE TABLE qiita.prep_template_processing_job (
    prep_template_id     bigint  NOT NULL,
    processing_job_id    uuid    NOT NULL,
    CONSTRAINT idx_prep_template_processing_job PRIMARY KEY ( prep_template_id, processing_job_id )
 ) ;
CREATE INDEX idx_prep_template_processing_job_pt_id ON qiita.prep_template_processing_job ( prep_template_id ) ;
CREATE INDEX idx_prep_template_processing_job_job ON qiita.prep_template_processing_job ( processing_job_id ) ;
ALTER TABLE qiita.prep_template_processing_job ADD CONSTRAINT fk_prep_template_processing_job_pt FOREIGN KEY ( prep_template_id ) REFERENCES qiita.prep_template( prep_template_id )    ;
ALTER TABLE qiita.prep_template_processing_job ADD CONSTRAINT fk_prep_template_processing_job_job FOREIGN KEY ( processing_job_id ) REFERENCES qiita.processing_job( processing_job_id )    ;

-- Populate the table software_type with the 2 types of plugins
INSERT INTO qiita.software_type (software_type, description)
    VALUES ('artifact transformation', 'A plugin that performs some kind of processing/transformation/manipulation over an artifact.'),
           ('artifact definition', 'A plugin that defines new artifact types.');

-- All the software present in the system belong to type 1 (artifact transformation)
UPDATE qiita.software SET software_type_id = 1;
-- Setting up NOT NULL attribute here since the value was null until the previous statement
ALTER TABLE qiita.software ALTER COLUMN software_type_id SET NOT NULL;

-- We are going to create 2 new type plugins.
-- The first one will define the type BIOM, while the other one will define
-- all the types needed for TARGET_GENE. This separation is better since BIOM
-- is a special type that even Qiita understands since it is the input for
-- analysis and almost all plugins will need. However, the rest of the types
-- are specific for the target gene plugin.
INSERT INTO qiita.software (name, version, description, environment_script, start_script, software_type_id)
    VALUES ('BIOM type', '2.1.4 - Qiime2', 'The Biological Observation Matrix format', '. activate qtp-biom', 'start_biom', 2),
           ('Target Gene type', '0.1.0', 'Target gene artifact types plugin', 'source activate qiita', 'start_target_gene_types', 2);
-- Add BIOM publication
INSERT INTO qiita.publication (doi, pubmed_id) VALUES ('10.1186/2047-217X-1-7', '23587224');
INSERT INTO qiita.software_publication (software_id, publication_doi) VALUES (2, '10.1186/2047-217X-1-7');

-- Add the commands - these will not be visible by the user as they're used internally
INSERT INTO qiita.software_command (software_id, name, description) VALUES
    -- This will have the ID 4
    (2, 'Validate', 'Validates a new artifact of type BIOM'),
    -- This will have the ID 5
    (2, 'Generate HTML summary', 'Generates the HTML summary of a BIOM artifact'),
    -- This will have the ID 6
    (3, 'Validate', 'Validates a new artifact of the given target gene type'),
    -- This will have the ID 7
    (3, 'Generate HTML summary', 'Generates the HTML summary of a given target gene type artifact');

-- Add the parameters - in this case all are required and they will be filled
-- internally by the system, so there is no need to populate the default_parameter_set
-- table, because there are no parameters that are not required.
INSERT INTO qiita.command_parameter (command_id, parameter_name, parameter_type, required)
    VALUES (4, 'template', 'prep_template', True),
           (4, 'files', 'string', True),
           (4, 'artifact_type', 'string', True),
           (5, 'input_data', 'artifact', True),
           (6, 'template', 'prep_template', True),
           (6, 'files', 'string', True),
           (6, 'artifact_type', 'string', True),
           (7, 'input_data', 'artifact', True);

-- Relate the artifact_type with the software that defines it
DO $do$
DECLARE
    biom_id  bigint;
    at_id    bigint;
BEGIN
    -- First the BIOM
    SELECT artifact_type_id FROM qiita.artifact_type WHERE artifact_type = 'BIOM' INTO biom_id;
    INSERT INTO qiita.software_artifact_type (software_id, artifact_type_id)
        VALUES (2, biom_id);

    -- The the rest
    FOR at_id IN
        SELECT artifact_type_id FROM qiita.artifact_type WHERE artifact_type <> 'BIOM'
    LOOP
        INSERT INTO qiita.software_artifact_type (software_id, artifact_type_id)
            VALUES (3, at_id);
    END LOOP;
END $do$;

-- Mar 28, 2016
INSERT INTO qiita.filepath_type (filepath_type) VALUES ('tgz');
