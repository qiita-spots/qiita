-- Apr 2nd, 2019
-- Add a new filepath type
INSERT INTO qiita.filepath_type (filepath_type) VALUES ('qza');

-- Apr 16th, 2019
-- Removing emp_person_id from Qiita
DROP INDEX qiita.idx_study_1;
ALTER TABLE qiita.study DROP CONSTRAINT fk_study_study_emp_person;
ALTER TABLE qiita.study DROP COLUMN emp_person_id;

-- Apr 18th, 2019
-- adding fp_size to filepaths to store the filepath size
ALTER TABLE qiita.filepath ADD fp_size BIGINT NOT NULL DEFAULT 0;
