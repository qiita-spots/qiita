-- November 15th, 2017
ALTER TABLE qiita.command_output ADD check_biom_merge bool DEFAULT 'False' NOT NULL;
ALTER TABLE qiita.command_parameter ADD name_order integer  ;
ALTER TABLE qiita.command_parameter ADD check_biom_merge bool DEFAULT 'False' NOT NULL;

-- Nov 22, 2017
-- Adding a hidden variable to the qiita.processing_job column

ALTER TABLE qiita.processing_job ADD COLUMN hidden boolean DEFAULT FALSE;

UPDATE qiita.processing_job
SET hidden = TRUE
WHERE processing_job_id IN (
    SELECT processing_job_id
    FROM qiita.processing_job
    LEFT JOIN qiita.processing_job_status USING (processing_job_status_id)
    WHERE processing_job_status != 'success');

-- Nov 28, 2017 (only in py file)
-- Adding a new command into Qiita/Alpha: delete_analysis

-- Nov 30, 2017 (only in py file)
-- Expand artifact name size

ALTER TABLE qiita.artifact ALTER COLUMN name TYPE VARCHAR;

-- Dec 3, 2017
-- Adding a function to retrieve the workflow roots of any job
CREATE OR REPLACE FUNCTION qiita.get_processing_workflow_roots(job_id UUID) RETURNS SETOF UUID AS $$
BEGIN
    IF EXISTS(SELECT * FROM qiita.processing_job_workflow_root WHERE processing_job_id = job_id) THEN
        RETURN QUERY SELECT job_id;
    ELSE
        RETURN QUERY WITH RECURSIVE root AS (
            SELECT child_id, parent_id
            FROM qiita.parent_processing_job
            WHERE child_id = job_id
          UNION
            SELECT p.child_id, p.parent_id
            FROM qiita.parent_processing_job p
            JOIN root r ON (r.parent_id = p.child_id)
        )
        SELECT DISTINCT parent_id
            FROM root
            WHERE parent_id NOT IN (SELECT child_id FROM qiita.parent_processing_job);
    END IF;
END
$$ LANGUAGE plpgsql;

-- Dev 7, 2017
-- Adding the name column to the prep template
ALTER TABLE qiita.prep_template ADD name varchar DEFAULT 'Default Name' NOT NULL;

-- Set the default name to be the previous name that was shown
UPDATE qiita.prep_template SET name = 'Prep information ' || prep_template_id::varchar;
