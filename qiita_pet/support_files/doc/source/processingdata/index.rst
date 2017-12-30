Processing Data
===============

Adding and Working With Preperation information
-----------------------------------------------

Prepare information files
~~~~~~~~~~~~~~~~~~~~~~~~~

The set of required fields for the *sample information* and *preparation
information files* varies based on the functionality that you want to
use from the system.

As described in :doc:`../qiita-philosophy/index`, a Qiita study can have
many biological samples, each with many preparations for different kinds of
multi-omic analysis. Thus, the study will have a single *sample information
file* that will define the biological context of each sample. Each multi-omic
data type prepared will have a separate *preparation information file* that
will describe the sequencing technology or analytical chemistry used to
generate that data set.

Please note that while *sample information* and *preparation information files*
are similar to a `QIIME metadata file
<http://qiime.org/documentation/file_formats.html#metadata-mapping-files>`__,
they are conceptually different. A QIIME metadata file includes information
about the biological context, like ``sample_type``, and about the wet lab
processing, like ``BarcodeSequence``. Qiita intentionally separates this
information into two separate files; it would be conceptually incorrect
to include ``BarcodeSequence`` with the *sample information*, as this
information pertains to the wet lab preparation and should be placed in the
*preparation information file*.

Ensure that your prep information column names are correct.

Example files
~~~~~~~~~~~~~

You can download an example prep information file from
`here <ftp://ftp.microbio.me/pub/qiita/sample_prep_information_files_examples.tgz>`__

Required fields for Qiita
~~~~~~~~~~~~~~~~~~~~~~~~~

This is the minimum set of columns for a prep information file to be added the
system:

+-------------------+-------------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Field name        | Format                        | Description                                                                                                                                                                                                                                                   |
+===================+===============================+===============================================================================================================================================================================================================================================================+
| ``sample_name``   | free text with restrictions   | Identifies a sample. It is the primary key, must be unique and should match the ones in the sample information file. Allowed characters are alphabetic ``[A-Za-z]``, numeric ``[0-9]``, and periods ``.``. Must match the sample_name in the sample template. |
+-------------------+-------------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+

Required fields for EBI submission
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Without this columns you will not be able to submit to EBI. These are the columns required for successfully submit your data to EBI:

+-------------------------------------+-------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Field name                          | Format                                    | Description                                                                                                                                                                                                    |
+=====================================+===========================================+================================================================================================================================================================================================================+
| ``primer``                          | IUPAC characters                          | The primer sequence (this is usually the forward primer for Illumina processed data, or the barcoded primer for LS454 data; `examples <http://www.nature.com/ismej/journal/v6/n8/extref/ismej20128x2.txt>`__). |
+-------------------------------------+-------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| ``center_name``                     | free text                                 | Name of the site (company/institution) where the study was performed.                                                                                                                                          |
+-------------------------------------+-------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| ``platform``                        | ``Illumina`` or ``LS454``                 | The sequencing technology used in the study. ``Illumina`` sequencing data was generated on an Illumina platform; ``LS454`` sequencing data was generated on a 454 pyrosequencing platform.                     |
+-------------------------------------+-------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| ``instrument_model``                | see table below                           | The sequencing instrument model used for sequencing. See table below for valid options.                                                                                                                        |
+-------------------------------------+-------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| ``library_construction_protocol``   | free text                                 | Brief description or reference to the protocol that was used for preparing this amplicon library starting from DNA, usually this includes what genomic region was targeted such as *16S*, *ITS*, *18S*, etc.   |
+-------------------------------------+-------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| ``experiment_design_description``   | free text                                 | High-level description of the study (for example, *A longitudinal study of the gut microbiome of two human subjects*).                                                                                         |
+-------------------------------------+-------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+

Valid values for instrument_model per platform, taken from ftp://ftp.sra.ebi.ac.uk/meta/xsd/sra_1_5/SRA.common.xsd

+--------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Platform     | Valid instrument_model options                                                                                                                                                                                                                                                                    |
+==============+===================================================================================================================================================================================================================================================================================================+
| ``LS454``    | ``454 GS``, ``454 GS 20``, ``454 GS FLX``, ``454 GS FLX+``, ``454 GS FLX Titanium``, ``454 GS Junior``, or ``unspecified``                                                                                                                                                                        |
+--------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| ``Illumina`` | ``Illumina Genome Analyzer``, ``Illumina Genome Analyzer II``, ``Illumina Genome Analyzer IIx``, ``Illumina HiSeq 2500``, ``Illumina HiSeq 2000``, ``Illumina HiSeq 1500``, ``Illumina HiSeq 1000``, ``Illumina MiSeq``, ``Illumina HiScanSQ``, ``HiSeq X Ten``, ``NextSeq 500``, ``unspecified`` |
+--------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+

.. _required-fields-for-preprocessing-target-gene-data:

Required fields for pre-processing target gene data
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you are adding target gene data (e.g. 16S, 18S, ITS), there are
additional columns that are required for successfully preprocessing
them:

+---------------+--------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Field name    | Format             | Description                                                                                                                                                                                                    |
+===============+====================+================================================================================================================================================================================================================+
| ``primer``    | IUPAC characters   | The primer sequence (this is usually the forward primer for Illumina processed data, or the barcoded primer for LS454 data; `examples <http://www.nature.com/ismej/journal/v6/n8/extref/ismej20128x2.txt>`__). |
+---------------+--------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| ``barcode``   | IUPAC characters   | The barcode sequence (`examples <http://www.nature.com/ismej/journal/v6/n8/extref/ismej20128x2.txt>`__).                                                                                                       |
+---------------+--------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+

In case that your data has been sequenced using multiple sequencing lanes or you
have :ref:`per_sample_fastq_files_without_barcode_or_primer_information`, an
additional column is required.

+------------------+-------------+------------------------------------------------------------------------------------------------------------------------------------------+
| Field name       | Format      | Description                                                                                                                              |
+==================+=============+==========================================================================================================================================+
| ``run_prefix``   | free text   | Name of your sequence file without the suffix (for example, ``seqs.fna`` becomes ``seqs``, and ``my-data.fastq`` becomes ``my-data``).   |
+------------------+-------------+------------------------------------------------------------------------------------------------------------------------------------------+

Attaching Prep Information
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. figure::  upload_page.png
   :align:   center
   
* **Upload Files Page**
 * Drag your data files into the box to upload your files
 * If you want to delete the file, press the box that appears next to that file then click delete selected files
 * **Go to study description**: Link to the study description page

.. figure::  add_preparation.png
   :align:   center
   
* **Study Description Page**
 * Choose **Add New Preparation** 

.. figure::  add_new_preparation.png
   :align:   center
   
* **Add New Preparation Page**
 * **Select File** (required): Select the preparatory information file you uploaded  
 * **Select Data Type** (required): Choose for what kind of data you studied
 * **Select Investigation Type** (optional): Not required, chooses the investigation you performed
 * **Create New Preparation**: Creates a new preparation based on the data inputted above
 
Associate data with prep
~~~~~~~~~~~~~~~~~~~~~~~~

.. figure::  data_type.png
   :align:   center
   
* **Data Type**
 * **16S, or the data type you studied** dropdown: Shows the preparations created on this type of data on this study
 * **Prep Information Page**
  * To add files
   * **Select Type** (required): Select the file type you uploaded, causing Qiita to associate your files with this preparation
   * **Add a name for this file** (required): Give the file a name
   * **Add Files**: Shows up after Select Type has been chosen, adds files to the preparation
   
.. figure::  prep_summary.png
   :align:   center
   
* **Prep Information Page** 
 * **Summary** Tab
  * Includes preparation info files of that data type that’s associated with your study
   
.. figure::  prep_processing.png
   :align:   center
   
* **Prep Information Page** 
 * **Processing** Tab
  * **Processing Network**: Contains artifacts that represent your data and commands being run on your data
  * **Hide**: Hides the processing network
 
Update prep info
~~~~~~~~~~~~~~~~

* **Prep Information Page**
 * Under the "Summary" tab 
  * Select “Update Information” and choose your updated file
  * *Barcodes and sample names cannot be updated*
   * Must create new preparation to update these

Processing Network Page
-----------------------

Files Network Within Data Type
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. figure::  files_network.png
   :align:   center
   
* **(FASTQ) or other data type artifact**: Represents the data from the study
* **Hide**: Hides the processing network 
* **Show**: Shows the processing network
* **Run**: Runs the command that is in the processing workflow window
* **Click on artifact circle**: Brings up more options 
 * **Edit**: Rename the artifact
 * **Process**: Brings you to processing network page so you can process the data
 * **Delete**: Delete the artifact/data from the files network
 * **Available Files**: FASTQ files that have been uploaded to this study can be downloaded here
 * **Generate Summary**: Creates a summary for the data attached to the artifact chosen
 * **Choose Command dropdown menu**: Will show you the commands that can be given to the chosen artifact
 * **Show processing information**: Shows the processing information of the artifact chosen
* The commands run on this page use the QIIME2 [64](..//references.rst) bioinformatics platform.


Converting Data to BIOM Tables
------------------------------

BIOM
~~~~

* No manipulation is necessary

FASTQ, SFF, FNA/QUAL, or FASTA/QUAL Files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. figure::  split_libraries.png
   :align:   center
   
* **Per-sample vs Multiplexed FASTQ Demultiplexing**
 * **Split libraries FASTQ**: Converts the raw FASTQ data into the file format used by Qiita for further analysis
  * **Input data** (required): Data being split
  * **Parameter Set** (required): Chooses the parameters for how to split the libraries
   * **Multiplexed FASTQ; generic 5 base pair barcodes**: Uses first 5 base pairs to identifies samples from FASTQ from multiple samples
   * **Multiplexed FASTQ; generic 5 base pair barcodes with Phred quality threshold: 0** [26](..//references.rst): Uses first 5 base pairs to identifies samples from FASTQ from multiple samples, only use samples with Phred quality score above 0
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
   * **Multiplexed FASTQ; Golay 12 base pair barcodes** [31](..//references.rst),[12](..//references.rst): Error correcting for the first 12 base pairs from FASTQ from multiple samples
   * **Multiplexed FASTQ; Golay 12 base pair barcodes with Phred offset: 33** [12](..//references.rst), [26](..//references.rst), [31](..//references.rst): Error correcting for the first 12 base pairs from FASTQ from multiple samples, uses Phred offset: 33 for measuring quality
   * **Multiplexed FASTQ; Golay 12 base pair barcodes with Phred offset: 64** [12](..//references.rst), [26](..//references.rst), [31](..//references.rst): Error correcting for the first 12 base pairs from FASTQ from multiple samples, uses Phred offset: 64 for measuring quality
   * **Multiplexed FASTQ; Golay 12 base pair reverse complement barcodes** [12](..//references.rst),[31](..//references.rst): Error correcting for the complementary base pairs to the last 12 base pairs in reverse order to identify samples from FASTQ from multiple samples
   * **Multiplexed FASTQ; Golay 12 base pair reverse complement barcodes with Phred offset: 33**[12](..//references.rst), [26](..//references.rst), [31](..//references.rst): Error correcting for the complementary base pairs to the last 12 base pairs in reverse order to identify samples from FASTQ from multiple samples, uses Phred offset: 33 for measuring quality
   * **Multiplexed FASTQ; Golay 12 base pair reverse complement barcodes with Phred offset: 64** [12](..//references.rst), [26](..//references.rst), [31](..//references.rst): Error correcting for the complementary base pairs to the last 12 base pairs in reverse order to identify samples from FASTQ from multiple samples, uses Phred offset: 64 for measuring quality
   * **Multiplexed FASTQ; Golay 12 base pair reverse complement mapping file barcodes with reverse complement barcodes (UCSD CMI standard)** [12](..//references.rst),[31](..//references.rst): Error correcting for the complementary base pairs to the last 12 base pairs in reverse order to identify samples from FASTQ from multiple samples
   * **Per-sample FASTQ defaults** (auto detect): Error detection for the FASTQ from 1 sample
   * **Per-sample FASTQs; Phred offset: 33** [26](..//references.rst): Error detection for the FASTQ from 1 sample, uses Phred offset: 33 for measuring quality
   * **Per-sample FASTQs; Phred offset: 64** [26](..//references.rst): Error detection for the FASTQ from 1 sample, uses Phred offset: 64 for measuring quality
    * For informtion regarding FASTQ formats please go to the `FASTQ wikipedia page  <https://en.wikipedia.org/wiki/FASTQ_format>`__.
   * For more information regarding Demultiplexing please go to the `Multiplexed wikipedia page  <https://en.wikipedia.org/wiki/Multiplexing>`__. 
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
----------
*Note that sff data cannot be deblurred*

.. figure::  trimming.png
   :align:   center
   
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
**Command from Trimmed Artifact**:

.. figure::  deblurring.png
   :align:   center
   
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
* **Deblur 16S Only Table** [2](..//references.rst): Only contains 16S deblurred sequences 
* **Deblur Final Table** [2](..//references.rst): Contains all the sequences.

Deblur Quality Filtering
~~~~~~~~~~~~~~~~~~~~~~~~

Looking for information about debluring? Please see the document here:

.. toctree::
   :maxdepth: 1

   deblur_quality.rst
   
Closed-Reference OTU Picking
----------------------------

.. figure::  closed_reference.png
   :align:   center
   
* **Pick Closed-Reference OTUs** [19](..//references.rst): Removes sequences that do not match those found in a database
 * **Input data** (required): Data being close referenced 
 * **Parameter Set** (required): Chooses the database to be compared to
  * **16S OTU Picking**:
   * **Defaults**: Compares to Greengenes 16S Database [61](..//references.rst)
   * **Defaults-parallel**: Compares to GreenGenes 16S database [61](..//references.rst) but performs it with multi-threading
  * **18S OTU Picking**:
   * **Silva 119**: Compares to Silva 119 Database [76](..//references.rst)
  * **ITS OTU Picking**:
   * **UNITE 7**: Compares to UNITE Database [1](..//references.rst)
 * **Default Parameters** (required)
  * **Reference-seq** (required): Path to blast database (Greengenes [61](..//references.rst), Silva 119 [76](..//references.rst), UNITE 7) [1](..//references.rst) as a fasta file
  * **Reference-tax** (required): Path to corresponding taxonomy file (Greengenes [61](..//references.rst), Silva 119 [76](..//references.rst), UNITE 7 [1](..//references.rst))
  * **Similarity** (required): Sequence similarity threshold
  * **Sortmerna coverage** [48](..//references.rst)(required): Minimum percent query coverage (of an alignment) to consider a hit, expressed as a fraction between 0 and 1 
  * **Sortmerna e_value** [48](..//references.rst)(required): Maximum e-value when clustering (local sequence alignment tool for filtering, mapping, and OTU picking) can expect to see by chance when searching a database
  * **Sortmerna max-pos** [48](..//references.rst)(required): Maximum number of positions per seed to store in the indexed database
  * **Threads** (required): Number of threads to use per job

Processing Recommendations
~~~~~~~~~~~~~~~~~~~~~~~~~~

Looking for information about processing data? Please see the document here:

.. toctree::
   :maxdepth: 1

   processing-recommendations.rst
