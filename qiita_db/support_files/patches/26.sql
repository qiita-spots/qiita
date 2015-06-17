-- June 11,, 2015
-- Adds portal type to analyses

-- Remove existing portals and replace with more relevant ones
UPDATE qiita.study SET portal_type_id = 1 WHERE portal_type_id = 3;

DELETE FROM qiita.portal_type WHERE portal = 'QIIME_EMP';

UPDATE qiita.portal_type
SET portal = 'QIITA', portal_description = 'QIITA portal. Access to all data stored in database.'
WHERE portal_type_id = 1;

-- Add analysis portal info to it's own table, as one analysis can be in two portals
CREATE TABLE qiita.analysis_portal (
	analysis_id             bigint  NOT NULL,
	portal_type_id       bigint  NOT NULL,
	CONSTRAINT pk_analysis_portal PRIMARY KEY ( analysis_id, portal_type_id )
 );

CREATE INDEX idx_analysis_portal ON qiita.analysis_portal ( analysis_id );

CREATE INDEX idx_analysis_portal_0 ON qiita.analysis_portal ( portal_type_id );

ALTER TABLE qiita.analysis_portal ADD CONSTRAINT fk_analysis_portal FOREIGN KEY ( analysis_id ) REFERENCES qiita.analysis( analysis_id );

ALTER TABLE qiita.analysis_portal ADD CONSTRAINT fk_analysis_portal_0 FOREIGN KEY ( portal_type_id ) REFERENCES qiita.portal_type( portal_type_id );

COMMENT ON TABLE qiita.analysis_portal IS 'Controls what analyses are visible on what portals';

-- Attach all existing analyses to the qiita portal
INSERT INTO qiita.analysis_portal (analysis_id, portal_type_id) SELECT analysis_id, 1 FROM qiita.analysis;

-- Remove study portal info to it's own table, as one study can be in multiple portals
CREATE TABLE qiita.study_portal (
	study_id             bigint  NOT NULL,
	portal_type_id       bigint  NOT NULL,
	CONSTRAINT pk_study_portal PRIMARY KEY ( study_id, portal_type_id )
 );

CREATE INDEX idx_study_portal ON qiita.study_portal ( study_id );

CREATE INDEX idx_study_portal_0 ON qiita.study_portal ( portal_type_id );

COMMENT ON TABLE qiita.study_portal IS 'Controls what studies are visible on what portals';

ALTER TABLE qiita.study_portal ADD CONSTRAINT fk_study_portal FOREIGN KEY ( study_id ) REFERENCES qiita.study( study_id );

ALTER TABLE qiita.study_portal ADD CONSTRAINT fk_study_portal_0 FOREIGN KEY ( portal_type_id ) REFERENCES qiita.portal_type( portal_type_id );

INSERT INTO qiita.study_portal (study_id, portal_type_id) SELECT s.study_id, s.portal_type_id FROM qiita.study s;

ALTER TABLE qiita.study DROP COLUMN portal_type_id;