-- Sep 20, 2017
-- Allowing per_sample_FASTQ to be submitted to EBI

UPDATE qiita.artifact_type SET can_be_submitted_to_ebi = true WHERE artifact_type='per_sample_FASTQ';
