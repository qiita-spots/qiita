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

-- Apr 25th, 2019
-- adding restriction tables for sample/prep info files
CREATE TABLE qiita.restrictions (
  table_name varchar,
  name varchar,
  valid_values varchar[]
);
INSERT INTO qiita.restrictions (table_name, name, valid_values) VALUES
  -- inserting the sample info file restrictions
  ('study_sample', 'env_package', ARRAY[
    'air', 'built environment', 'host-associated', 'human-amniotic-fluid',
    'human-associated', 'human-blood', 'human-gut', 'human-oral', 'human-skin',
    'human-urine', 'human-vaginal', 'microbial mat/biofilm',
    'miscellaneous natural or artificial environment', 'plant-associated',
    'sediment', 'soil', 'wastewater/sludge', 'water']),
  -- inserting the prep info file restrictions
  ('prep_template_sample', 'target_gene', ARRAY[
    '16S rRNA', '18S rRNA', 'ITS']),
  ('prep_template_sample', 'platform', ARRAY[
    'Ion Torrent', 'LS454', 'Illumina']),
  ('prep_template_sample', 'target_subfragment', ARRAY[
    'V1', 'V2', 'V3', 'V4', 'V6', 'V9', 'ITS1', 'ITS2'])
;
