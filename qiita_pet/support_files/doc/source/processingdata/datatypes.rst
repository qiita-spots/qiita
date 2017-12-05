HELP WITH: .SSF SAMPLE + FASTA/FMLA + QUAL+ HAMADY AND KNIGHT PAPER

BIOM
----
* No manipulation is necessary
**.sff sample: Antonio can you help with this**
-----------------------------------------------
* **FASTA/fma+qual**
--------------------
FASTQ/FAST.gz
--------------
* **Per-sample vs Multiplexed FASTQ Demultiplexing**
 * **Split libraries FASTQ**: converts the raw FASTQ data into the file format used by Qiita for further analysis
  * **Input data** (required): data being split
  * Hamady and Knight, 2005: CANNOT FIND THIS PAPER
  * **Parameter Set** (required): Chooses the parameters for how to split the libraries
    * **Multiplexed FASTQ; generic 5 base pair barcodes**: uses first 5 base pairs to identifies samples from FASTQ from multiple samples
    * **Multiplexed FASTQ; generic 5 base pair barcodes with Phred quality threshold: 0**:  uses first 5 base pairs to identifies samples from FASTQ from multiple samples, only use samples with Phred quality score above 0
    * **Multiplexed FASTQ; generic 5 base pair reverse complement mapping file barcodes**:  uses the complementary base pairs to the last 5 base pairs in reverse order to identify samples from FASTQ from multiple samples
    * **Multiplexed FASTQ; generic 6 base pair barcodes**: uses first 6 base pairs to identify samples from FASTQ from multiple samples
    * **Multiplexed FASTQ; generic 6 base pair reverse complement mapping file barcodes**: uses the complementary base pairs to the last 6 base pairs in reverse order to identify samples from FASTQ from multiple samples
    * **Multiplexed FASTQ; generic 8 base pair barcodes**: uses first 8 base pairs to identify samples from FASTQ from multiple samples
    * **Multiplexed FASTQ; generic 8 base pair barcodes with Phred offset: 33**: uses first 8 base pairs to identify samples from FASTQ from multiple samples, uses Phred offset: 33 for measuring quality
    * **Multiplexed FASTQ; generic 8 base pair reverse complement mapping file barcodes**: uses the complementary base pairs to the last 8 base pairs in reverse order to identify samples from FASTQ from multiple samples
    * **Multiplexed FASTQ; generic 11 base pair barcodes**: uses first 11 base pairs to identify samples from FASTQ from multiple samples
    * **Multiplexed FASTQ; generic 11 base pair reverse complement barcodes**: uses the complementary base pairs to the last 11 base pairs in reverse order to identify samples from FASTQ from multiple samples
    * **Multiplexed FASTQ; generic 12 base pair barcodes**: uses first 12 base pairs to identify samples from FASTQ from multiple samples
    * **Multiplexed FASTQ; generic 12 base pair reverse complement barcodes**: uses the complementary base pairs to the last 12 base pairs in reverse order to identify samples from FASTQ from multiple samples
    * **Multiplexed FASTQ; Golay 12 base pair barcodes**: error correcting for the first 12 base pairs from FASTQ from multiple samples
    * **Multiplexed FASTQ; Golay 12 base pair barcodes with Phred offset: 33**: error correcting for the first 12 base pairs from FASTQ from multiple samples, uses Phred offset: 33 for measuring quality
    * **Multiplexed FASTQ; Golay 12 base pair barcodes with Phred offset: 64**: error correcting for the first 12 base pairs from FASTQ from multiple samples, uses Phred offset: 64 for measuring quality
    * **Multiplexed FASTQ; Golay 12 base pair reverse complement barcodes**: error correcting for the complementary base pairs to the last 12 base pairs in reverse order to identify samples from FASTQ from multiple samples
    * **Multiplexed FASTQ; Golay 12 base pair reverse complement barcodes with Phred offset: 33**: error correcting for the complementary base pairs to the last 12 base pairs in reverse order to identify samples from FASTQ from multiple samples, uses Phred offset: 33 for measuring quality
    * **Multiplexed FASTQ; Golay 12 base pair reverse complement barcodes with Phred offset**: 64: error correcting for the complementary base pairs to the last 12 base pairs in reverse order to identify samples from FASTQ from multiple samples, uses Phred offset: 64 for measuring quality
    * **Multiplexed FASTQ; Golay 12 base pair reverse complement mapping file barcodes with reverse complement barcodes (UCSD CMI standard)**: Error correcting for the complementary base pairs to the last 12 base pairs in reverse order to identify samples from FASTQ from multiple samples
    * **Per-sample FASTQ defaults** (auto detect): error detection for the FASTQ from 1 sample
    * **Per-sample FASTQs; Phred offset: 33**: error detection for the FASTQ from 1 sample, uses Phred offset: 33 for measuring quality
    * **Per-sample FASTQs; Phred offset: 64**: error detection for the FASTQ from 1 sample, uses Phred offset: 64 for measuring quality
    * **Citation for Golay Coding**: *Golay, Marcel J. E. (1949). "Notes on Digital Coding". Proc. IRE. (37): 657.*
    * **Citation for Golay 16S**: *Caporaso, J., Lauber, C.L., Walter, W.A. Berg0Lyons, D., Huntley, J., Fierer, N., Owens, S.M., Betley, J., Fraser, L., Mauer, M., Gormley, N., Gilbert, J.A., Smith, G., Knight, R., (2012) “Ultra-high-throughput microbial community analysis on the Illumina HiSeq and MiSeq platforms”. ISME J.*
    * **Phred Citation**: *Ewing, B., Hillier, L., Wendi, M.C., Green, P. (1998). (1998). "Base-calling of automated sequencer traces using phred. I. Accuracy assessment". Genome Research. 8 (3): 175–185.*
     * *https://en.wikipedia.org/wiki/FASTQ_format*
    * **Demultiplexing**: **https://en.wikipedia.org/wiki/Multiplexing*
   * **Default Parameters Set**
    * **barcode type** (required): The type of barcode used
    * **max bad_run_length** (required): Max number of consecutive low quality base calls allowed before truncating a read
    * **max barcode_errors** (required): Maximum number of errors in barcode
    * **min per_read_length_fraction** (required): Min number of consecutive high quality base calls to include a read
    * **phred offset** (required): The ascii (character that corresponds to a Phred score) offset to use when decoding phred scores
    * **phred quality threshold** (required): The minimum acceptable Phred quality score
    * **rev comp** (required): Reverse complement sequence before writing to output file
    * **rev comp_barcode** (required): Reverse complement barcode reads before lookup
    * **rev comp_mapping_barcodes** (required): Reverse complement barcode in mapping before lookup
    * **sequence max_n** (required): Maximum number of N characters allowed in a sequence to retain it



