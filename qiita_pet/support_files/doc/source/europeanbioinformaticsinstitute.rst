.. role:: red

EBI submission via Qiita
========================

Qiita allows users to deposit their study, sample, experiment and sequence data to the
`European Nucleotide Archive (ENA) <https://www.ebi.ac.uk/ena>`__, which is the permanent data
repository of the `European Bioinformatics Institute (EBI) <https://www.ebi.ac.uk/>`__. Submitting to
this repository will provide you with a unique identifier for your study, which is generally a
requirement for publications. Your study will be housed with all other Qiita submissions
and so we require adherence to the `MiXs standard <http://gensc.org/mixs/>`__.

EBI/ENA requires a given set of column fields to describe your samples and experiments which can be found on the
`Knight Lab website <https://knightlab.ucsd.edu/wordpress/?page_id=478>`__ under "MetaData Template" and "Prep Template".
Without these, **Qiita Admins** will not be able to submit your data to EBI. If you want to submit your data or need
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


EBI-ENA NULL values vocabulary
------------------------------

We support the following values: *not applicable*, *missing: not collected*, *missing: not provided*, *missing: restricted access*.

For the latest definitions and explanation visit the `EBI/ENA Missing value reporting <http://www.ebi.ac.uk/ena/about/missing-values-reporting>`__.

.. warning::
   Column names in your information files cannot be named as a Postgres reserved word. For example, a column cannot be named `CONDITION`, but could instead be named `DISEASE_CONDITION`. For a full list of these reserved words, see this `link <https://www.postgresql.org/docs/9.3/static/sql-keywords-appendix.html>`__.


Required Sample Information Fields for EBI submission
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

These are the columns required for successfully submit your data to EBI:
To successfully submit your data to EBI, view the required columns listed on the sample information spread sheet
`Knight Lab website <https://knightlab.ucsd.edu/wordpress/?page_id=478>`__ under "MetaData Template". Without these columns
you will not be able to submit to EBI.


Required Prep Information Fields for EBI submission
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To successfully submit your data to EBI, view the required columns listed on the preparation information spread sheet
`Knight Lab website <https://knightlab.ucsd.edu/wordpress/?page_id=478>`__ under "Prep Template". Without these columns
you will not be able to submit to EBI.

For all valid values for instrument_model per platform, view the values in the table below:

+--------------+----------------------------------------------------------------------------------------------------------+
| Platform     | Valid instrument_model options                                                                           |
+==============+==========================================================================================================+
| ``LS454``    |  ``454 GS``, ``454 GS 20``, ``454 GS FLX``, ``454 GS FLX+``, ``454 GS FLX Titanium``, ``454 GS Junior``, |
|              |  ``454 GS Junior`` or ``unspecified``                                                                    |
+--------------+----------------------------------------------------------------------------------------------------------+
| ``Illumina`` |  ``Illumina Genome Analyzer``, ``Illumina Genome Analyzer II``, ``Illumina Genome Analyzer IIx``,        |
|              |  ``Illumina HiSeq 4000``, ``Illumina HiSeq 3000``, ``Illumina HiSeq 2500``, ``Illumina HiSeq 2000``,     |
|              |  ``Illumina HiSeq 1500``, ``Illumina HiSeq 1000``, ``Illumina MiSeq``, ``Illumina MiniSeq``,             |
|              |  ``Illumina NovaSeq 6000````Illumina HiScanSQ``,``HiSeq X Ten``, ``NextSeq 500``, ``NextSeq 550``,       |
|              |  or ``unspecified``                                                                                      |
+--------------+----------------------------------------------------------------------------------------------------------+
