-- Drop the current options storage and create new table
ALTER TABLE qiita.command DROP COLUMN input;

ALTER TABLE qiita.command DROP COLUMN required;

ALTER TABLE qiita.command DROP COLUMN optional;

ALTER TABLE qiita.command DROP COLUMN output;

CREATE TABLE qiita.command_option ( 
	command_option_id    bigserial  NOT NULL,
	command_id           bigint  NOT NULL,
	option               varchar  NOT NULL,
	description          varchar  NOT NULL,
	required             bool  NOT NULL,
	setable              bool DEFAULT 'False' NOT NULL,
	def                  varchar,
	input_type           varchar  NOT NULL,
	filepath_type_id     bigint  ,
	triggers             bigint[]  ,
	CONSTRAINT pk_command_option PRIMARY KEY ( command_option_id )
 ) ;

CREATE INDEX idx_command_option ON qiita.command_option ( command_id ) ;

CREATE INDEX idx_command_option_0 ON qiita.command_option ( filepath_type_id ) ;

COMMENT ON TABLE qiita.command_option IS 'Options available for each command';

COMMENT ON COLUMN qiita.command_option.option IS 'The option, e.g. -o';

COMMENT ON COLUMN qiita.command_option.description IS 'Text description of the option';

COMMENT ON COLUMN qiita.command_option.required IS 'Whether this option is required to run';

COMMENT ON COLUMN qiita.command_option.def IS 'Default value for the command';

COMMENT ON COLUMN qiita.command_option.input_type IS 'Type of value expected, e.g. int, float, filepath, etc.';

COMMENT ON COLUMN qiita.command_option.filepath_type_id IS 'If input_type is filepath, type required for input';

COMMENT ON COLUMN qiita.command_option.triggers IS 'Options made required by setting this one (command_option_ids)';

ALTER TABLE qiita.command_option ADD CONSTRAINT fk_command_option_command_id FOREIGN KEY ( command_id ) REFERENCES qiita.command ( command_id )    ;

ALTER TABLE qiita.command_option ADD CONSTRAINT fk_command_fp_type_id FOREIGN KEY ( filepath_type_id ) REFERENCES qiita.filepath_type( filepath_type_id )    ;

-- Populate new table with options
INSERT INTO qiita.command_option (command_id, option, description, required, setable, def, input_type, filepath_type_id, triggers) VALUES
(1, '--otu_table_fp', 'The input OTU table', TRUE, FALSE, NULL, 'filepath', 7, NULL),
(1, '--mapping_fp', 'The mapping table filepath, if mapping category given', FALSE, FALSE, NULL, 'filepath', 9, NULL),
(1, '--mapping_category', 'Metadata category to map to', FALSE, TRUE, NULL, 'text', NULL, '{2}'),
(1, '--sort', 'Whether to sort the resulting output', FALSE, TRUE, NULL, 'bool', NULL, NULL),
(1, '--output_dir', 'Directory to output to', TRUE, FALSE, NULL, 'filepath', 8, NULL),
(2, '--otu_table_fp', 'The input OTU table', TRUE, FALSE, NULL, 'filepath', 7, NULL),
(2, '--mapping_fp', 'The mapping table filepath', TRUE, FALSE, NULL, 'filepath', 9, NULL),
(2, '--tree_fp', 'The filepath to the reference tree', FALSE, TRUE, NULL, 'filepath', 12, NULL),
(2, '--color_by_all_fields', 'Plots will have coloring for all mapping fields', FALSE, TRUE, NULL, 'bool', NULL, NULL),
(2, '--seqs_per_sample', 'Depth of coverage for even sampling', FALSE, TRUE, NULL, 'int', NULL, NULL),
(2, '--output_dir', 'Directory to output to', TRUE, FALSE, NULL, 'filepath', 8, NULL),
(3, '--otu_table_fp', 'The input OTU table', TRUE, FALSE, NULL, 'filepath', 7, NULL),
(3, '--mapping_fp', 'The mapping table filepath', TRUE, FALSE, NULL, 'filepath', 9, NULL),
(3, '--tree_fp', 'The filepath to the reference tree', FALSE, TRUE, NULL, 'filepath', 12, NULL),
(3, '--num_steps', 'Number of steps (or rarefied OTU table sizes) to make between min and max counts', FALSE, TRUE, '10', 'int', NULL, NULL),
(3, '--min_rare_depth', 'The lower limit of rarefaction depths', FALSE, TRUE, '10', 'int', NULL, NULL),
(3, '--max_rare_depth', 'The upper limit of rarefaction depths', FALSE, TRUE, NULL, 'int', NULL, NULL),
(2, '--retain_intermediate_files', 'retain intermediate files: rarefied OTU tables (rarefaction) and alpha diversity results (alpha_div).', TRUE, FALSE, 'False', 'bool', NULL, NULL),
(3, '--output_dir', 'Directory to output to', TRUE, FALSE, NULL, 'filepath', 8, NULL);
