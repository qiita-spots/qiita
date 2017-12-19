EBI submission via Qiita
========================

Qiita allows users to deposit their study, sample, experiment and sequence data to the
`European Nucleotide Archive (ENA) <https://www.ebi.ac.uk/ena>`__, which is the permanent data
repository of the `European Bioinformatics Institute (EBI) <https://www.ebi.ac.uk/>`__. Submitting to
this repository will provide you with a unique identifier for your study, which is generally a
requirement for publication. Your study will be housed with all other Qiita submissions
and so we require adherence to the MiXs standard.

EBI/ENA requires a given set of column fields to describe your samples and experiments, for more
information visit :doc:`prepare-information-files` and pay most attention to EBI required fields,
without these **Qiita Admins** will not be able to submit. If you want to submit your data or need
help send an email to `qiita.help@gmail.com <qiita.help@gmail.com>`__. Help will include
advice on additional fields to add to ensure MiXs compliance.

Note that submissions are time consuming and need full collaboration from the user.
:red:`Do not wait until the last minute to request help.` In general, the best
time to request a submission is when you are writing your paper. Remember that the
data can be submitted to EBI and can be kept private and simply make public when
the paper is accepted. Note that EBI/ENA takes up to 15 days to change the status
from private to public, so consider this when submitting data and your manuscript.

.. note::
   For convenience Qiita allows you to upload a QIIME mapping file to process your data. However,
   the QIIME mapping file, in general, doesn't have all the EBI/ENA fields. Thus, you will need to
   update your information files (sample or preparation) via the update option. To simplify this process,
   you can download the system generated files and add/modify these fields for each file.
   
Required fields for EBI submission
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

These are the columns required for successfully submit your data to EBI:

+----------------------------------+-------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------+
| Field name                       | Format                  | Description                                                                                                                                         |
+==================================+=========================+=====================================================================================================================================================+
| ``collection_timestamp``         | ``yyyy-mm-dd hh:mm:ss`` | The time stamp (preferred) of when the sample was collected. Several format are accepted, all ISO 8601.                                             |
|                                  | or ``yyyy-mm-dd hh:mm`` |                                                                                                                                                     |
|                                  | or ``yyyy-mm-dd hh``    |                                                                                                                                                     |
|                                  | or ``yyyy-mm-dd ``      |                                                                                                                                                     |
|                                  | or ``yyyy-mm``          |                                                                                                                                                     |
|                                  | or ``yyyy``.            |                                                                                                                                                     |
|                                  | Years are only          |                                                                                                                                                     |
|                                  | supported as 4 ``yyyy`` |                                                                                                                                                     |
|                                  | digits                  |                                                                                                                                                     |
+----------------------------------+-------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------+
| ``physical_specimen_location``   | free text               | Where you would go to find physical sample or DNA, regardless of whether it is still available or not.                                              |
+----------------------------------+-------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------+
| ``taxon_id``                     | integer                 | NCBI taxon ID for the sample. Should indicate metagenome being investigated. Examples: 410658 for soil metagenome, 749906 for gut metagenome,       |
|                                  |                         | 256318 for metagenome (used for unspecified or blanks). To find others visit `NCBI Taxonomy Database <http://www.ncbi.nlm.nih.gov/taxonomy>`__.     |
+----------------------------------+-------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------+
| ``scientific_name``              | free text               | NCBI's scientific name for the provided taxon ID. This is the name of the metagenome, not the host scientific name. Examples: soil metagenome,      |
|                                  |                         | gut metagenome, marine sediment metagenome, marine metagenome.                                                                                      |
+----------------------------------+-------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------+
| ``description``                  | free text               | Description of the sample.                                                                                                                          |
+----------------------------------+-------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------+

Required fields for centralized Qiita
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

These are the columns required if you want to make your date public at
the centralized `Qiita server <http://qiita.microbio.me>`__:

+-----------------------------------+----------------------------------------------------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Field name                        | Format                                                               | Description                                                                                                                                                                                                                                                                                                                                       |
+===================================+======================================================================+===================================================================================================================================================================================================================================================================================================================================================+
| ``host_subject_id``               | free text                                                            | An identifier for the “host”. Should be specific to a host, and can be a one-to-many relationship with samples. All samples from the same source (host, sample) should have the same identifier to facilitate analysis. If this is not a host-associated study, this can be an identifier for a replicate, or can be the same as ``sample_name``. |
+-----------------------------------+----------------------------------------------------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| ``sample_type``                   | free text                                                            | Description of the type of sample.                                                                                                                                                                                                                                                                                                                |
+-----------------------------------+----------------------------------------------------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| ``physical_specimen_remaining``   | ``TRUE`` or ``FALSE``                                                | Is there still physical sample (e.g., soil, not DNA) available?                                                                                                                                                                                                                                                                                   |
+-----------------------------------+----------------------------------------------------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| ``dna_extracted``                 | ``TRUE`` or ``FALSE``                                                | Has DNA already been extracted for this sample?                                                                                                                                                                                                                                                                                                   |
+-----------------------------------+----------------------------------------------------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| ``latitude``                      | `decimal degrees <http://en.wikipedia.org/wiki/Decimal_degrees>`__   | Latitude where sample was collected.                                                                                                                                                                                                                                                                                                              |
+-----------------------------------+----------------------------------------------------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| ``longitude``                     | `decimal degrees <http://en.wikipedia.org/wiki/Decimal_degrees>`__   | Longitude where sample was collected.                                                                                                                                                                                                                                                                                                             |
+-----------------------------------+----------------------------------------------------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+


EBI-ENA NULL values vocabulary
------------------------------

We support the following values: *not applicable*, *missing: not collected*, *missing: not provided*, *missing: restricted access*.

For the latest definitions and explanation visit the `EBI/ENA Missing value reporting <http://www.ebi.ac.uk/ena/about/missing-values-reporting>`__.

.. warning::
   Column names in your information files cannot be named as a Postgres reserved word. For example, a column cannot be named `CONDITION`, but could instead be named `DISEASE_CONDITION`. For a full list of these reserved words, see this `link <https://www.postgresql.org/docs/9.3/static/sql-keywords-appendix.html>`__.
