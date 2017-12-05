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


