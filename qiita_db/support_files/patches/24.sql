-- May 7, 2015
-- This patch adds the ON UPDATE CASCADE constraint to all the FK
-- that are referencing the sample ids

DO $do$
DECLARE
    dyn_t varchar;
    fk_vals RECORD;
BEGIN

-- The dynamic tables do not have a FK set on their sample ID
-- We need to find the dynamic tables existing in the system and we add the
-- FK constraint to them.
FOR dyn_t IN
    SELECT DISTINCT table_name
    FROM information_schema.columns
    WHERE (SUBSTR(table_name, 1, 7) = 'sample_'
           OR SUBSTR(table_name, 1, 5) = 'prep_')
        AND table_schema = 'qiita'
        AND table_name NOT IN ('prep_template',
                               'prep_template_preprocessed_data',
                               'prep_template_filepath',
                               'prep_columns',
                               'sample_template_filepath',
                               'prep_template_sample')
LOOP
    EXECUTE 'ALTER TABLE qiita.' || dyn_t || '
                ADD CONSTRAINT fk_' || dyn_t || '
                FOREIGN KEY (sample_id)'
                'REFERENCES qiita.study_sample (sample_id);';
END LOOP;

-- Search for all the tables that are pointing to the sample_id
-- and add the FK constraint with ON UPDATE CASCADE
FOR fk_vals IN 
    SELECT r.table_name, r.column_name, fk.constraint_name
        FROM information_schema.constraint_column_usage u
        INNER JOIN information_schema.referential_constraints fk
            ON u.constraint_catalog = fk.unique_constraint_catalog
            AND u.constraint_schema = fk.unique_constraint_schema
            AND u.constraint_name = fk.unique_constraint_name
        INNER JOIN information_schema.key_column_usage r
            ON r.constraint_catalog = fk.constraint_catalog
            AND r.constraint_schema = fk.constraint_schema
            AND r.constraint_name = fk.constraint_name
        WHERE u.column_name = 'sample_id'
            AND u.table_schema = 'qiita'
            AND u.table_name = 'study_sample'
LOOP
    EXECUTE 'ALTER TABLE qiita.' || fk_vals.table_name || '
                DROP CONSTRAINT ' || fk_vals.constraint_name || ',
                ADD CONSTRAINT ' || fk_vals.constraint_name ||'
                    FOREIGN KEY (' || fk_vals.column_name ||')
                    REFERENCES qiita.study_sample( sample_id )
                    ON UPDATE CASCADE;';
END LOOP;
END $do$;