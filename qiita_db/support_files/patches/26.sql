-- June 11,, 2015
-- Adds ability to associate Analyses and Studies with multiple portals
-- and associates all existing studies + analyses with proper portal(s).

-- Remove existing portals and replace with more relevant ones
UPDATE qiita.study SET portal_type_id = 2 WHERE portal_type_id = 3;

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

-- Add new default analyses for other portals
DO $do$
DECLARE
	eml varchar;
	aid bigint;
	portal bigint;
BEGIN
FOR eml IN
	SELECT email FROM qiita.qiita_user
LOOP
	FOR portal IN
		SELECT portal_type_id from qiita.portal_type WHERE portal_type_id != 1
	LOOP
		INSERT INTO qiita.analysis (email, name, description, dflt, analysis_status_id) VALUES (eml, eml || '-dflt', 'dflt', true, 1) RETURNING analysis_id INTO aid;
		INSERT INTO qiita.analysis_workflow (analysis_id, step) VALUES (aid, 2);
		INSERT INTO qiita.analysis_portal (analysis_id, portal_type_id) VALUES (aid, portal);
	END LOOP;
END LOOP;
END $do$;

-- Move study portal info to it's own table, as one study can be in multiple portals
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

-- Attach all existing studies to the qiita portal and, if necessary, EMP portal
INSERT INTO qiita.study_portal (study_id, portal_type_id) SELECT s.study_id, s.portal_type_id FROM qiita.study s;

INSERT INTO qiita.study_portal (study_id, portal_type_id) SELECT s.study_id, 1 FROM qiita.study s WHERE s.portal_type_id != 1;

ALTER TABLE qiita.study DROP COLUMN portal_type_id