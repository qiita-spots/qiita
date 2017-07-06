-- Jul 6, 2017
-- DELETE all sample/prep CONSTRAINTs

-- Step 1, remove all FK constraints from study_sample
CREATE OR REPLACE FUNCTION qiita.delete_study_sample_constraints(cname text, tname text) RETURNS void AS $$
    BEGIN
      EXECUTE 'ALTER TABLE ' || tname || ' DROP CONSTRAINT ' || cname;
    END;
$$ LANGUAGE plpgsql;

WITH query AS (
  SELECT constraint_name AS cname, 'qiita.' || table_name AS tname
    FROM information_schema.table_constraints
    WHERE constraint_type ='FOREIGN KEY' AND (
        (constraint_name LIKE 'fk_sample_%' AND table_name LIKE 'sample_%') OR
        (constraint_name LIKE 'fk_prep_%' AND table_name LIKE 'prep_%')) AND
        table_name NOT IN ('prep_template', 'prep_template_sample',
                           'prep_template_filepath', 'prep_template_processing_job'))
SELECT qiita.delete_study_sample_constraints(cname, tname) FROM query;

DROP FUNCTION qiita.delete_study_sample_constraints(cname text, tname text);
