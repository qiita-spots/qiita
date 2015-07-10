-- July 10, 2015
-- Adds the connections between the default analysis from new user and
-- the portals.

DO $do$
DECLARE
    aid bigint;
    portal bigint;
    rec RECORD;
BEGIN

FOR portal IN
    SELECT portal_type_id FROM qiita.portal_type
LOOP
    FOR aid IN
        SELECT analysis_id
        FROM qiita.analysis
        WHERE dflt = TRUE
            AND name LIKE CONCAT('%-dflt-', portal)
            AND analysis_id NOT IN (
                SELECT analysis_id FROM qiita.analysis_portal)
    LOOP
        INSERT INTO qiita.analysis_portal (analysis_id, portal_type_id)
        VALUES (aid, portal);
    END LOOP;
END LOOP;
END $do$;
