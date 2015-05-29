# Qiita changelog


Qiita 0.1.0-dev (changes since Qiita 0.1.0 go here)
---------------------------------------------------

* Creating an empty RawData is no longer needed in order to add a PrepTemplate.
Now, the PrepTemplate is required in order to add a RawData to a study. This is
the normal flow of a study, as the PrepTemplate information is usually
available before the RawData information is available.
* A user can upload a QIIME mapping file instead of a SampleTemplate. The
system will create a SampleTemplate and a PrepTemplate from the information
present in the QIIME mapping file. The QIIME required columns for this
functionality to work are 'BarcodeSequence', 'LinkerPrimerSequence' and
'Description'. For more information about QIIME mapping files, visit
http://qiime.org/documentation/file_formats.html#mapping-file-overview.

Version 0.1.0 (2015-04-30)
--------------------------

Initial alpha release.
