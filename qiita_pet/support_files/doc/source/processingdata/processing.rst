Processing Network Page
=======================
Files Network Within Data Type
------------------------------
* **Dflt_name-(FASTQ) artifact**: Represents the original FASTQ data from the study
* **Click on artifact circle**: Brings up more options 
 * **Edit**: Rename the artifact
 * **Process**: Brings you to processing network page so you can process the data
 * **Delete**: Delete the artifact/data from the files network
 * **Available Files**: FASTQ files that have been uploaded to this study can be downloaded here
 * **Generate Summary**: Creates a summary for the data attached to the artifact chosen

Workflow Page
-------------
* **Run**: Runs the command that is in the processing workflow window
* **Select artifact**: Brings up choose command pulldown menu
* **Choose Command Pull down menu**: Will show you the commands that can be given to the chosen artifact

Converting Data to BIOM Tables
==============================

BIOM
----
* No manipulation is necessary

FASTQ, sff, or FASTA with qual
--------------
* **Per-sample vs Multiplexed FASTQ Demultiplexing**
 * **Split libraries FASTQ**: Converts the raw FASTQ data into the file format used by Qiita for further analysis
  * **Input data** (required): Data being split
  * Hamady and Knight, 2005: CANNOT FIND THIS PAPER
  * **Parameter Set** (required): Chooses the parameters for how to split the libraries
   * **Multiplexed FASTQ; generic 5 base pair barcodes**: Uses first 5 base pairs to identifies samples from FASTQ from multiple samples
   * **Multiplexed FASTQ; generic 5 base pair barcodes with Phred quality threshold: 0**: Uses first 5 base pairs to identifies samples from FASTQ from multiple samples, only use samples with Phred quality score above 0
   * **Multiplexed FASTQ; generic 5 base pair reverse complement mapping file barcodes**: Uses the complementary base pairs to the last 5 base pairs in reverse order to identify samples from FASTQ from multiple samples
   * **Multiplexed FASTQ; generic 6 base pair barcodes**: Uses first 6 base pairs to identify samples from FASTQ from multiple samples
   * **Multiplexed FASTQ; generic 6 base pair reverse complement mapping file barcodes**: Uses the complementary base pairs to the last 6 base pairs in reverse order to identify samples from FASTQ from multiple samples
   * **Multiplexed FASTQ; generic 8 base pair barcodes**: Uses first 8 base pairs to identify samples from FASTQ from multiple samples
   * **Multiplexed FASTQ; generic 8 base pair barcodes with Phred offset: 33**: Uses first 8 base pairs to identify samples from FASTQ from multiple samples, uses Phred offset: 33 for measuring quality
   * **Multiplexed FASTQ; generic 8 base pair reverse complement mapping file barcodes**: Uses the complementary base pairs to the last 8 base pairs in reverse order to identify samples from FASTQ from multiple samples
   * **Multiplexed FASTQ; generic 11 base pair barcodes**: Uses first 11 base pairs to identify samples from FASTQ from multiple samples
   * **Multiplexed FASTQ; generic 11 base pair reverse complement barcodes**: Uses the complementary base pairs to the last 11 base pairs in reverse order to identify samples from FASTQ from multiple samples
   * **Multiplexed FASTQ; generic 12 base pair barcodes**: Uses first 12 base pairs to identify samples from FASTQ from multiple samples
   * **Multiplexed FASTQ; generic 12 base pair reverse complement barcodes**: Uses the complementary base pairs to the last 12 base pairs in reverse order to identify samples from FASTQ from multiple samples
   * **Multiplexed FASTQ; Golay 12 base pair barcodes**: Error correcting for the first 12 base pairs from FASTQ from multiple samples
   * **Multiplexed FASTQ; Golay 12 base pair barcodes with Phred offset: 33**: Error correcting for the first 12 base pairs from FASTQ from multiple samples, uses Phred offset: 33 for measuring quality
   * **Multiplexed FASTQ; Golay 12 base pair barcodes with Phred offset: 64**: Error correcting for the first 12 base pairs from FASTQ from multiple samples, uses Phred offset: 64 for measuring quality
   * **Multiplexed FASTQ; Golay 12 base pair reverse complement barcodes**: Error correcting for the complementary base pairs to the last 12 base pairs in reverse order to identify samples from FASTQ from multiple samples
   * **Multiplexed FASTQ; Golay 12 base pair reverse complement barcodes with Phred offset: 33**: Error correcting for the complementary base pairs to the last 12 base pairs in reverse order to identify samples from FASTQ from multiple samples, uses Phred offset: 33 for measuring quality
   * **Multiplexed FASTQ; Golay 12 base pair reverse complement barcodes with Phred offset**: 64: Error correcting for the complementary base pairs to the last 12 base pairs in reverse order to identify samples from FASTQ from multiple samples, uses Phred offset: 64 for measuring quality
   * **Multiplexed FASTQ; Golay 12 base pair reverse complement mapping file barcodes with reverse complement barcodes (UCSD CMI standard)**: Error correcting for the complementary base pairs to the last 12 base pairs in reverse order to identify samples from FASTQ from multiple samples
   * **Per-sample FASTQ defaults** (auto detect): Error detection for the FASTQ from 1 sample
   * **Per-sample FASTQs; Phred offset: 33**: Error detection for the FASTQ from 1 sample, uses Phred offset: 33 for measuring quality
   * **Per-sample FASTQs; Phred offset: 64**: Error detection for the FASTQ from 1 sample, uses Phred offset: 64 for measuring quality
   * **Citation for Golay Coding**: *Golay, Marcel J. E. (1949). "Notes on Digital Coding". Proc. IRE. (37): 657.*
   * **Citation for Golay 16S**: *Caporaso, J., Lauber, C.L., Walter, W.A. Berg0Lyons, D., Huntley, J., Fierer, N., Owens, S.M., Betley, J., Fraser, L., Mauer, M., Gormley, N., Gilbert, J.A., Smith, G., Knight, R., (2012) “Ultra-high-throughput microbial community analysis on the Illumina HiSeq and MiSeq platforms”. ISME J.*
   * **Phred Citation**: *Ewing, B., Hillier, L., Wendi, M.C., Green, P. (1998). (1998). "Base-calling of automated sequencer traces using phred. I. Accuracy assessment". Genome Research. 8 (3): 175–185.*
    * *https://en.wikipedia.org/wiki/FASTQ_format*
   * **Demultiplexing**: **https://en.wikipedia.org/wiki/Multiplexing*
  * **Default Parameters Set**
   * **barcode type** (required): Type of barcode used
   * **max bad_run_length** (required): Max number of consecutive low quality base calls allowed before truncating a read
   * **max barcode_errors** (required): Maximum number of errors in barcode
   * **min per_read_length_fraction** (required): Minimum number of consecutive high quality base calls to include a read
   * **phred offset** (required): Ascii (character that corresponds to a Phred score) offset to use when decoding phred scores
   * **phred quality threshold** (required): Minimum acceptable Phred quality score
   * **rev comp** (required): Reverse complement sequence before writing to output file
   * **rev comp_barcode** (required): Reverse complement barcode reads before lookup
   * **rev comp_mapping_barcodes** (required): Reverse complement barcode in mapping before lookup
   * **sequence max_n** (required): Maximum number of N characters allowed in a sequence to retain it

Deblurring
==========
*Note that sff data cannot be deblurred*
* **Trimming**: Removes base pairs from the sequences
 * **Input Data** (required): Data being trimmed
 * **Parameter Set** (required): How many bases to trim off
  * **90 base pairs**- Removes first 90 base pairs from the sequences
  * **100 base pairs**- Removes first 100 base pairs from the sequences
  * **125 base pairs**- Removes first 125 base pairs from the sequences
  * **150 base pairs**- Removes first 150 base pairs from the sequences
  * **200 base pairs**- Removes first 200 base pairs from the sequences
  * **250 base pairs**- Removes first 250 base pairs from the sequences
  * **300 base pairs**- Removes first 300 base pairs from the sequences
* **Command from Trimmed Artifact**:
 * **Deblur Workflow**: Removes sequences due to error and does not take into account if sequences are found in a database
  * **Default Parameters** 
   * **Error probabilities for each Hamming distance** (required): List of error probabilities for each hamming distance
    * Length of list determines number of hamming distances taken into account
   * **Indexed negative filtering database** (required): Indexed version of the negative filtering database
   * **Indexed positive filtering database** (required): Indexed version of the positive filtering database
   * **Insertion/deletion (indel) probability** (required): Insertion/deletion probability
   * **Jobs to start** (required): Number of workers to start (if to run in parallel)
   * **Maximum number of insertion/deletion (indel)** (required): Maximum number of allowed insertions/deletions
   * **Mean per nucleotide error rate** (required): Mean per nucleotide error rate
    * Used for original sequence estimate if the the typical Illumina error wasn’t passed for the original
   * **Minimum dataset-wide read threshold** (required): Keep only the sequences which appear at this many times study wide (as opposed to per-sample)
   * **Minimum per-sample read threshold** (required): Keep only the sequences which appear at this many times per sample (as opposed to study wide)
   * **Negative filtering database** (required): Negative (artifacts) filtering database
    * Drops all sequences which align to any record in this
   * **Positive filtering database** (required): Positive reference filtering database
    * Keeps all sequences permissively aligning to any sequence
   * **Sequence trim length (-1 for no trimming)** (required): Sequence trim length
   * **Threads per sample** (required): Number of threads to use per sample
 * **Deblur 16S Only Table**: Only contains 16S deblurred sequences 
 * **Deblur Final Table**: Contains all the sequences.
* **Deblur Citation**: *Amir, A., McDonald, D., Navas-Molina, J.A., Kopylova, E., Morton, J., Xu, Z.Z., Kightley, E.P.,  Thompson, L.R., Hyde, E.R., Gonzalez, A., Knight, R. (2017) “Deblur rapidly resolves single-nucleotide community sequence patterns.” mSystems. 2 (2) e00191-16.*

Closed-Reference OTU Picking
============================
* **Pick Closed-Reference OTUs**: Removes sequences that do not match those found in a database
 * **Input data** (required): Data being close referenced 
 * **Parameter Set** (required): Chooses the database to be compared to
  * **16S OTU Picking**:
   * **Defaults**: Compares to Greengenes 16S Database
    * **Greengenes Citation**: *McDonald, D., Price, M. N., Goodrich, J., Nawrocki, E. P., DeSantis, T. Z., Probst, A., Anderson, G. L., Knight, R.,  Hugenholtz, P. (2012). “An improved Greengenes taxonomy with explicit ranks for ecological and evolutionary analyses of bacteria and archaea.” The ISME Journal. 6(3): 610–618.*
   * **Defaults-parallel**: Compares to GreenGenes 16S database but performs it with multi-threading
    * **Greengenes Citation**:  *McDonald, D., Price, M. N., Goodrich, J., Nawrocki, E. P., DeSantis, T. Z., Probst, A., Anderson, G. L., Knight, R.,  Hugenholtz, P. (2012). “An improved Greengenes taxonomy with explicit ranks for ecological and evolutionary analyses of bacteria and archaea.” The ISME Journal. 6(3): 610–618.*
  * **18S OTU Picking**:
   * **Silva 119**: Compares to Silva 119 Database
    * **Silve 119 Citation**: *Quast, C., Pruesse, E., Yilmaz, P., Gerken, J., Schweer, T., Yarza, P., Peplies, J., Glöckner, F. O. (2013). “The SILVA ribosomal RNA gene database project: improved data processing and web-based tools”. Nucl. Acids Res. 41 (D1): D590-D596.*
  * **ITS OTU Picking**:
   * **UNITE 7**: Compares to UNITE Database
    * **UNITE Citation**: *Abarenkov, K., Nilsson, R. H., Larsson, K., Alexander, I. J., Eberhardt, U., Erland, S., Høiland, K., Kjøller, R., Larsson, E., Pennanen, R., Sen, R., Taylor, A. F. S., Tedersoo, L., Ursing, B. M., Vrålstad, T., Liimatainen, K., Peintner, U., Kõljalg, U. (2010). “The UNITE database for molecular identification of fungi - recent updates and future perspectives”. New Phytologist. 186(2): 281-285.*
 * **Default Parameters** (required)
  * **Reference-seq** (required): Path to blast database (Greengenes, Silva 119, UNITE 7) as a fasta file
  * **Reference-tax** (required): Path to corresponding taxonomy file (Greengenes, Silva 119, UNITE 7)
  * **Similarity** (required): Sequence similarity threshold
  * **Sortmerna coverage** (required): Minimum percent query coverage (of an alignment) to consider a hit, expressed as a fraction between 0 and 1 
  * **Sortmerna e_value** (required): Maximum e-value when clustering (local sequence alignment tool for filtering, mapping, and OTU picking) can expect to see by chance when searching a database
  * **Sortmerna max-pos** (required): Maximum number of positions per seed to store in the indexed database
  * **Threads** (required): Number of threads to use per job
  * **SortMeRNA Citation**: *Kopylova, E., Noe, L., Touzet, H. (2012). “SortMeRNA: fast and accurate filtering of ribosomal RNAs in metatranscriptomic data”. Bioinformatics. 28 (24) 3211-7.*
 * **QIIME Citation**: *Navas-Molina, J.A., Peralta-Sánchez, J.M., González, A., McMurdie, P.J., Vázquez-Baeza, Y., Xu, Z., Ursell, L.K., Lauber, C., Zhou, H., Song S.J., Huntley, J., Ackermann, G.L., Berg-Lyons, D., Holmes, S., Caporaso, J.G., Knight, R. (2013). “Advancing Our Understanding of the Human Microbiome Using QIIME”. Methods in Enzymology. (531): 371-444*
 * **Closed Reference Citation**: *Chou, H.H., Holmes, M.H. (2001). “DNA sequence quality trimming and vector removal”. Bioinformatics. 17 (12):1093–1104.*
 
For advanced processing information see below:
 
Processing recommendations: Advanced
====================================

Currently, Qiita supports the processing :sup:`(*)` of raw data from:

#. Target gene barcoded sequencing
#. Shotgun sequencing

Note that the selected processing are mainly guided so we can perform meta-analyses, this is combine different studies, even from different wet lab techniques or
sequencing technologies. Remember to check the :ref:`example_study_processing_workflow` before continuing.

For more information about meta-analysis, examples and things to consider:

- `"Tiny microbes, enormous impacts: what matters in gut microbiome studies?" <https://genomebiology.biomedcentral.com/articles/10.1186/s13059-016-1086-x>`_
- `"Meta-analyses of studies of the human microbiota" <http://genome.cshlp.org/content/23/10/1704.short>`_.
- `"A Guide to Enterotypes across the Human Body: Meta-Analysis of Microbial Community Structures in Human Microbiome Datasets" <http://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1002863>`_.
- `"Dynamic changes in short- and long-term bacterial composition following fecal microbiota transplantation for recurrent Clostridium difficile infection" <http://microbiomejournal.biomedcentral.com/articles/10.1186/s40168-015-0070-0>`_.

:sup:`(*)` Remember that you can also upload BIOM tables for plotting but not covered here because this is only for raw data.

Target gene barcoded sequencing
-------------------------------

For this you can start with raw, not demultiplexed data or per_sample_FASTQ, see :ref:`example_study_processing_workflow`. Either way, you will need to
"Split libraries and QC", which uses the default in QIIME 1.9.1. Once your demultiplexed and QCed artifact is created you need to select which processing to perform.
There are two main ideologies/methodologies to process target gene data: sequence clustering and sequence cleanup.

Sequencing cleanup (preferred)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For this we use `deblur <https://github.com/biocore/deblur>`_. Here 2 BIOM tables are generated by default: fina.biom and final.only-16s.biom. The former is the full biom table, which can be used with any target gene and wetlab work;
the latter is the trimmed version to those sequences that match Greengenes at 80% similarity, a really basic and naive filtering. Each of those BIOM tables, is accompanied by a FASTA that contains
the representative sequences. The OTU IDs are given by the unique sequence.

Note that deblur needs all sequences to be trimmed at the same length, thus the recommended pipeline is to trim everything at 150bp and the deblur.

Sequencing clustering
^^^^^^^^^^^^^^^^^^^^^

Here we use close reference picking, for an explanation of the different picking methods see
`"Subsampled open-reference clustering creates consistent, comprehensive OTU definitions and scales to billions of sequences" <https://peerj.com/articles/545/>`_.
Here we generate a single BIOM table with the OTUs/per-sample. The OTU IDs are given based on the reference database selected.

Currently, we have the reference databases: Greengenes version 3_8-97, Silva 119 and Unite 7. Depending on your selection is if the reference has a phylogenetic tree.


Shotgun sequencing
------------------

Qiita currently has one shotgun metagenomics data analysis pipeline. Note that this is the initial processing pipeline and we will be adding more soon.

With that said, the current workflow is as follows:

#. Removal of adapter sequence and host contamination using `KneadData <https://bitbucket.org/biobakery/kneaddata/wiki/Home>`_.
#. Gene calling and pathway profiling using `HUMAnN2 <https://bitbucket.org/biobakery/humann2/wiki/Home>`_.

This workflow starts with per_sample_FASTQ files. We recommend only uploading sequences that have already been through QC and host /
human sequence removal. However, all sequence files currently are required to go through KneadData to ensure they are ready for
subsequent analyses. Currently, the KneadData command removes adaptor sequences (choice of TruSeq3-PE-2 and NexteraPE-PE) and
sequences mapping to the human genome (additional host genomes will become available soon).

Next, the QC'd sequences will be compared against reference databases to determine the presence and abundance of protein-coding functional genes and
pathways using HUMAnN2. These are then summarized as BIOM tables, which can be used in subsequent analysis and visualization.

For more information visit the `Shotgun Qiita Plugin GitHub page <https://github.com/qiita-spots/qp-shotgun>`.

