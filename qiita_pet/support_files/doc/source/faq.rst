Frequently Asked Questions
==========================

What kind of data can I upload to Qiita for processing?
-------------------------------------------------------

We need 3 things: raw data, sample template, and prep template. At this
moment, raw data is fastq files without demultiplexing with forward,
reverse (optional) and barcode reads. We should have before the end of
the week SFF processing so it's OK to upload. Note that we are accepting
any kind of target gene (16S, 18S, ITS, whatever) as long as they have
some kind of demultiplexing strategy and that you can also upload WGS.
However, WGS processing is not ready.

What's the difference between a sample and a prep template?
-----------------------------------------------------------

Sample template is the information about your samples, including
environmental and other important information about them. The prep
template is basically what kind of wet lab work all or a subset of the
samples had. If you collected 100 samples, you are going to need 100
rows in your sample template describing each of them, this includes
blanks, etc. Then you prepared 95 of them for 16S and 50 of them for
18S. Thus, you are going to need 2 prep templates: one with 95 rows
describing the preparation for 16S, and another one with 50 to
describing the 18S. For a more complex example go
`here <#h.eddzjlm5e6l6>`__ and for examples of these files you can go to
the "Upload instructions"
`here <https://www.google.com/url?q=https%3A%2F%2Fvamps.mbl.edu%2Fmobe_workshop%2Fwiki%2Findex.php%2FMain_Page&sa=D&sntz=1&usg=AFQjCNE4PTOKIvFNlWtHmJyLLy11mfzF8A>`__.

Example study processing workflow
---------------------------------

A few more instructions: for the example above the workflow should be:

#. Create a new study
#. Add a sample template, you can add 1, try to process it and the
   system will let you know if you have errors or missing columns. The
   most common errors are: the sample name column should be named
   sample\_name, duplicated sample names are not permitted, and the prep
   template should contain all the samples in the sample template or a
   subset. Finally, if you haven't processed your sample templates and
   can add a column to your template named sloan\_status with this info:
   SLOAN (funded by Sloan), SLOAN\_COMPATIBLE (not Sloan funded but with
   compatible metadata, usually public), NOT\_SLOAN (not included i.e.
   private study), that will be great!
#. Add a raw data. Depending on your barcoding/sequencing strategy you
   might need 1 or 2 raw datas for the example above. If you have two
   different fastq file sets (forward, reverse (optional) and barcodes)
   you will need two raw datas but if you only have one set, you only
   need one.
#. You can link your raw data to your files
#. You can add a prep template to your raw data. If you have the case
   with only one fastq set (forward, reverse (optional) and barcodes),
   you can add 2 different prep templates. Common missing fields here
   are: emp\_status, center\_name, run\_prefix, platform,
   library\_construction\_protocol, experiment\_design\_description,
   center\_project\_name. Note that if you get a 500 error at this stage
   is highly probable because emp\_status only accepts 3 values: 'EMP',
   'EMP\_Processed', 'NOT\_EMP', if errors persist please do not
   hesitate to contact us.
#. You can preprocess your files. For target gene, this means
   demultiplexing and QC.

