Frequently Asked Questions
==========================

Qiita data disclaimer
---------------------

Qiita is a research tool, and as such, is hosted on research computing resources
maintained by the Knight Lab at the University of California San Diego.

Data privacy is a key aspect of our operations, and is strictly adhered to at
every step of the workflow. We are committed to protecting any and all
information (including sequence data) submitted to Qiita. For example, your data
is sandboxed by default upon upload, and remains private at the discretion of the
Owner (i.e., you are the Owner) of the study.

Authorizations and access associated with any given study is maintained and
controlled by the Owner of the study; importantly, this means that sharing
rights of a study within Qiita is determined solely by the Owner.

Sample IDs, and any associated metadata must be de-identified prior to submission
to Qiita. This is a requirement of our
`Terms of Use <https://qiita.ucsd.edu/iframe/?iframe=qiita-terms>`__.

A study within Qiita, and its associated sequence and metadata, can be
permanently deleted by the Owner as long as it is not public.

What kind of data can I upload to Qiita for processing?
-------------------------------------------------------

Processing in Qiita requires 3 things: raw data, sample and prep information
files. `Here <https://github.com/biocore/qiita/blob/master/README.rst#accepted-raw-files>`__
you can find a list of currently supported raw files files. Note that we are
accepting any kind of target gene (16S, 18S, ITS, whatever), Whole Genome and
Metatranscriptomic. Check our :doc:`processingdata/processing-recommendations`.


What's the difference between a sample and a prep information file?
-------------------------------------------------------------------

A sample information file describes the samples in a study, including
environmental factors relating to the associated host. The prep information
file has information on how the sample was processed in the wet lab. If you
collected 100 samples for your study, you will need 100 rows in your sample
information file describing each of them, and additional rows for blanks and other
control samples. If you prepared 95 of them for 16S and 50 of them for 18S,
you will need 2 prep information files: one with 95 rows describing the preparation
for 16S, and another one with 50 describing the 18S. For more information
visit :ref:`complex_example`.

.. _example_study_processing_workflow:


How should I split my samples within preparations?
--------------------------------------------------

This question normally comes up when you are working with per sample FASTQs as at this
stage there is no lane and run grouping within the samples.

Generally, we recommend to set a single preparation for each lane in each sequencing
run. This separation allows users to first test there are no biases within their
lanes and runs, and optionally merge them in a single analysis. For your convenience, when you
create a new analysis you can keep samples separate (default) or merge samples with matching
names in different preparations.

Another thing to consider is that once you are ready, you might want to submit to EBI-ENA
and they have a limit of 10M on the metadata that you want to submit. This limitation is a
combination of the metadata of each preparation and the sample information. For example, if
we imagine the worst case scenario, that we have in all our columns the default
'not applicable' NULL value, and that XML adds 4 times the size due to its formatting (how
EBI-ENA expects the submission); then we will have `len('not applicable') * 50 * 4 = 2800 (2.8K)`
per sample. Thus, we cannot have more than 3.5K samples. Note that this number depends on
the number of metadata columns in your sample information file and the number of characters
in the values of each sample and metadata column.

To enforce these ideas, Qiita has a limit of 800 samples per preparation (remember, you can add as
many samples as you want to your sample information). This number was selected because is the maximum
number of unique target gene barcodes for the EMP.

Please do not hesitate to send us an email if you have questions about this.


Example study processing workflow
---------------------------------

A few more instructions: for the example above the workflow should be:

#. **Create a new study.**
#. **Add a sample information file.** You can add 1, try to process it and the
   system will let you know if you have errors or missing columns. The
   most common errors are: the sample name column should be named
   sample\_name, duplicated sample names are not permitted. For a full list of
   required fields, visit :doc:`gettingstartedguide/index`.
#. **Add a prep information file to your study for each data type.** The prep
   information file should contain all the samples in the sample information
   file or a subset. If you have more than one FASTQ file set (forward,
   reverse (optional) and barcodes) you will need to add a run_prefix column,
   see :ref:`prepare_information_files`.
   A prep information file and a QIIME compatible mapping file will
   be available for download after the prep information file is added
   successfully.
#. **Upload and link your raw data to each of your prep information files.**
   Depending on your barcoding/sequencing strategy you might need 1 or more
   raw data file sets. If you have 2 raw data sets you may have to rename one
   set so that each set has a different name. If they have the same name they
   will over-write on upload. Note that you can have one FASTQ file set linked
   to more than one prep information file.
#. **Preprocess your files.** For target gene amplicon sequencing, this will demux
   and QC. There are multiple options for preprocessing depending on the
   barcode format and the data output from the sequencing center - this may
   require a series of trial and error to establish the correct option for
   your data files. After demultiplexing a log file is generated with
   statistics about the files demultiplexed including the number of sequences
   assigned per sample.
#. **Process each of your preprocessed data types.** For target gene, this will
   perform closed OTU picking against the latest version of Greengenes and can
   be quite time consuming depending on the number of samples and the depth
   of sequencing.


.. _issues_unzip:

How to solve download or unzip errors?
--------------------------------------

Dealing with large files might be daunting but, in general, following these
instructions should make things easier. First, make sure that you have enough space
for the zip download file; if you are unsure of the size required click on the button
and your browser will show an estimate size of the download.
Second, make sure that your computer has all the sleep settings turned off;
for example, in a Mac, got to System Preferences, Energy Saver, Power Adapter and unselect
the option of "Put hard disks to sleep when possible"; don't forget to save the settings.
Third, download the file but point to the storage that you want to save your file in; using
Chrome, right click on the download button and select "Save Link As ..."; and select the
location where you have enough space (see point 1). Fourth, wait for the download to finish,
this will depend on your Internet service. Finally, unzip the file with a newer version
of zip (see below).

By the way, if you are a developer and would like to add to Qiita the possibility of resumable
downloads, we would happily welcome this contribution.

Now, when trying to open the large downloaded zip file there is a change that you will get
an error like: **"start of central directory not found; zipfile corrupt"**. This issue
arises from using old versions of zip and you need to have unzip >= 6.0.0. To check
you unzip version you can run: `unzip -v`.

To update your unzip for most operating systems you can simply use your regular package
admin program. However, for Mac we suggest using
`this version of unzip <ftp://ftp.microbio.me/pub/qiita/unzip>`__.

Additionally, there is a chance that you will see an error/warning message like this:
``extracting: BIOM/57457/all.biom bad CRC f6b2a86b (should be 38903659)``. These
messages are consequence of the zip library we are using internally and are fine to
ignore. If you want to check them, we suggest taking any of the files and generating their
CRC32 checksum; in MAC's you can run ``crc32 [filename]`` and should get the first number
in that message; for example:

.. code-block:: bash

   $ crc32 57457_all.biom
   f6b2a86b

Do you have specific Qiita questions?
-------------------------------------

Please send them to qiita.help@gmail.com; this will assure prompt responses while keeping your
information private.

Do you have general analytical questions?
-----------------------------------------

Normally these are: How can I test X factor in my samples? Why do I see this pattern?
Which statistical method better fits my question?

As you can imagine, you are not alone as this is a common problem while doing analysis.
Thus, we suggest posting your data processing questions (raw-data to feature-table) to
qiita.help@gmail.com and general-interest analytical questions (feature-table analyses) to the `QIIME2 Forum <https://forum.qiime2.org/>`__, please be sure to **add your question in the "General Discussion" category of the forum**.
This will generally ensure that your question is answered in a timely manner. There
are many users and developers monitoring the QIIME2 Forum. Posting questions in the forum
allows you to share answers with others, who may have similar questions in the future.

Do you have Meta-Analysis questions?
------------------------------------

A common thing is why do I have a given pattern in my analysis, like
PCoA plots or taxonomy summaries.

Let's start by saying, this is an open area of research so we are still
learning about the effect sizes and what matters in individual and
meta-analysis. However, there are a few good resources to help you
understand those patterns:

1. `Meta-analyses of studies of the human microbiota <https://genome.cshlp.org/content/23/10/1704>`__.

2. `Tiny microbes, enormous impacts: what matters in gut microbiome studies? <https://genomebiology.biomedcentral.com/articles/10.1186/s13059-016-1086-x>`__.

3. `Qiita: rapid, web-enabled microbiome meta-analysis <https://www.nature.com/articles/s41592-018-0141-9>`__.

4. Additionally there some posts in the Qiime2 forum that might help you, like
   `this <https://forum.qiime2.org/t/combining-datasets-with-2-sets-of-primers/3073>`__ or
   `this <https://forum.qiime2.org/t/combining-data-from-different-sequencing-centers-and-primers/4241>`__.


How to solve BIOM name errors?
------------------------------

When uploading a BIOM table, you may get an error like: **"The sample ids in the BIOM
table do not match the ones in the prep information. Please, provide the column "run_prefix"
in the prep information to map the existing sample ids to the prep information sample ids."**.
This issue arises if your sample names in your BIOM table do not match with the sample names
in your preparation information file.

To correct this issue, simply add a column to your preparation information file named
"run_prefix". In this column, add the sample names from your BIOM table that matches the sample
names listed in the sample_name column in your preparation information file.

As a reminder, direct BIOM uploads cannot become public in the system.


What's a Qiita Artifact?
------------------------

A Qiita artifact is a collection of files and their summaries that represent the output
or input of a processing or analytical command.

For example a per_sample_FASTQ artifact will contain the per sample FASTQ files and their
summary (if a user generated); while a BIOM artifact has the feature table as a biom file, a
QIIME2 QZA, any other supporting files (like a phylogenetic tree for deblur or sortmerna_picked_otus.tgz
for close reference picking), and summaries.


How to convert Qiita files to QIIME2 artifacts?
-----------------------------------------------

As a reminder, Qiita and QIIME 2 artifacts are similar as they encapsulate multiple files. However, a big
difference is that QIIME 2 only has 2 main artifact types: QZA (all kinds of files) and QZV (visualization).

Here is quick reference conversion table, but please visit the `Transferring Qiita Artifacts to Qiime2 Tutorial <https://forum.qiime2.org/t/transferring-qiita-artifacts-to-qiime2/4790>`__
in the `QIIME2 forum <https://forum.qiime2.org>`__. for more details:

+----------------------------+----------------------------------------------------------------------+
| Qiita                      | QIIME 2                                                              |
+============================+======================================================================+
| beta diversity .tsv        | DistanceMatrix (QZA)                                                 |
+----------------------------+----------------------------------------------------------------------+
| FASTA sequence files       | FeatureData[Taxonomy | Sequence] (QZA)                               |
+----------------------------+----------------------------------------------------------------------+
| .biom tables               | FeatureTable[Frequency | RelativeFrequency | PresenceAbsence] (QZA)  |
+----------------------------+----------------------------------------------------------------------+
| ordination .txt            | PCoAResults (QZA)                                                    |
+----------------------------+----------------------------------------------------------------------+
| phylogentic tree .txt      | Phylogeny[Rooted] (QZA)                                              |
+----------------------------+----------------------------------------------------------------------+
| alpha diversity .tsv       | SampleData[AlphaDiversity] (QZA)                                     |
+----------------------------+----------------------------------------------------------------------+
| taxonomic classifier       | Taxonomic Classifier (QZA)                                           |
+----------------------------+----------------------------------------------------------------------+
| all QIIME 2 visualizations | Visualization (QZV)                                                  |
+----------------------------+----------------------------------------------------------------------+

Note that all feature table (bioms) and analytical steps will generate QZA and QZV, which are native QIIME2 artifacts.


How to add extra files to a Qiita study?
----------------------------------------

Many publications rely on extra files that are not part or
generated within Qiita. However, to facilitate analytical reproducibility a user
might like to link these files to Qiita. In this case, we recommend to upload
your external file to a long term repository, like
`figshare.com <https://figshare.com/>`__, and then link to your study via the
"Analytical Notes" within a study. The "Analytical Notes" section can be accessed
within the study "Edit" button. Note that this text box renders Markdown when
displayed in the study section. Markdown allows to format text, add images,
etc; for more information check
`this 3 minute read about Markdown <https://guides.github.com/features/mastering-markdown/>`__.


Where's my QIIME1 mapping file?
-------------------------------

During the 2020.11 deployment we removed the functionality that automatically created
the merged preparation and sample information file per preparation. This change will allow us
to make faster information file updates allow for future multi-site operations.

If you want to create a merged and validated mapping file (merged sample and preparation
information file) please create an analysis by following these instructions:
:ref:`creating_a_new_analysis`.


I want to transfer a lot of files to Qiita, is there an easy way?
-----------------------------------------------------------------

Yes! This is available in the "Upload Files" section of each study by accessing the tab
"Upload via Remote Server (ADVANCED)".

We currently suggest using scp, note that your server where you store your files should allow
connecting to it via scp - in other words, this only works when moving files from a server to Qiita.

Now, the way it works is that you need to create a new secure key to that server, imagine
that you are making a copy of your storage-shed key, then you share that key to Qiita (you will give
access to Qiita to run a single copy command in your server), Qiita uses that key and securely
destroy it.

To take advantage of this feature you need to:

#. Prepare all the files you want to transfer in a single folder (or you can transfer
   multiple times from multiple folders into one study). Note that Qiita will only collect
   files with valid extensions from the top level directory (no sub-directories); see the
   top of the "Upload Files" page within your study for the latests list of valid extensions.
#. In your server (this needs to be run within your home directory in the server where you
   store the files!), generate a new key by running:
   `ssh-keygen -t rsa -C "ssh test key" -f ~/.ssh/qiita-key -P ""`. Here is where you are
   creating that key to your storage-shed.
#. Allow access using the new key to new connections (this also needs to be run in the
   remote server): `cat ~/.ssh/qiita-key.pub >> ~/.ssh/authorized_keys`. This tells the
   server that is OK to give access to the key created to your storage-shed; note that if
   you want to completely stop that key to work you can open that file and remove the line
   with the name of this key.
#. Download your new generated key `qiita-key` (the file) to your local computer and use it
   in the `Key` option of "Upload via Remote Server (ADVANCED)".

Using this key you can `List Files` to test the connection and verify the list of study files. Then,
if the connection is made and files are correct, press 'Transfer Files' to initiate the transfer.

Note that if you click multiple times, too quickly there is a chance that your server will block
Qiita, if this happens, just wait a few minutes and retry again.


How do I update the sample or preparation file?
-----------------------------------------------

Remember, these are separate files so they need to be updated separately. In both cases,
the easiest is to upload the new file from your computer to Qiita using the `Upload Files`
button in your study. Once the file you want to use is there you can use them within Qiita.

To update a sample information file: Click on `Sample Information` button in the your study
page, then use the `Update sample information` section on that page to select your file and
update it. Note that for this you can also directly upload your file via the
`Direct upload file (< 2MB)`.

To update a preparation information file: Click on the preparation you want to update within
your study page, then click on `Summary`, and use the `Update prep information` section on
that page to select your file and update it.

Note that these information is generally independent of the sequence processing so you
don't need to reprocess your sequences; however, if you use your study in an analysis, you will
need to recreate that analysis to use the updated sample or preparation metadata


When do I need the run_prefix in my preparation information file?
-----------------------------------------------------------------

It depends on your sequence processing but in general it will facilitate loading your
files to your preparation in Qiita.

First of all, this is a prefix value so you only need the beginning of the file
name to load the files in Qiita; for example if your file names for a given sample are:
AWERWADFA_I1.fastq.gz, AWERWADFA_R1.fastq.gz, AWERWADFA_R2.fastq.gz, the run_prefix for
the sample should be AWERWADFA. Qiita will use that to group those files under the same
sample with that run_prefix.

Now the run_prefix is used constantly within file selection and processing in all file types but
specially on:

- BIOM: the run_prefix is used to rename the samples in your BIOM to match the sample names
  in Qiita. Basically, if you add the sample names in your BIOM file as the run_prefix and the
  sample name in Qiita in the sample_name column of your preparation, Qiita will automatically
  rename them to match.
- per sample FASTQ: run_prefix is the way to link which sample goes with which files so using here
  will facilitate loading your files to the preparation and then used for processing, without it
  Qiita will not be able to process your samples.


Loading an existing study/project from EBI-ENA to Qiita.
--------------------------------------------------------

If you want us to load a study into Qiita, please complete `this form <https://docs.google.com/forms/d/1SIq_JNWai7cZ2wwjD8xZpTab7qBifLKu3TZm2B363CE/edit?ts=5fbe8c0b&gxids=7628>`__
and send us an email to qiita.help@gmail.com. Then, a Qiita Admin will download your requested studies
using https://github.com/ucsd-cmi/qebil and then loading into Qiita using
https://github.com/qiita-spots/qiita/pull/3112. Note that as this is still
not automatic, only an admin can do this. However, we ask the user requesting
the studies to help us fix the metadata - try to make as close as possible to
:ref:`checklist-for-ebi-ena-submission` so we can open them to other users. qebil
will download the associated metadata from EBI-ENA but in our experience this
is not close to Qiita requirements and thus, we request your help in amending
the metadata.


Software and Data Licensing
---------------------------

Qiita's software and its plugins can be found here: https://github.com/qiita-spots/. They are
distributed with a BSD 3-Clause License. When you use the `Qiita WebServer <https://qiita.ucsd.edu/>`__,
you are adhering to the `Qiita Terms <https://qiita.ucsd.edu/iframe/?iframe=qiita-terms>`__. All data
downloaded from `qiita.ucsd.edu <https://qiita.ucsd.edu/>` and redbiom, including raw and processed data
and metadata, are distributed under the BSD 3-Clause License.


Some of the studies have `Qiita-EBI Import` as the PI, why is this?
-------------------------------------------------------------------

These are studies that were downloaded to Qiita via `qebil <https://github.com/ucsd-cmi/qebil>`. If you want
us to add your study, please send us an email.

Now, if you are wondering about the possible "Processing notes", here are their explanation:

-  MISSING: One or more of the fastq files for your study were unavailable for download from
   EBI/ENA or the downloaded files were found to contain corrupt data and were excluded from our
   automatic association and processing. A list of the affected samples and their corresponding
   EBI/ENA ftp links can be found in the .MISSING. preparation information files in the Uploads
   section of this page. If you would like to attempt to manually download and/or correct the
   fastq files, please visit the linked EBI/ENA project page in the Study details and follow our
   instructions for manually associating and processing the files.

- TOOMANYREADS: One or more of the fastq files for your study were found to contain more read
  files than indicated by the single or paired-end read technology that EBI/ENA indicated was
  used for processing the sample. This is most likely the case for studies where index reads
  have been included in a separate file as part of the upload, however our automated system
  is unable to readily distinguish this. A list of the affected samples and their corresponding
  EBI/ENA ftp links can be found in the .TOOMANYREADS. preparation information files in the
  Uploads section of this page. If you would like to attempt to have these samples processed,
  please visit the linked EBI/ENA project page in the Study details and either a) follow our
  instructions for manually associating and processing the files here or b) email us to
  indicate that the study should be processed with the assumption that the first file
  associated with a samples is an index read file.


Are you planning a workshop or class?
-------------------------------------------------------------------

We encourage users to use Qiita for their classes and/or workshops and to facilitate processing
we urge them to request a special reservation in the system. A reservation should help your
and your participant jobs to move quicker in the system. If you are interested, please send us
an email to qiita.help@gmail.com and add the name of your workshop/course, the number of
participants, the expected days this will happen. Note that reservations are only available for
analysis and not for sequencing processing, and that the reservation can be added/edited during
the creation of the analysis or at any point within each individual analysis page.

You can add the reservation string to the analysis at the time of creation (bottom of the creation
page), or the analysis page via the reservation button (top right). Note that once the reservation
time finishes, your jobs will fail as the reservation will no longer exist so you will need to
remove it - we suggest doing this before submitting new jobs.

How to cite Qiita?
------------------

If you use Qiita for processing, submission to EBI-ENA and/or its data for any published research, please include the following citation:

**Qiita: rapid, web-enabled microbiome meta-analysis.**
Antonio Gonzalez, Jose A. Navas-Molina, Tomasz Kosciolek, Daniel McDonald, Yoshiki Vázquez-Baeza, Gail Ackermann, Jeff DeReus, Stefan Janssen, Austin D. Swafford, Stephanie B. Orchanian, Jon G. Sanders, Joshua Shorenstein, Hannes Holste, Semar Petrus, Adam Robbins-Pianka, Colin J. Brislawn, Mingxun Wang, Jai Ram Rideout, Evan Bolyen, Matthew Dillon, J. Gregory Caporaso, Pieter C. Dorrestein & Rob Knight. Nature Methods, volume 15, pages 796–798 (2018);
`https://doi.org/10.1038/s41592-018-0141-9 <https://doi.org/10.1038/s41592-018-0141-9>`__.
