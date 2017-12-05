Adding Data for Analysis
========================
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



