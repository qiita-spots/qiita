Qiita (canonically pronounced *cheetah*)
========================================

|Build Status| |Coverage Status|

Advances in sequencing, proteomics, transcriptomics, metabolomics, and others are giving
us new insights into the microbial world and dramatically improving our ability
to understand their community composition and function at high resolution.
These new technologies are generating vast amounts of data, even from a single
study or sample, leading to challenges in storage, representation, analysis,
and integration of the disparate data types. Qiita was designed to allow users
address these new challenges by keeping track of multiple studies with multiple
'omics data. Additionally, Qiita is capable of supporting multiple analytical
pipelines through a 3rd-party plugin system, allowing the user to have a single
entry point for all their analyses. Qiita's main site provides database and
compute resources to the global community, alleviating the technical burdens,
such as familiarity with the command line or access to compute power, that are
typically limiting for researchers studying microbial ecology.

Qiita is currently in production/stable status. We are very open to community
contributions and feedback. If you're interested in contributing to Qiita,
see `CONTRIBUTING.md <https://github.com/qiita-spots/qiita/blob/master/CONTRIBUTING.md>`__.
If you'd like to report bugs or request features, you can do that in the
`Qiita issue tracker <https://github.com/qiita-spots/qiita/issues>`__.

To install and configure your own Qiita server, see
`INSTALL.md <https://github.com/qiita-spots/qiita/blob/master/INSTALL.md>`__. However, Qiita is not designed to be used locally but rather on a server, we therefore advise against installing your own version on a personal computer. Nevertheless, it can run just fine on a laptop or small computer for development and educational purposes. For example, for every single PR and release, we install Qiita from scratch as GitHub Actions, you can follow `these steps <https://github.com/qiita-spots/qiita/actions>`__.

For more specific details about Qiita's philosophy and design visit `the Qiita main site tutorial <https://qiita.microbio.me/static/doc/html/qiita-philosophy/index.html>`__.

Current features
----------------

* Full study management: Create, delete, update samples in the sample and
  multiple preparation information files.
* Upload files via direct drag & drop from the web interface or via scp
  from any server that allows these connections.
* Study privacy management: Sandboxed -> Private -> Public.
* Easy long-term sequence data deposition to the European Nucleotide Archive (ENA),
  part of the European Bioinformatics Institute (EBI) for private and public
  studies.
* Raw data processing for `Target Gene, Metagenomic, Metabolomic, Genome Isolates and BIOM files <https://qiita.ucsd.edu/static/doc/html/processingdata/index.html#processing-recommendations>`__. NOTE: BIOM files can be added as new preparation files for downstream analyses; however, this cannot be made public in the system.
* Basic downstream analyses using QIIME 2. Note that Qiita produces qza/qzv in the analytical steps but you can also convert `non QIIME 2 artifacts <https://qiita.ucsd.edu/static/doc/html/faq.html#how-to-convert-qiita-files-to-qiime2-artifacts>`__.
* Bulk download of `studies and artifacts <https://qiita.ucsd.edu/static/doc/html/downloading.html>`__.
* Basic study search in the study listing page.
* Complex metadata search via redbiom.

For more detailed information visit the `Qiita tutorial <https://cmi-workshop.readthedocs.io/en/latest/>`__
and the `Qiita help <https://qiita.ucsd.edu/static/doc/html/index.html>`__.

Accepted raw files
------------------

* Multiplexed SFF
* Multiplexed FASTQ: forward, reverse (optional), and barcodes
* Per sample FASTQ: forward and reverse (optional)
* Multiplexed FASTA/qual files
* Per sample FASTA, only for "Full Length Operon"


.. |Build Status| image:: https://github.com/qiita-spots/qiita/actions/workflows/qiita-ci.yml/badge.svg
   :target: https://github.com/qiita-spots/qiita/actions/workflows/qiita-ci.yml
.. |Coverage Status| image:: https://coveralls.io/repos/github/qiita-spots/qiita/badge.svg?branch=dev
   :target: https://coveralls.io/github/qiita-spots/qiita?branch=master
