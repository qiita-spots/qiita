.. _join-paired-end-reads:

.. index:: join-paired-end-reads

Join paired end reads
=====================

Having high quality, longer reads helps with taxonomy assignment and classification.
Thus, if your forward and reverse reads overlap you should join them. Note that this
is not currently possible automatically in Qiita but we will be adding this
functionality in the future.

.. note::
   Please note that most of these guides assume you have a working
   `QIIME <http://www.qiime.org>`__ installation and basic knowledge on the
   usage of the command line.

Joining forward and reverse reads for raw files
-----------------------------------------------

You could use `join_paired_ends.py <http://qiime.org/scripts/join_paired_ends.html>`__
and then upload your joined sequence and barcode files for processing. Then you
will upload the resulting joined file to Qiita.

.. _join_forward_and_reverse_reads_for_per_sample_fastq_files_without_barcodes_and_primers:

Joining forward and reverse reads for per sample FASTQ files without barcodes and primers
-----------------------------------------------------------------------------------------

You could use `multiple_join_paired_ends.py <http://qiime.org/scripts/multiple_join_paired_ends.html>`__
and then upload your joined sequence and barcode files for processing. Then you
will upload the resulting joined per sample files to Qiita.


.. _per_sample_fastq_files_without_barcodes_but_with_primer_information_with_overlapping_regions:

Per sample FASTQ files without barcodes but with primer information with overlapping regions
--------------------------------------------------------------------------------------------

To process this kind of files you will need to run two steps:

#. Run multiple_join_paired_ends.py to stitch the reads. See
   `multiple_join_paired_ends.py <http://qiime.org/scripts/multiple_join_paired_ends.html>`__.
#. Run multiple_extract_barcodes.py to strip out the primers. You will need to use a
   parameter file with:

   .. code:: bash

     extract_barcodes:input_type barcode_paired_stitched
     extract_barcodes:bc1_len X
     extract_barcodes:bc2_len Y

Be sure to replace `X` and `Y` for your actual values.

These steps will generate a folder per sample, each with 2 files: the reads and
the barcodes. You will need to upload just the reads and ignore the generated barcode
files.
