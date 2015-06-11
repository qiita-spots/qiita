-- June 11,, 2015
-- Adds portal type to analyses

ALTER TABLE qiita.analysis
ADD portal_type_id bigint NOT NULL DEFAULT 3;

ALTER TABLE qiita.analysis
ADD CONSTRAINT fk_analysis_portal
FOREIGN KEY (portal_type_id)
REFERENCES qiita.portal_type(portal_type_id);