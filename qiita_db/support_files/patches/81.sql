-- Jan 25, 2021
-- Add creation_timestamp and modification_timestamp for qiita.prep_template

ALTER TABLE qiita.prep_template ADD creation_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE qiita.prep_template ADD modification_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP;



-- Feb 23, 2021

-- a. Removing software_id from qiita.default_workflow and replacing it by a
--    table which will like different data_types with the default_workflow +
--    adding an active flag in case we need to deprecate default_workflows
ALTER TABLE qiita.default_workflow DROP software_id;
CREATE TABLE qiita.default_workflow_data_type (
	default_workflow_id	BIGINT NOT NULL,
	data_type_id BIGINT NOT NULL,
  CONSTRAINT fk_default_workflow_id FOREIGN KEY ( default_workflow_id ) REFERENCES qiita.default_workflow( default_workflow_id ),
  CONSTRAINT fk_data_type_id FOREIGN KEY ( data_type_id ) REFERENCES qiita.data_type ( data_type_id ),
  PRIMARY KEY(default_workflow_id, data_type_id)
);
ALTER TABLE qiita.default_workflow ADD active BOOL DEFAULT TRUE;

-- b. Remocing command_id from qiita.default_workflow_node and default_parameter_set as this information
--    can be accessed via the default_parameter object (the info is duplicated)
ALTER TABLE qiita.default_workflow_node DROP command_id;

-- c. Linking some of the data_types with the default_workflows; note that this
--    is fine for the test database but we are going to need to clean up and
--    insert the most up to date recommendations directly in qiita.ucsd.edu
INSERT INTO qiita.default_workflow_data_type (default_workflow_id, data_type_id) VALUES
  -- data types:
  --   1 | 16S
  --   2 | 18S
  --   3 | ITS
  (1, 1),
  (1, 2),
  (2, 2),
  (3, 3);
