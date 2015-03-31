-- March 28, 2015
-- Add default analyses for all existing users
DO $do$
DECLARE 
	eml varchar;
BEGIN
FOR eml IN
	SELECT email FROM qiita.qiita_user
LOOP
	INSERT INTO qiita.analysis(email, name, description, dflt, analysis_status_id) VALUES (eml, eml || '-dflt', 'dflt', true, 1);
END LOOP;
END $do$;