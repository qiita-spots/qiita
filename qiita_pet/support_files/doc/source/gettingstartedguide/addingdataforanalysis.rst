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

Example files
-------------

You can download an example sample information file and prep information file from
`here <ftp://ftp.microbio.me/pub/qiita/sample_prep_information_files_examples.tgz>`__

EBI-ENA NULL values vocabulary
------------------------------

We support the following values: *Not applicable*, *Missing: Not collected*, *Missing: Not provided*, *Missing: Restricted access*.

For the latest definitions and explanation visit the `EBI/ENA Missing value reporting <http://www.ebi.ac.uk/ena/about/missing-values-reporting>`__.

.. warning::
   Column names in your information files cannot be named as a Postgres reserved word. For example, a column cannot be named `CONDITION`, but could instead be named `DISEASE_CONDITION`. For a full list of these reserved words, see this `link <https://www.postgresql.org/docs/9.3/static/sql-keywords-appendix.html>`__.

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
  * must create new preparation to update these



