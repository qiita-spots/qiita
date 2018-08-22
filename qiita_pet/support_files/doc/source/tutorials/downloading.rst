.. _downloading:

.. index:: downloading

Downloading From Qiita
======================

Qiita allows users to download public data as well as the user's own private
data. This data can then be used for processing and analysis in external tools.

Downloading All Public Data
---------------------------

Users can download all public studies on Qiita. To do this, users can select
"Downloads" from the center of the toolbar located on the top of the screen.
This will download a zip file with each study and their respective processed
BIOM tables. *Note that this does not download any BIOM tables after the
processing steps (BIOM tables from analyses).*

Download Processed Data
-----------------------

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

Finding Samples Based On Their Metadata
---------------------------------------

For help on doing complex searches for samples go to :doc:`../redbiom`. Redbiom
helps users find samples based on their metadata, a specific taxon or feature
of interest via a simple Qiita GUI or the command line (more powerful).

Moving Your Analysis From Qiita to QIIME2
-----------------------------------------

After downloading your Qiita data, you can continue your analysis in QIIME2.
For information on transfering your data, visit the
`Transferring Qiita Artifacts to QIIME2 <https://forum.qiime2.org/t/transferring-qiita-artifacts-to-qiime2/4790>`__
QIIME2 community tutorial page.
