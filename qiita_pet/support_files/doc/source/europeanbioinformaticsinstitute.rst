.. role:: red

EBI Submission via Qiita
========================

  1.  Upload sample information and preparation information with their required fields for amplicon sequencing
  2.  Link appropriate sequence files
  3.  Run split libraries, trimming, then deblur or closed reference commands

*  Note: when using closed reference make sure you're using Greengenes for 16S  :ref:`[7]<reference7>`, Silva for 18S  :ref:`[8]<reference8>`  , and UNITE for ITS  :ref:`[9]<reference9>`

Qiita allows users to deposit their study, sample, experiment and sequence data to the
`European Nucleotide Archive (ENA) <https://www.ebi.ac.uk/ena>`__, which is the permanent data
repository of the `European Bioinformatics Institute (EBI) <https://www.ebi.ac.uk/>`__. Submitting to
this repository will provide you with a unique identifier for your study, which is generally a
requirement for publications. Your study will be housed with all other Qiita submissions
and so we require adherence to the `MiXs standard <http://gensc.org/mixs/>`__.

EBI/ENA requires a given set of column fields to describe your samples and experiments described below. 

Creating a sample information template on our website using `Qiimp<https://qiita.ucsd.edu/iframe/?iframe=qiimp>`__ will ensure your data is EBI/ENA compliant. Alternatively, you can refer to the example template which can be found on the
`Knight Lab website <https://knightlab.ucsd.edu/wordpress/?page_id=478>`__ under "MetaData Template" and "Prep Template".

Without these, **Qiita Admins** will not be able to submit your data to EBI. If you want to submit your data or need
help send an email to `qiita.help@gmail.com <qiita.help@gmail.com>`__ and please include your study ID. Help will include advice on additional fields to add to ensure MiXs compliance.

Note that submissions are time consuming and need full collaboration from the user.
:red:`Do not wait until the last minute to request help.` In general, the best
time to request a submission is when you are writing your paper. Remember that the
data can be submitted to EBI and can be kept private and simply make public when
the paper is accepted. Note that EBI/ENA takes up to 15 days to change the status
from private to public, so consider this when submitting data and your manuscript.

.. note::
   For convenience Qiita allows you to upload a QIIME mapping file to process your data. However,
   the QIIME mapping file, in general, does not have all the EBI/ENA fields. Thus, you will need to
   update your information files (sample or preparation) via the update option. To simplify this process,
   you can download the system generated files and add/modify these fields for each file.


EBI-ENA NULL values vocabulary
------------------------------

We support only the following values: *not applicable*, *not collected*, *not provided*, *restricted access*.

For the latest definitions and explanation visit the `EBI/ENA Missing value reporting <http://www.ebi.ac.uk/ena/about/missing-values-reporting>`__.

.. warning::
   Column names in your information files cannot be named as a Postgres reserved word. For example, a column cannot be named `CONDITION`, but could instead be named `DISEASE_CONDITION`. For a full list of these reserved words, see this `link <https://www.postgresql.org/docs/9.3/static/sql-keywords-appendix.html>`__.

Required Sample Information Fields for EBI submission
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
These are the columns required for successfully submit any data to EBI via Qiita:
sample_name, collection_device, collection_method, collection_timestamp, description, dna_extracted, elevation, elevation_units, empo_1,
empo_2, empo_3, env_biome, env_feature, env_material, env_package, geo_loc_name, host_subject_id, latitude, latitude_units, longitude,
longitude_units, physical_specimen_location, physical_specimen_remaining, sample_type, scientific_name, taxon_id, taxon_id_units, title, tube_id.

If your samples are related to animals you will also need:
host_age, host_age_units, host_body_habitat, host_body_product, host_body_site, host_common_name, host_height, host_height_units, host_scientific_name, host_taxid, host_taxid_units, host_weight, host_weight_units, life_stage, sex, time_point, time_point_units.

If your samples are related to humans you will also need:
host_body_mass_index, host_body_mass_index_units, irb_institute, irb_protocol_id

__Please note that personally identifiable health information and protected health information (PHI) should NOT be supplied. For information regarding the rules for defining PHI you can reference the `CMI User Information Sheet: The De-Identification of Protected
Health Information<https://drive.google.com/a/eng.ucsd.edu/file/d/0B6NwNax2VIfab1lBWmVQSGdnM0U/>`__

We recommend creation of a metadata template for your study using `Qiimp<https://qiita.ucsd.edu/iframe/?iframe=qiimp>`__ as this tool enables you to automatically ensure compliance with EBI and MIMARKS standards and enable your data to be consistent with other studies used in Qiita to maximize your ability to perform meta-analyses.

Alternatively, you can refer to the example sample information spread sheet under "MetaData Template" at the `Knight Lab website <https://knightlab.ucsd.edu/wordpress/?page_id=478>`__ .

Without these columns you will not be able to submit to EBI.


Required Prep Information Fields for EBI submission
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To successfully submit your data to EBI, you will also need to include a minimal number of columns in your preparation information depending on your data type:

Amplicon Sequencing Data (16S, 18S, ITS, etc.)
sample_name, barcode, linkerprimer ( use primer for older 454), experiment_design_description, library, library_construction_protocol, linker, platform, run_center, run_date, run_prefix, pcr_primers, sequencing_meth, target_gene, target_subfragment, center_name, center_project_name, instrument_model, runid

Metagenomic Sequencing Data (WGS, WGMS,"shotgun", etc.)
sample_name, experiment_design_description, library_construction_protocol, platform, run_center, run_date, run_prefix, sequencing_meth, center_name,	center_project_name, instrument_model, run_id, forward_read, reverse_read, sample_plate, sample_well,	i7_index_id (Illumina only), index, i5_index_id (Illumina only), index2, sample_project, well_description

Metabolomics Data:
sample_name, experiment_design_description, run_center, run_date, run_prefix, extraction_solvent, center_name, center_project_name, sample_plate, sample_well, well_description

For descriptions of these fields, you can view the required columns listed on the preparation information spread sheet under "Prep Template" on the `Knight Lab website <https://knightlab.ucsd.edu/wordpress/?page_id=478>`__.

Without these columns you will not be able to submit to EBI.

For sequencing data, all valid values for instrument_model per platform, view the values in the table below:
+--------------+----------------------------------------------------------------------------------------------------------+
| Platform     | Valid instrument_model options                                                                           |
+==============+==========================================================================================================+
| ``LS454``    |  ``454 GS``, ``454 GS 20``, ``454 GS FLX``, ``454 GS FLX+``, ``454 GS FLX Titanium``, ``454 GS Junior``, |
|              |  ``454 GS Junior`` or ``unspecified``                                                                    |
+--------------+----------------------------------------------------------------------------------------------------------+
| ``Illumina`` |  ``HiSeq X Five``, ``HiSeq X Ten``, ``Illumina Genome Analyzer``, ``Illumina Genome Analyzer II``,       |
|              |  ``Illumina Genome Analyzer IIx``, ``Illumina HiScanSQ``, ``Illumina HiSeq 1000``,                       |
|              |  ``Illumina HiSeq 1500``,, ``Illumina HiSeq 2000``, ``Illumina HiSeq 2500``, ``Illumina HiSeq 3000``,    |
|              |  ``Illumina HiSeq 4000``, ``Illumina MiSeq``, ``Illumina MiniSeq``, ``Illumina NovaSeq 6000``,           |
|              |  ``NextSeq 500``, ``NextSeq 550``, or ``unspecified``                                                    |
+--------------+----------------------------------------------------------------------------------------------------------+
