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
-- values taken from ftp://ftp.sra.ebi.ac.uk/meta/xsd/sra_1_5/SRA.common.xsd
CREATE TABLE qiita.restrictions (
  table_name varchar,
  name varchar,
  valid_values varchar[]
);
INSERT INTO qiita.restrictions (table_name, name, valid_values) VALUES
  -- inserting the sample info file restrictions
  ('study_sample', 'env_package', ARRAY[
    'air', 'built environment', 'host-associated', 'human-associated',
    'human-skin', 'human-oral', 'human-gut', 'human-vaginal',
    'microbial mat/biofilm', 'misc environment', 'plant-associated',
    'sediment', 'soil', 'wastewater/sludge', 'water']),
  -- inserting the prep info file restrictions
  ('prep_template_sample', 'target_gene', ARRAY[
    '16S rRNA', '18S rRNA', 'ITS1/2', 'LSU']),
  ('prep_template_sample', 'platform', ARRAY[
    'FASTA', 'Illumina', 'Ion Torrent', 'LS454', 'Oxford Nanopore']),
  ('prep_template_sample', 'target_subfragment', ARRAY[
    'V3', 'V4', 'V6', 'V9', 'ITS1/2']),
  ('prep_template_sample', 'instrument_model', ARRAY[
    -- LS454
    '454 GS', '454 GS 20', '454 GS FLX', '454 GS FLX+', '454 GS FLX Titanium',
    '454 GS Junior',
    -- Illumina
    'Illumina Genome Analyzer', 'Illumina Genome Analyzer II',
    'Illumina Genome Analyzer IIx', 'Illumina HiScanSQ',
    'Illumina HiSeq 1000', 'Illumina HiSeq 1500', 'Illumina HiSeq 2000',
    'Illumina HiSeq 2500', 'Illumina HiSeq 3000', 'Illumina HiSeq 4000',
    'Illumina MiSeq', 'Illumina MiniSeq', 'Illumina NovaSeq 6000',
    'NextSeq 500', 'NextSeq 550',
    -- Ion Torren
    'Ion Torrent PGM', 'Ion Torrent Proton', 'Ion Torrent S5',
    'Ion Torrent S5 XL',
    -- Oxford Nanopore
    'MinION', 'GridION', 'PromethION',
    -- all
    'unspecified']);
