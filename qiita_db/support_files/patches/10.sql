-- Dec 17, 2014
-- Adding a new filepath_type = raw_sff
-- Adding 454 Parameters

INSERT INTO qiita.filepath_type (filepath_type) VALUES ('raw_sff');

DROP TABLE qiita.preprocessed_sequence_454_params;
CREATE TABLE qiita.preprocessed_sequence_454_params ( 
	preprocessed_params_id bigserial NOT NULL,
    min_seq_len integer DEFAULT 200 NOT NULL,
    max_seq_len integer DEFAULT 1000 NOT NULL,
    trim_seq_length bool DEFAULT FALSE NOT NULL,
    min_qual_score integer DEFAULT 25 NOT NULL,
    max_ambig integer DEFAULT 6 NOT NULL,
    max_homopolymer integer DEFAULT 6 NOT NULL,
    max_primer_mismatch integer DEFAULT 0 NOT NULL,
    barcode_type varchar DEFAULT 'golay_12' NOT NULL,
    max_bc_errors real DEFAULT 1.5 NOT NULL,
    disable_bc_correction bool DEFAULT FALSE NOT NULL,
    qual_score_window integer DEFAULT 0 NOT NULL,
    disable_primers bool DEFAULT FALSE NOT NULL,
    reverse_primers varchar DEFAULT 'disable' NOT NULL,
    reverse_primer_mismatches integer DEFAULT 0 NOT NULL,
    median_length_filtering varchar DEFAULT '' NOT NULL,
    truncate_ambig_bases bool DEFAULT FALSE NOT NULL,
	CONSTRAINT pk_preprocessed_sequence_454_params PRIMARY KEY ( preprocessed_params_id )
 );

COMMENT ON TABLE qiita.preprocessed_sequence_454_params IS 'Parameters used for processing 454 sequence data.';

INSERT INTO qiita.preprocessed_sequence_454_params (barcode_type) VALUES ('golay_12'), ('hamming_8');
