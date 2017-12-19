Creating an Account
===================
*  **Sign up**: Brings you to window to create an account
Home Screen
-----------
* **Icons** (located on top right corner)
 * **Envelope Icon** (3rd from the right): Your system messages
 * **Clipboard Icon** (2nd from the right): Your selected samples
 * **Server Icon** (rightmost): Your active jobs and their statuses
Creating a Study
==============
* **Creating a New Study/Edit Study Page**
 * **Study Title** (required): Name of the experiment
 * **Study Alias** (required): A different name to put your experiment under
 * **DOI (optional)**: Not required but if your paper has already been published you will be given a DOI, or Digital Object Identifier, that scientists can use to find your paper
 * **PubMed ID** (optional): Not required but if your paper has been published in PubMed it will be given a designated PubMed ID that scientists can use to help find your paper
 * **Study Abstract** (required): Abstract for your experiment
 * **Study Description** (required): Quick description of your study, shorter than the abstract
 * **Principal Investigator** (required): Whose lab it is
 * **Lab Person** (optional): Who to contact if you have questions about the experiment
 * **Environmental Packages** (optional): Describing the environment from which a biological sample originates
  * To find out which type of sample you have read this paper found in `Nature <http://www.nature.com/nbt/journal/v29/n5/full/nbt.1823.html>`__.
 * **Event-Based Data** (optional): If your experiment contained interventions you can include that here
* **Study Information Page**
 * **Edit**: Brings you to the Edit Study Page if you wanted to update your study
 * **Study tags** (optional): Keywords that will help you, and others, find your study in Qiita
  * For example, if you’re studying soil you can add that as a tag
  * Must **Save tags** To keep them otherwise they dissapear
 * **Sample Information**: A link to your metadata summary 
 * **Upload Files**: A link to a screen to upload your files to
 * **Sample Summary**: A link to a screen to view each sample separately with their respective metadata
Editing a Study
----------------
*  Go to the “Study Information Page”
*  Select “Edit” from “Study Information Page” to bring you to “Edit Study Page”
*  Make the desired edits and select “Update Study”

Adding and Working With Sample information
==========================================
Creating the Sample Information File
------------------------------------
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

+----------------------------------+-------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------+
| Field name                       | Format                  | Description                                                                                                                                         |
+==================================+=========================+=====================================================================================================================================================+
| ``collection_timestamp``         | ``yyyy-mm-dd hh:mm:ss`` | The time stamp (preferred) of when the sample was collected. Several format are accepted, all ISO 8601.                                             |
|                                  | or ``yyyy-mm-dd hh:mm`` |                                                                                                                                                     |
|                                  | or ``yyyy-mm-dd hh``    |                                                                                                                                                     |
|                                  | or ``yyyy-mm-dd ``      |                                                                                                                                                     |
|                                  | or ``yyyy-mm``          |                                                                                                                                                     |
|                                  | or ``yyyy``.            |                                                                                                                                                     |
|                                  | Years are only          |                                                                                                                                                     |
|                                  | supported as 4 ``yyyy`` |                                                                                                                                                     |
|                                  | digits                  |                                                                                                                                                     |
+----------------------------------+-------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------+
| ``physical_specimen_location``   | free text               | Where you would go to find physical sample or DNA, regardless of whether it is still available or not.                                              |
+----------------------------------+-------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------+
| ``taxon_id``                     | integer                 | NCBI taxon ID for the sample. Should indicate metagenome being investigated. Examples: 410658 for soil metagenome, 749906 for gut metagenome,       |
|                                  |                         | 256318 for metagenome (used for unspecified or blanks). To find others visit `NCBI Taxonomy Database <http://www.ncbi.nlm.nih.gov/taxonomy>`__.     |
+----------------------------------+-------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------+
| ``scientific_name``              | free text               | NCBI's scientific name for the provided taxon ID. This is the name of the metagenome, not the host scientific name. Examples: soil metagenome,      |
|                                  |                         | gut metagenome, marine sediment metagenome, marine metagenome.                                                                                      |
+----------------------------------+-------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------+
| ``description``                  | free text               | Description of the sample.                                                                                                                          |
+----------------------------------+-------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------+

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
Attaching the Sample Information to the Study
---------------------------------------------

Example files
-------------

You can download an example sample information file from
`here <ftp://ftp.microbio.me/pub/qiita/sample_prep_information_files_examples.tgz>`__

EBI-ENA NULL values vocabulary
------------------------------

For all public studies including those being submitted to EBI, no blanks are allowed in the smaple information. We support the following null values: *not applicable*, *missing: not collected*, *missing: not provided*, *missing: restricted access*.

For the latest definitions and explanation visit the `EBI/ENA Missing value reporting <http://www.ebi.ac.uk/ena/about/missing-values-reporting>`__.

.. warning::
   Column names in your information files cannot be named as a Postgres reserved word. For example, a column cannot be named `CONDITION`, but could instead be named `DISEASE_CONDITION`. For a full list of these reserved words, see this `link <https://www.postgresql.org/docs/9.3/static/sql-keywords-appendix.html>`__.
   
Upload Sample Information
^^^^^^^^^^^^^^^^^^^^^^^^^

* **Upload Files Page**
 * Drag your sample info file into the box to upload your files
 * **Delete selected files**: Delete a file with the selected boxes
 * **Go to study description**: Link to the study description page

Viewing Sample Information
^^^^^^^^^^^^^^^^^^^^^^^^^^

* **Sample Information Page**
 * **Sample Info**: Downloads the metadata onto your computer
 * See different metadata values
* **Sample Summary Page**
 * **Add sample column information to table**: Allows you to add an additional metadata column to the sample summary for comparison on this page

Update Sample info
^^^^^^^^^^^^^^^^^^

* **Upload Files Page**
 * Drag new sample info file into the box to upload the new file
 * Go to study description by clicking the “Go to study description” 
* **Study Information Page**
 * Go to the sample information page by clicking the “Sample Information” 
 * You can edit your metadata here too:
  *If the data has not been processed...
   * Delete your old metadata file
   * Upload your new metadata file
  * If the data has been processed...
   * The metadata file cannot be deleted 
   * To remove data, go to the sample information page and use the trash icon to delete the unwanted sample information columns
   * You can only update the fields that do exist (these fields can be found in the sample information page)
   * Sample names cannot be deleted
    * Any sample name change will be interpreted as a new sample
  * *Note that this changes will not update on your analysis*
  * But these changes will not affect your processing data since the metadata isn’t applied until analysis
  
Adding Data for Analysis
========================

Prepare information files
-------------------------

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
-------------

You can download an example prep information file from
`here <ftp://ftp.microbio.me/pub/qiita/sample_prep_information_files_examples.tgz>`__

Attaching Prep Information
--------------------------
* **Upload Files Page**
 * Drag your prep info file into the box to upload your files
 * If you want to delete the file, press the box that appears next to that file then click delete selected files
 * **Go to study description**: Link to the study description page
* **Study Description Page**
 * Select “Add New Preparation”
Attach data
-----------
* **Upload Files Page**
 * Drag your data files into the box to upload your files
 * If you want to delete the file, press the box that appears next to that file then click delete selected files
 * **Go to study description**: Link to the study description page
* **Study Description Page**
 * Select “Add new preparation page”
* **Add New Preparation Page**
 * **Select File** (required): Select the preparatory information file you uploaded  
 * **Select Data Type** (required): Choose for what kind of data you studied
 * **Select Investigation Type** (optional): Not required, chooses the investigation you performed
 * **Create New Preparation**: Creates a new preparation based on the data inputted above
Associate data with prep
------------------------
* **Data Type**
 * Includes preparation info files of that data type that’s associated with your study
 * **16S, or the data type you studied** (required): Preparation page
 * **Select Type** (required): Select the file type you uploaded, causing Qiita to associate your files with this preparation
 * **Add a name for this file** (required): Give the file a name
 * **Add Files**: Shows up after Select Type has been chosen, adds files to the preparation
 * **Files Network**: Contains artifacts that represent your data
Update prep info
----------------
* **Data Type 16S Page**
 * Select “Update Information” and choose your updated file
 * *Barcodes and sample names cannot be updated*
  * Must create new preparation to update these

