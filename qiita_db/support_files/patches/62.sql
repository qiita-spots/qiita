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
