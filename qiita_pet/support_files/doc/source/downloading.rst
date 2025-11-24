.. _downloading:

.. index:: downloading

Downloading From Qiita
======================

Qiita provides convenient ways to access its data while keeping the data private
based on the owners data permission. For example, the owner decides when the data
becomes public and if the raw data is available for public download.

For an owner to make their study raw data available the owner needs to make the
artifacts public and select "Allow Qiita users to download raw data files" from
the main study page.

.. note::
   - All Qiita downloads are zip files but the name of the file will change based
     on the tool you use to download them. For example if you are using wget,
     we recommend adding the URL in quotes and using the -O flag to save the
     file with a correct name; like this:
     `wget "your-qiita-URL" -O your_filename.zip`.
   - The downloaded zip file is a dump of our storage with the data you requested
     organized by the data type. This is, when unzipped the contents will be
     in folders by the type (`mapping_file, BIOM, per_sample_FASTQ, processed_data,
     etc`) and within each you will have (a) folder(s) with the artifact id(s) download;
     each of these folders will have the files of that artifact: `biom, txt, fastq.gz,
     index.html, etc.`

Downloading All Public Data in BIOM format
------------------------------------------

**requires to be log into the system**

Users can download all public studies on Qiita. To do this, users can select
"Downloads" from the center of the toolbar located on the top of the screen.
This will download a zip file with each study and their respective processed
BIOM tables. *Note that this does not download any BIOM tables after the
processing steps (BIOM tables from analyses).*

Download Processed Data
-----------------------

**requires to be log into the system**

Users can download unprocessed or processed data from a single study. To do
this, user's go to the "View Studies Page" by selecting "View Studies" on the
"Studies" drop-down menu on the toolbar. Here, users can view their own
studies as well as all of Qiita's public studies. By clicking on the title of
the study, users will be brought to the study's "Study Information" page. By
selecting the data type as well as the specific preparation information that
the user wants to study, they will be brought to the "Processing Network" page.
On this page, users will see the study's data, unprocessed and/or processed.
When the user selects their desired artifact, a list of "Available files" will
appear below. These files can include FASTQ, FASTA, and BIOM table files that
can be further processed and/or analyzed outside of Qiita.

Download Analyzed Data
----------------------

**requires to be log into the system**

Users can download analyzed data from an analysis of a single study or from a
meta-analysis of multiple studies. To do this, user's go to the
"View Analysis Page" by selecting "See Previous Analyses" on the "Analysis"
drop-down menu on the tool bar. Here, users can view their own analyses as
well as all of Qiita's public analyses. By clicking on the name of the
analysis, users will be brought to the analysis' "Processing Network" page.
On this page, users will see the analysis's data, processed and analyzed. When
the user selects their desired artifact, a list of "Available files" will
appear below. These files can include distance matrixes, PCoA, visualization,
other resulting files. These can be download from here and further analyzed
outside of Qiita.

Access a public study or artifact without login
-----------------------------------------------

**no log required / wget or curl friendly**

To display the study or artifact information within Qiita you can (do not
forget to replace study-id or artifact-id):

- Study: https://qiita.ucsd.edu/public/?study_id=study-id
- Artifact: https://qiita.ucsd.edu/public/?artifact_id=artifact-id

Now, if you would like to download any give artifact you can (do not forget to
replace artifact-id):

- https://qiita.ucsd.edu/public_artifact_download/?artifact_id=artifact-id


Access non-public artifacts without a login
-------------------------------------------

**no log required / wget or curl friendly**

This feature is currently only available for non-public artifacts. To create a link you
must be the owner of the study that contains the artifact. To generate the link
visit the artifact you want to download and click on "Generate Download Link"; this will
generate a unique link for that artifact. Note that for an artifact that belongs to a study,
you first need to got to that study, then click on the data type (16S, Metagenomic, etc) you
want to download, click on the specific preparation and then click on the triangle (artifact)
you want to download. For analyses, go to your analysis of interest and click on the artifact
you want to download.

Download metadata, raw or all BIOM files from a study
-----------------------------------------------------

**no log required / wget or curl friendly**

We provide direct access to public data via a single end point. This end point
can be used to download BIOMs or raw data. Do not forget to replace `study-id`,
`prep_id` and/or `data_type` for your study, preparation or data type of interest:

- All raw data: https://qiita.ucsd.edu/public_download/?data=raw&study_id=study-id
- All BIOMs + mapping files: https://qiita.ucsd.edu/public_download/?data=biom&study_id=study-id
- Only 16S raw data: https://qiita.ucsd.edu/public_download/?data=raw&study_id=study-id&data_type=16S
- Only Metagenomic BIOMs + mapping files: https://qiita.ucsd.edu/public_download/?data=biom&study_id=study-id&data_type=Metagenomic
- Only the sample information file: https://qiita.ucsd.edu/public_download/?data=sample_information&study_id=study-id
- Only the preparation information file: https://qiita.ucsd.edu/public_download/?data=prep_information&prep_id=prep-id
- Raw data for a given preparation: https://qiita.ucsd.edu/public_download/?data=raw&prep_id=prep-id
- BIOM data for a given preparation: https://qiita.ucsd.edu/public_download/?data=biom&prep_id=prep-id

Note that if you are downloading raw data, the owner should have made that data
available by selecting "Allow Qiita users to download raw data files" in
the main study page. Every artifact contained in the download zip file is paired
with a mapping file to facilitate subsequent processing; the pairing is based
off the artifact ID and is present in the artifact and metadata filenames.

Finding Samples Based On Their Metadata
---------------------------------------

For help on doing complex searches for samples go to :doc:`./redbiom`. Redbiom
helps users find samples based on their metadata, a specific taxon or feature
of interest via a simple Qiita GUI or the command line (more powerful).

Moving Your Analysis From Qiita to QIIME2
-----------------------------------------

After downloading your Qiita data, you can continue your analysis in QIIME2.
For information on transfering your data, visit the
`Transferring Qiita Artifacts to QIIME2 <https://forum.qiime2.org/t/transferring-qiita-artifacts-to-qiime2/4790>`__
QIIME2 community tutorial page.
