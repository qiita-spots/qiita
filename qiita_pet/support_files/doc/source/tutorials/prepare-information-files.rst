.. _prepare-information-files:

.. index:: prepare-information-files

Prepare information files
=========================

The set of required fields for the *sample information* and *preparation
information files* varies based on the functionality that you want to
use from the system.

As described in :doc:`../qiita-philosophy/index`, a Qiita study can have
many biological samples, each with many preparations for different kinds of
multi-omic analysis. As described in :doc:`getting-started`, the study will
have a single *sample information file* that will define the biological context
of each sample. Each multi-omic data type prepared will have a separate
*preparation information file* that will describe the sequencing technology
or analytical chemistry used to generate that data set.

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


Example files
-------------

You can download an example sample information file and prep information file from
`here <ftp://ftp.microbio.me/pub/qiita/sample_prep_information_files_examples.tgz>`__

Sample information file
-----------------------

The *sample information file* will define the biological context of each
sample, with categories like ``sample_type``, ``treatment``,
etc. The ``sample_name`` defined in this file is used to relate each
sample in the preparation file with the biological sample.



Required fields for Qiita
~~~~~~~~~~~~~~~~~~~~~~~~~

This is the minimum set of columns for a sample information file to be added to
the system:

+-------------------+-------------------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------+
| Field name        | Format                        | Description                                                                                                                                            |
+===================+===============================+========================================================================================================================================================+
| ``sample_name``   | free text with restrictions   | Identifies a sample. It is the primary key and must be unique. Allowed characters are alphabetic ``[A-Za-z]``, numeric ``[0-9]``, and periods ``.``.   |
+-------------------+-------------------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------+

Required fields for EBI submission
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

These are the columns required for successfully submit your data to EBI:

+----------------------------------+----------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------+
| Field name                       | Format               | Description                                                                                                                                         |
+==================================+======================+=====================================================================================================================================================+
| ``collection_timestamp``         | ``mm/dd/yy hh:mm``   | Date and time with time in 24-hour format in which the sample was collected.                                                                        |
+----------------------------------+----------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------+
| ``physical_specimen_location``   | free text            | Where you would go to find physical sample or DNA, regardless of whether it is still available or not.                                              |
+----------------------------------+----------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------+
| ``taxon_id``                     | integer              | NCBI's taxon id for the sample. Note, for amplicon sequencing, this is the taxonomy id for the metagenome being targeted, not the host taxonomy id. |
+----------------------------------+----------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------+
| ``description``                  | free text            | Description of the sample.                                                                                                                          |
+----------------------------------+----------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------+
| ``scientific_name``              | free text            | NCBI's scientific name for the provided taxon ID. Note, the name of the metagenome, not the host scientific name.                                   |
+----------------------------------+----------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------+

Required fields for centralized Qiita
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

These are the columns required if you want to make your date public at
the centralized `Qiita server <http://qiita.microbio.me>`__:

+-----------------------------------+----------------------------------------------------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Field name                        | Format                                                               | Description                                                                                                                                                                                                                                                                                                                                       |
+===================================+======================================================================+===================================================================================================================================================================================================================================================================================================================================================+
| ``host_subject_id``               | free text                                                            | An identifier for the “host”. Should be specific to a host, and can be a one-to-many relationship with samples. All samples from the same source (host, sample) should have the same identifier to facilitate analysis. If this is not a host-associated study, this can be an identifier for a replicate, or can be the same as ``sample_name``. |
+-----------------------------------+----------------------------------------------------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| ``sample_type``                   | free text                                                            | Description of the type of sample.                                                                                                                                                                                                                                                                                                                |
+-----------------------------------+----------------------------------------------------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| ``physical_specimen_remaining``   | ``TRUE`` or ``FALSE``                                                | Is there still physical sample (e.g., soil, not DNA) available?                                                                                                                                                                                                                                                                                   |
+-----------------------------------+----------------------------------------------------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| ``dna_extracted``                 | ``TRUE`` or ``FALSE``                                                | Has DNA already been extracted for this sample?                                                                                                                                                                                                                                                                                                   |
+-----------------------------------+----------------------------------------------------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| ``latitude``                      | `decimal degrees <http://en.wikipedia.org/wiki/Decimal_degrees>`__   | Latitude where sample was collected.                                                                                                                                                                                                                                                                                                              |
+-----------------------------------+----------------------------------------------------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| ``longitude``                     | `decimal degrees <http://en.wikipedia.org/wiki/Decimal_degrees>`__   | Longitude where sample was collected.                                                                                                                                                                                                                                                                                                             |
+-----------------------------------+----------------------------------------------------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+

Optional fields for centralized Qiita by portal
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* Sloan, Microbiology of the Built Environment

  +------------+------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
  | Field name | Format     | Description                                                                                                                                                                   |
  +============+============+===============================================================================================================================================================================+
  | ``sloan``  | free text  | Sloan sample status. SLOAN (funded by Sloan), SLOAN_COMPATIBLE (not Sloan funded but with compatible metadata, usually public), NOT_SLOAN (not included i.e. private study).  |
  +------------+------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+

* Earth Microbiome Project

  +-------------------+------------+---------------------------------------------------------------------------------------------------------------------------------------------+
  | Field name        | Format     | Description                                                                                                                                 |
  +===================+============+=============================================================================================================================================+
  | ``emp_status``    | free text  | EMP sample status. ‘EMP’ (part of the EMP), ‘EMP_Processed’ (processed in the weblab using EMP parameters), ‘NOT_EMP’ (not EMP compatible). |
  +-------------------+------------+---------------------------------------------------------------------------------------------------------------------------------------------+

Prep information file
---------------------

The *preparation information file* will describe the wet lab technology used
to generate this data type, including sequencing, proteomics, metabolomics,
etc. A shared ``sample_name`` linkes a prepared sample to a biological
sample in the *sample information file.*

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
| ``center_name``                     | free text                                 | Name of the sequencing facility.                                                                                                                                                                               |
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

+--------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Platform     | Valid instrument_model options                                                                                                                                                                                                                                                                   |
+==============+==================================================================================================================================================================================================================================================================================================+
| ``LS454``    | ``454 GS``, ``454 GS 20``, ``454 GS FLX``, ``454 GS FLX+``, ``454 GS FLX Titanium``, ``454 GS Junior``, or ``unspecified``                                                                                                                                                                       |
+--------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| ``Illumina`` | ``Illumina Genome Analyzer``, ``Illumina Genome Analyzer II``, ``Illumina Genome Analyzer Ix``, ``Illumina HiSeq 2500``, ``Illumina HiSeq 2000``, ``Illumina HiSeq 1500``, ``Illumina HiSeq 1000``, ``Illumina MiSeq``, ``Illumina HiScanSQ``, ``HiSeq X Ten``, ``NextSeq 500``, ``unspecified`` |
+--------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+

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
