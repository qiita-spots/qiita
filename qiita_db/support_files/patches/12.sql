-- Dec 26, 2014
-- Adding barcode_type for Illumina Parameters

INSERT INTO qiita.preprocessed_sequence_illumina_params (param_set_name, barcode_type, rev_comp_mapping_barcodes) 
    VALUES ('barcode_type 8, defaults', '8', false),
    	   ('barcode_type 8, reverse complement mapping file barcodes', '8', true),
    	   ('barcode_type 6, defaults', '6', false),
    	   ('barcode_type 6, reverse complement mapping file barcodes', '6', true);