Qiita (canonically pronounced *cheetah*)
========================================

|Build Status| |Coverage Status| |Gitter|

Advances in sequencing, proteomics, transcriptomics and metabolomics are giving
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

Qiita is currently in alpha status. We are very open to community
contributions and feedback. If you're interested in contributing to Qiita,
see `CONTRIBUTING.md <https://github.com/biocore/qiita/blob/master/CONTRIBUTING.md>`__.
If you'd like to report bugs or request features, you can do that in the
`Qiita issue tracker <https://github.com/biocore/qiita/issues>`__.

To install and configure your own Qiita server, see
`INSTALL.md <https://github.com/biocore/qiita/blob/master/INSTALL.md>`__.

For more specific details about qiita visit `the Qiita main site tutorial <https://qiita.microbio.me/static/doc/html/qiita-philosophy/index.html>`__.

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
* Raw data processing for:

  * Target gene data: we support deblur against GreenGenes (13_8) and close
    reference picking against GreenGenes (13_8) and Silva.
  * Metagenoic/Shotgun data: we support Shogun processing. Note that this data
    is suitable for download and further down stream analyses but we don't recommend
    meta-analysis within Qiita (only single study).
  * biom files can be added as new preparation templates for downstream
    analyses; however, this cannot be made public.

* Basic downstream analyses using Qiime2.
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

Roadmap
-------

The following is a non-exhaustive list of features that we plan to add in the
future.

* Integration of other pipelines via artifacts. Processing of raw data in
  external sources. For example, metabolomics processing in
  `GNPS <http://gnps.ucsd.edu>`__ and data visualization in Qiita.
* Creation of a REST API to query and access the data hosted by Qiita.
* Improved analysis pipeline for target gene datasets.
* Crowd-sourced metadata curation of existing studies: improve the metadata of
  existing studies by submitting a fix proposals to the authors of the study.


.. |Build Status| image:: https://travis-ci.org/biocore/qiita.png?branch=master
   :target: https://travis-ci.org/biocore/qiita
.. |Coverage Status| image:: https://codecov.io/gh/biocore/qiita/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/biocore/qiita
.. |Gitter| image:: https://badges.gitter.im/Join%20Chat.svg
   :target: https://gitter.im/biocore/qiita?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge
