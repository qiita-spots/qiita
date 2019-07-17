-- November 21, 2018
-- moving sample and prep info files to jsonb

-- 4/4 This is the continuation of the patching that started in 68.sql, let's
-- remove all the temp (_bk) tables we created

-- On January 17, 2019 while releasing the release candidate; we realized that
-- we were hitting the max memory allocated for the machine so we needed to
-- split this into two
-- Dropping all the _bk tables 2/2
DO $do$
DECLARE
    dyn_table varchar;
BEGIN
  FOR dyn_table IN
    SELECT DISTINCT table_name
    FROM information_schema.columns
    WHERE table_name LIKE '%_bk'
  LOOP
    EXECUTE 'DROP TABLE qiita.' || dyn_table;
  END LOOP;
END $do$;
