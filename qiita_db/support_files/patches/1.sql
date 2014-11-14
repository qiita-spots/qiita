-- Nov 14, 2014
-- This patch adds to the database the tables needed for supporting environmental packages

-- The environmental package table
CREATE TABLE qiita.environmental_package ( 
	environmental_package_id bigserial  NOT NULL,
	name                 varchar  NOT NULL,
	CONSTRAINT pk_environmental_package PRIMARY KEY ( environmental_package_id )
 ) ;

COMMENT ON TABLE qiita.environmental_package IS 'Holds the information for each environmental package';

COMMENT ON COLUMN qiita.environmental_package.name IS 'Holds the name of the environmental package';

-- Which columns are required for each environmental package
CREATE TABLE qiita.environmental_package_columns ( 
	environmental_package_id bigint  NOT NULL,
	column_name          varchar  NOT NULL,
	column_type          varchar  NOT NULL,
	CONSTRAINT pk_environmental_package_columns PRIMARY KEY ( environmental_package_id, column_name, column_type )
 ) ;

CREATE INDEX idx_environmental_package_columns ON qiita.environmental_package_columns ( environmental_package_id ) ;

COMMENT ON TABLE qiita.environmental_package_columns IS 'Holds the required columns for the environmental packages';

COMMENT ON COLUMN qiita.environmental_package_columns.column_name IS 'Holds the name of the required column';

COMMENT ON COLUMN qiita.environmental_package_columns.column_type IS 'Holds the type of the required column';


-- The 1 to N relationship between the study and the environmental packages
CREATE TABLE qiita.study_environmental_package ( 
	study_id             bigint  NOT NULL,
	environmental_package_id bigint  NOT NULL,
	CONSTRAINT pk_study_environmental_package PRIMARY KEY ( study_id, environmental_package_id )
 ) ;

CREATE INDEX idx_study_environmental_package ON qiita.study_environmental_package ( study_id ) ;

CREATE INDEX idx_study_environmental_package_0 ON qiita.study_environmental_package ( environmental_package_id ) ;

COMMENT ON TABLE qiita.study_environmental_package IS 'Holds the 1 to many relationship between the study and the environmental package.';

ALTER TABLE qiita.environmental_package_columns ADD CONSTRAINT fk_environmental_package_columns FOREIGN KEY ( environmental_package_id ) REFERENCES qiita.environmental_package( environmental_package_id )    ;

ALTER TABLE qiita.study_environmental_package ADD CONSTRAINT fk_study_environmental_package FOREIGN KEY ( study_id ) REFERENCES qiita.study( study_id )    ;

ALTER TABLE qiita.study_environmental_package ADD CONSTRAINT fk_study_environmental_package_0 FOREIGN KEY ( environmental_package_id ) REFERENCES qiita.environmental_package( environmental_package_id )    ;

-- We insert the environmental packages that we know
INSERT INTO qiita.environmental_package (name) VALUES ('air'), ('built environment'), ('host-associated'), ('human-amniotic-fluid'), ('human-associated'), ('human-blood'), ('human-gut'), ('human-oral'), ('human-skin'), ('human-urine'), ('human-vaginal'), ('microbial mat/biofilm'), ('miscellaneous natural or artificial environment'), ('plant-associated'), ('sediment'), ('soil'), ('wastewater/sludge'), ('water');