Frequently Asked Questions
==========================

What kind of data can I upload to Qiita for processing?
-------------------------------------------------------

Processing in Qiita requires 3 things: raw data, sample and prep information
files. `Here <https://github.com/biocore/qiita/blob/master/README.rst#accepted-raw-files>`__
you can find a list of currently supported raw files files. Note that we are
accepting any kind of target gene (16S, 18S, ITS, whatever). You can also upload
WGS however, WGS processing is not ready.

What's the difference between a sample and a prep information file?
-------------------------------------------------------------------

A sample information file describes the samples in a study, including
environmental factors relating to the associated host. The prep information
file has information on how the sample was processed in the wet lab. If you
collected 100 samples for your study, you will need 100 rows in your sample
information file describing each of them, and additional rows for blanks and other
control samples. If you prepared 95 of them for 16S and 50 of them for 18S,
you will need 2 prep information files: one with 95 rows describing the preparation
for 16S, and another one with 50 describing the 18S. For a more complex
example go
`here <#h.eddzjlm5e6l6>`__ and for examples of these files you can go to
the "Upload instructions"
`here <https://www.google.com/url?q=https%3A%2F%2Fvamps.mbl.edu%2Fmobe_workshop%2Fwiki%2Findex.php%2FMain_Page&sa=D&sntz=1&usg=AFQjCNE4PTOKIvFNlWtHmJyLLy11mfzF8A>`__.

.. _example_study_processing_workflow:

Example study processing workflow
---------------------------------

A few more instructions: for the example above the workflow should be:

#. **Create a new study.**
#. **Add a sample information file.** You can add 1, try to process it and the
   system will let you know if you have errors or missing columns. The
   most common errors are: the sample name column should be named
   sample\_name, duplicated sample names are not permitted. For a full list of
   required fields, visit :doc:`gettingstarted/gettingstarted`.
#. **Add a prep information file to your study for each data type.** The prep
   information file should contain all the samples in the sample information
   file or a subset. If you have more than one FASTQ file set (forward,
   reverse (optional) and barcodes) you will need to add a
   :ref:`run_prefix <required-fields-for-preprocessing-target-gene-data>`
   column.
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

How to solve unzip errors?
--------------------------

When downloading large zip files within Qiita there is a change that you will get
an error like: **"start of central directory not found; zipfile corrupt"**. This issue
arises from using old versions of zip and you need to have unzip >= 6.0.0. To check
you unzip version you can run: `unzip -v`.

To update your unzip for most operating systems you can simply use your regular package
admin program. However, for Mac we suggest using
`this version of unzip <ftp://ftp.microbio.me/pub/qiita/unzip>`__.
