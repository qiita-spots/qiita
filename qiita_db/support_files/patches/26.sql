-- Jun 11, 2015

-- Updating FASTA-Sanger -> FASTA_Sanger, needed so we can put restrictions on
-- what kind of files the user can select in the GUI
UPDATE qiita.filetype SET type='FASTA_Sanger' WHERE type = 'FASTA-Sanger';

-- Adding new filetype
INSERT INTO qiita.filetype (type) VALUES ('per_sample_FASTQ');


-- Adding new illumina processing params if they do not exists
-- adapted from: http://stackoverflow.com/a/13902402
INSERT INTO qiita.preprocessed_sequence_illumina_params (param_set_name, barcode_type)
  SELECT DISTINCT 'per sample FASTQ defaults', 'not-barcoded' FROM qiita.preprocessed_sequence_illumina_params
  WHERE NOT EXISTS (SELECT 1 FROM qiita.preprocessed_sequence_illumina_params WHERE barcode_type = 'not-barcoded');
>>>>>>> 1322f888a3cd1e91b90b7e4b62315b6a14e4b69f
