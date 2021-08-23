-- Jun 23, 2020
-- Adds a new job_type VALIDATOR to processing_job_resource_allocation

INSERT INTO qiita.processing_job_resource_allocation (name, job_type, allocation) VALUES
  ('default', 'VALIDATOR', '-q qiita -l nodes=1:ppn=1 -l mem=1gb -l walltime=4:00:00'),
  ('per_sample_FASTQ', 'VALIDATOR', '-q qiita -l nodes=1:ppn=5 -l mem=2gb -l walltime=10:00:00'),
  ('ordination_results', 'VALIDATOR', '-q qiita -l nodes=1:ppn=1 -l mem=10gb -l walltime=2:00:00'),
  ('Demultiplexed', 'VALIDATOR', '-q qiita -l nodes=1:ppn=5 -l mem=25gb -l walltime=150:00:00'),
  ('distance_matrix', 'VALIDATOR', '-q qiita -l nodes=1:ppn=1 -l mem=42gb -l walltime=150:00:00'),
  ('BIOM', 'VALIDATOR', '-q qiita -l nodes=1:ppn=1 -l mem=90gb -l walltime=150:00:00'),
  ('alpha_vector', 'VALIDATOR', '-q qiita -l nodes=1:ppn=1 -l mem=10gb -l walltime=70:00:00');


-- For EBI-ENA, Ion Torren is Ion_Torrent
UPDATE qiita.restrictions SET valid_values = ARRAY['FASTA', 'Illumina', 'Ion_Torrent', 'LS454', 'Oxford Nanopore']
  WHERE table_name = 'prep_template_sample' AND name = 'platform';
