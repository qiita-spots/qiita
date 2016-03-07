-- Jan 26, 2016
-- Relate the artifact types with the filepath types that they support

CREATE TABLE qiita.artifact_type_filepath_type (
	artifact_type_id     bigint  NOT NULL,
	filepath_type_id     bigint  NOT NULL,
	required             bool DEFAULT 'TRUE' NOT NULL,
	CONSTRAINT idx_artifact_type_filepath_type PRIMARY KEY ( artifact_type_id, filepath_type_id )
 ) ;

CREATE INDEX idx_artifact_type_filepath_type_at ON qiita.artifact_type_filepath_type ( artifact_type_id ) ;
CREATE INDEX idx_artifact_type_filepath_type_ft ON qiita.artifact_type_filepath_type ( filepath_type_id ) ;
ALTER TABLE qiita.artifact_type_filepath_type ADD CONSTRAINT fk_artifact_type_filepath_type_at FOREIGN KEY ( artifact_type_id ) REFERENCES qiita.artifact_type( artifact_type_id )    ;
ALTER TABLE qiita.artifact_type_filepath_type ADD CONSTRAINT fk_artifact_type_filepath_type_ft FOREIGN KEY ( filepath_type_id ) REFERENCES qiita.filepath_type( filepath_type_id )    ;

INSERT INTO qiita.artifact_type_filepath_type (artifact_type_id, filepath_type_id, required) VALUES
    -- Artifact Type: SFF - Filepath Types: raw_sff (required)
    (1, 17, TRUE),
    -- Artifact Type: FASTA_Sanger - Filepath Types: raw_fasta (required), raw_qual (currently required)
    (2, 18, TRUE), (2, 19, TRUE),
    -- Artifact Type: FASTQ - Filepath Types: raw_forward_seqs (required), raw_reverse_seqs (optional), raw_barcodes (requred)
    (3, 1, TRUE), (3, 2, FALSE), (3, 3, TRUE),
    -- Artifact Type: FASTA - Filepath Types: raw_fasta (required), raw_qual (currently required)
    (4, 18, TRUE), (4, 19, TRUE),
    -- Artifact Type: per_sample_FASTQ - Filepath Types: raw_forward_seqs (required), raw_reverse_seqs (optional)
    (5, 1, TRUE), (5, 2, FALSE),
    -- Artifact Type: Demultiplexed - Filepath Types: preprocessed_fasta (required), preprocessed_fastq (required), preprocessed_demux (optional), log (optional)
    (6, 4, TRUE), (6, 5, TRUE), (6, 6, FALSE), (6, 13, FALSE),
    -- Artifact Type: BIOM - Filepath Types: biom, directory, log
    (7, 7, TRUE), (7, 8, FALSE), (7, 13, FALSE);
