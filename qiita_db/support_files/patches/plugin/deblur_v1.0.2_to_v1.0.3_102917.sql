-- With the QIIMEq2 release, the parameters for the command "Pick closed-reference
-- OTUs" changed. The parameter "reference" has ben substituted for 2 parameters
-- "reference-tax" and "reference-seq" which contains the path to the actual
-- reference taxonomy file and the reference sequence file

DO $do$
DECLARE
    old_deblur_id BIGINT;
    new_deblur_id BIGINT;
    a_info        RECORD;
    pj_id         UUID;
BEGIN
    SELECT command_id INTO old_deblur_id
        FROM qiita.software_command sc
            JOIN qiita.software s USING (software_id)
        WHERE s.name = 'deblur' AND s.version = '1.0.2' AND sc.name = 'deblur-workflow';

    SELECT command_id INTO new_deblur_id
        FROM qiita.software_command sc
            JOIN qiita.software s USING (software_id)
        WHERE s.name = 'deblur' AND s.version = '1.0.3' AND sc.name = 'deblur-workflow';

    -- Modify those artifacts and jobs that have been picked against Greengenes
    FOR a_info IN
        SELECT * FROM qiita.artifact WHERE command_id = old_deblur_id
    LOOP
        SELECT processing_job_id INTO pj_id
            FROM qiita.processing_job
                JOIN qiita.artifact_output_processing_job USING (processing_job_id)
            WHERE artifact_id = a_info.artifact_id;

        UPDATE qiita.processing_job
            SET command_parameters = parameters, command_id = new_deblur_id
            WHERE processing_job_id = pj_id;

        UPDATE qiita.artifact
            SET command_parameters = parameters, command_id = new_deblur_id
            WHERE artifact_id = a_info.artifact_id;

    END LOOP;
END $do$
