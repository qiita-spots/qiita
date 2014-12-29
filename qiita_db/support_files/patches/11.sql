-- Dec 17, 2014
-- Adding a new filepath_type = raw_sff
-- Adding 454 Parameters

INSERT INTO qiita.filepath_type (filepath_type) VALUES ('raw_sff'), ('raw_fasta'), ('raw_qual');
INSERT INTO qiita.filetype (type) VALUES ('FASTA');

DROP TABLE qiita.preprocessed_sequence_454_params;
CREATE TABLE qiita.preprocessed_sequence_454_params ( 
	preprocessed_params_id bigserial NOT NULL,
    param_set_name varchar NOT NULL,
    min_seq_len integer DEFAULT 200 NOT NULL,
    max_seq_len integer DEFAULT 1000 NOT NULL,
    trim_seq_length bool DEFAULT FALSE NOT NULL,
    min_qual_score integer DEFAULT 25 NOT NULL,
    max_ambig integer DEFAULT 6 NOT NULL,
    max_homopolymer integer DEFAULT 6 NOT NULL,
    max_primer_mismatch integer DEFAULT 0 NOT NULL,
    barcode_type varchar DEFAULT 'golay_12' NOT NULL,
    max_barcode_errors real DEFAULT 1.5 NOT NULL,
    disable_bc_correction bool DEFAULT FALSE NOT NULL,
    qual_score_window integer DEFAULT 0 NOT NULL,
    disable_primers bool DEFAULT FALSE NOT NULL,
    reverse_primers varchar DEFAULT 'disable' NOT NULL,
    reverse_primer_mismatches integer DEFAULT 0 NOT NULL,
    truncate_ambig_bases bool DEFAULT FALSE NOT NULL,
	CONSTRAINT pk_preprocessed_sequence_454_params PRIMARY KEY ( preprocessed_params_id )
 );

COMMENT ON TABLE qiita.preprocessed_sequence_454_params 
    IS 'Parameters used for processing 454 sequence data.';

INSERT INTO qiita.preprocessed_sequence_454_params (param_set_name, barcode_type) 
    VALUES ('Defaults with Golay 12 barcodes', 'golay_12'), 
           ('Defaults with Hamming 8 barcodes', 'hamming_8');

-- add param set name to illumina sequence params. We're not setting defauft
-- as we need to update the existing parameter sets and then add in the 
-- default
ALTER TABLE qiita.preprocessed_sequence_illumina_params 
    ADD COLUMN param_set_name varchar;

UPDATE qiita.preprocessed_sequence_illumina_params 
    SET param_set_name='Defaults' WHERE preprocessed_params_id=1;
UPDATE qiita.preprocessed_sequence_illumina_params 
    SET param_set_name='Defaults with reverse complement mapping file barcodes' WHERE preprocessed_params_id=2;

ALTER TABLE qiita.preprocessed_sequence_illumina_params 
    ALTER COLUMN param_set_name SET NOT NULL; 
