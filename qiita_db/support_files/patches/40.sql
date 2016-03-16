-- Mar 12, 2016
-- Add software_type table. This new table allows us to have different types of
-- plugins. Here, we will introduce a new type, the "type plugin", and define
-- the previous type as the "processing plugin" type. The new group "type plugin"
-- define plugins that do not perform any processing on the artifacts but they
-- are able to validate that they're correct and generate they summary page.
-- These new plugins are special. They are not directly visible by the end Qiita
-- user by they are useful to plugin developers so they do not need to re-define
-- types if they already exist. This way, multiple plugins can share the same
-- type of artifacts without depending in another "processing" plugin.

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
    VALUES ('processing plugin', 'A plugin that performs some kind of processing over an artifact.'),
           ('type plugin', 'A plugin that defines new artifact types.');

-- All the software presente in the system belong to type 1 (processing plugin)
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
    VALUES ('BIOM type plugin', '2.1.4', 'The Biological Observation Matrix format', 'source activate qiita', 'start_biom', 2),
           ('Target Gene type plugin', '0.1.0', 'Target gene artifact types plugin', 'source activate qiita', 'start_target_gene_types', 2);
-- Add BIOM publication
INSERT INTO qiita.publication (doi, pubmed_id) VALUES ('10.1186/2047-217X-1-7', '23587224');
INSERT INTO qiita.software_publication (software_id, publication_doi) VALUES (2, '10.1186/2047-217X-1-7');

-- Add the commands - these will not be visible by the user as they're used internally
INSERT INTO qiita.software_command (software_id, name, description) VALUES
    -- This will have the ID 4
    (2, 'Create artifact', 'Creates a new artifact of type BIOM'),
    -- This will have the ID 5
    (2, 'Generate HTML summary', 'Generates the HTML summary of a BIOM artifact'),
    -- This will have the ID 6
    (3, 'Create artifact', 'Creates a new artifact of the given target gene type'),
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
END $do$
