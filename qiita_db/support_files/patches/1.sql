-- Nov 17, 2014
-- This patch adds to the database the structure needed for supporting environmental packages

CREATE TABLE qiita.environmental_package ( 
	environmental_package_name varchar  NOT NULL,
	metadata_table       varchar  NOT NULL,
	CONSTRAINT pk_environmental_package PRIMARY KEY ( environmental_package_name )
 ) ;

COMMENT ON COLUMN qiita.environmental_package.environmental_package_name IS 'The name of the environmental package';

COMMENT ON COLUMN qiita.environmental_package.metadata_table IS 'Contains the name of the table that contains the pre-defined metadata columns for the environmental package';

CREATE TABLE qiita.study_environmental_package ( 
	study_id             bigint  NOT NULL,
	environmental_package_name varchar  NOT NULL,
	CONSTRAINT pk_study_environmental_package PRIMARY KEY ( study_id, environmental_package_name )
 ) ;

CREATE INDEX idx_study_environmental_package ON qiita.study_environmental_package ( study_id ) ;

CREATE INDEX idx_study_environmental_package_0 ON qiita.study_environmental_package ( environmental_package_name ) ;

COMMENT ON TABLE qiita.study_environmental_package IS 'Holds the 1 to many relationship between the study and the environmental_package';

ALTER TABLE qiita.study_environmental_package ADD CONSTRAINT fk_study_environmental_package FOREIGN KEY ( study_id ) REFERENCES qiita.study( study_id )    ;

ALTER TABLE qiita.study_environmental_package ADD CONSTRAINT fk_study_environmental_package_0 FOREIGN KEY ( environmental_package_name ) REFERENCES qiita.environmental_package( environmental_package_name )    ;

-- We insert the environmental packages that we know
INSERT INTO qiita.environmental_package (environmental_package_name, metadata_table) VALUES
	('air', 'ep_air'),
	('built environment', 'ep_built_environment'),
	('host-associated', 'ep_host_associated'),
	('human-amniotic-fluid', 'ep_human_amniotic_fluid'),
	('human-associated', 'ep_human_associated'),
	('human-blood', 'ep_human_blood'),
	('human-gut', 'ep_human_gut'),
	('human-oral', 'ep_human_oral'),
	('human-skin', 'ep_human_skin'),
	('human-urine', 'ep_human_urine'),
	('human-vaginal', 'ep_human_vaginal'),
	('microbial mat/biofilm', 'ep_microbial_mat_biofilm'),
	('miscellaneous natural or artificial environment', 'ep_misc_artif'),
	('plant-associated', 'ep_plant_associated'),
	('sediment', 'ep_sediment'),
	('soil', 'ep_soil'),
	('wastewater/sludge', 'ep_wastewater_sludge'),
	('water', 'ep_water');
