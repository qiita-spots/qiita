In order to ensure a direct comparability between studies, Qiita
enforces the usage of raw data files as the main input file, this is,
sequence files as they come out of the sequencing instrument. However
there are many reasons why this is not always possible and thus we've
created the following guides to help you overcome this limitation and be
able to use Qiita to process your data files.

.. note::
   Please note that most of these guides assume you have a working
   `QIIME <http://www.qiime.org>`__ installation and basic knowledge on the
   usage of the command line.


Per sample FASTQ files with barcode information
===============================================

Due to the nature of Qiita this is the prefered way to add per sample files.

In this example we assume we are working with uncompressed per-sample
FASTQ files. Thus before we begin, we have to make sure that we separate
the data in two folders ``forward`` for forward reads and ``reverse``
for the reverse reads. **Note** that there are some sequencing protocols
that will not yield reverse reads, so don't worry if you don't have them
and feel free to ignore the steps referring to the reverse reads.

First thing is to extract the barcodes from the sequence files and store
them in a per-sample location:

.. code:: bash

    for i in `ls forward/*.fastq`; do extract_barcodes.py -f ${i} -c barcode_in_label --bc1_len "length_of_your_barcode" -o barcodes/${i}; done

Once we have all the barcode files we should concatenate them into a
single ``barcodes.fastq`` file.

.. code:: bash

    cat barcode/*/* > barcodes.fastq

To create the forward reads file ``forward.fastq`` and the reverse reads
file ``reverse.fastq``, we just need to concatenate the files. In the
following example we assume all of our forward reads are in a folder
named ``forward`` and all of our reverse reads are in a folder named
``reverse``:

.. code:: bash

    cat forward/*.fastq > forward.fastq
    cat reverse/*.fastq > reverse.fastq

While you don't have to compress the generated files, it will make data
transfer and storage more convenient, the preferred and only supported
compression program to use is ``gzip``:

.. code:: bash

    # this compress barcodes.fastq, forward.fastq and reverse.fastq and create
    # new files, named barcodes.fastq.gz, forward.fastq.gz and revers.fastq.gz
    gzip *.fastq


.. _per_sample_fastq_files_without_barcode_or_primer_information:

Per sample FASTQ files without barcode and primer information
=============================================================

In this example we assume we are working with uncompressed per-sample FASTQ
files and that they do not have any barcode or primer information. This file type
normally is what you can download from `Illumina's BaseSpace <https://basespace.illumina.com/home/index>`__.


The current system allows to upload this kind of files. The only requirement is
that the prep template should have the uploaded sequence file(s) name in the
run_prefix field. This should be an exact match without extension (fastq or
fastq.gz). For example, if your uploaded file is named sample1_L001_R1.fastq.gz
you will need to have sample1_L001_R1 as the run_prefix.


Per sample FASTQ files without barcode but with primer information
==================================================================

The current way to process this files is to remove the primer section of the
reads and follow the `Per sample FASTQ files without barcode and primer information`_
instructions after they have been removed.

To remove the primer information we will use `extract_barcodes.py <http://qiime.org/scripts/extract_barcodes.html>`__
and pass the size of the primer as the barcode and simply discard the barcode
files created during this step. For this you could follow the
`Per sample FASTQ files with barcode information`_ tutorial.
