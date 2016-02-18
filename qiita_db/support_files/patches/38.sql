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
	artifact_type_id     bigint  NOT NULL,
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
	name                 varchar  NOT NULL,
	command_id           bigint  NOT NULL,
	artifact_type_id     bigint  NOT NULL,
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
	software_id          bigint  NOT NULL,
	name                 varchar  NOT NULL,
	CONSTRAINT pk_default_workflow PRIMARY KEY ( default_workflow_id ),
	CONSTRAINT idx_default_workflow UNIQUE ( software_id, name )
 ) ;
CREATE INDEX idx_default_workflow_software ON qiita.default_workflow ( software_id ) ;
ALTER TABLE qiita.default_workflow ADD CONSTRAINT fk_default_workflow_software FOREIGN KEY ( software_id ) REFERENCES qiita.software( software_id )    ;

-- The table default_workflow_node stores the nodes information from the
-- workflow graph
CREATE TABLE qiita.default_workflow_node (
	default_workflow_node_id bigserial  NOT NULL,
	default_workflow_id  bigint  NOT NULL,
	command_id           bigint  NOT NULL,
	default_parameter_set_id bigint  NOT NULL,
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
	default_workflow_edge_id bigserial  NOT NULL,
	parent_id            bigint  NOT NULL,
	child_id             bigint  NOT NULL,
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
	default_workflow_edge_id bigint  NOT NULL,
	parent_output_id     bigint  NOT NULL,
	child_input_id       bigint  NOT NULL,
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
	processing_job_worfklow_id bigint  NOT NULL,
	email                varchar  NOT NULL,
	name                 varchar  ,
	CONSTRAINT pk_processing_job_workflow PRIMARY KEY ( processing_job_worfklow_id )
 ) ;
CREATE INDEX idx_processing_job_workflow ON qiita.processing_job_workflow ( email ) ;
ALTER TABLE qiita.processing_job_workflow ADD CONSTRAINT fk_processing_job_workflow FOREIGN KEY ( email ) REFERENCES qiita.qiita_user( email )    ;

-- The processing_job_workflow_roots connects the processing_job_workflow with
-- it's initial set of jobs. From this jobs, we can trace down the rest of the
-- workflow
CREATE TABLE qiita.processing_job_workflow_roots (
	processing_job_workflow_id 	bigint  NOT NULL,
	processing_job_id    		uuid  	NOT NULL,
	CONSTRAINT idx_processing_job_workflow_roots_0 PRIMARY KEY ( processing_job_workflow_id, processing_job_id )
 ) ;
CREATE INDEX idx_processing_job_workflow_roots_wf ON qiita.processing_job_workflow_roots ( processing_job_workflow_id ) ;
CREATE INDEX idx_processing_job_workflow_roots_job ON qiita.processing_job_workflow_roots ( processing_job_id ) ;
ALTER TABLE qiita.processing_job_workflow_roots ADD CONSTRAINT fk_processing_job_workflow_roots_job FOREIGN KEY ( processing_job_workflow_id ) REFERENCES qiita.processing_job_workflow( processing_job_worfklow_id )    ;
ALTER TABLE qiita.processing_job_workflow_roots ADD CONSTRAINT fk_processing_job_workflow_roots_wf FOREIGN KEY ( processing_job_id ) REFERENCES qiita.processing_job( processing_job_id )    ;

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

-- Populate the newly created tables
DO $do$
DECLARE
	in_slq_param_id		bigint;
	in_sl_param_id		bigint;
	in_po_param_id		bigint;
	dflt_slq_id			bigint;
	dflt_sl_id			bigint;
	dflt_per_sample_id	bigint;
	dflt_po_id			bigint;
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

END $do$
