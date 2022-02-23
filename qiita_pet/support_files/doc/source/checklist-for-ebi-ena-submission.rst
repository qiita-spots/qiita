.. role:: red
.. _checklist-for-ebi-ena-submission:

Making data Public in Qiita and/or send data to EBI-ENA
=======================================================

Qiita allows users to deposit their study, sample, experiment and sequence data to the
`European Nucleotide Archive (ENA) <https://www.ebi.ac.uk/ena>`__, which is the permanent data
repository of the `European Bioinformatics Institute (EBI) <https://www.ebi.ac.uk/>`__. Submitting to
this repository will provide you with a unique identifier for your study, which is generally a
requirement for publications. Your study will be housed with all other Qiita submissions
and so we require adherence to the `MiXs standard <http://gensc.org/mixs/>`__. Note that this also
applies for studies in sandbox state that will become private or public.

.. warning::
   direct BIOM uploads cannot become private or public

.. note::
    The EBI-ENA submission returns two accessions - the primary starts with PRJ
    and the secondary with ERP; they can be used irrespectively. We suggest that
    you add at least one of them to your manuscript, together with the Qiita Study id.
    Please do not forget to cite Qiita (https://doi.org/10.1038/s41592-018-0141-9).
    This information should be sufficient for your manuscript but if you would like
    to add direct links to your data, once they are public, you can use the EBI-ENA:
    `https://www.ebi.ac.uk/ena/browser/view/[accession]` or the Qiita Study
    id: `https://qiita.ucsd.edu/public/?study_id=[study-id]`

`Here <https://knightlab.ucsd.edu/wordpress/wp-content/uploads/2016/04/QiitaTemplate_20181218.xlsx>`__ you will find a document outlining these requirements, with examples, when possible.

Note that submissions are time consuming and need full collaboration from the user.
:red:`Do not wait until the last minute to request help.` In general, the best
time to request a submission is when you are writing your paper. Remember that the
data can be submitted to EBI and can be kept private and simply make public when
the paper is accepted. Note that EBI/ENA takes up to 15 days to change the status
from private to public, so consider this when submitting data and your manuscript.
If need help send an email to `qiita.help@gmail.com <mailto:qiita.help@gmail.com>`__
and please include your study ID.

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

Checklist
---------

Remember, metadata is the most important part for an analysis, without it we only have sequences; thus, for each preparation that needs to be uploaded to EBI-ENA or become public we will check:

  1. Data processing

    a. Only datasets where raw sequences are available and linked to the preparation can be submitted. Studies where the starting point is a BIOM table cannot be submitted, since EBI is a sequence archive
    b. The data is processed and the owner confirms the data is correct and followed our :doc:`processingdata/processing-recommendations`.

  2. Verify the sample information

    a. Check that the sample information file complies with `the current Qiita metadata format <https://qiita.ucsd.edu/static/doc/html/gettingstartedguide/index.html#sample-information-file>`__.
    b. Minimal information:

      1. *sample_name*
      2. *host_subject_id*
      3. *sample_type*
      4. *taxon_id* - needs to match *scientific_name* value
      5. *scientific_name* - needs to match *taxon_id* value - this is the name of the `metagenome <https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?mode=Tree&id=12908&lvl=3&srchmode=1&keep=1&unlock>`__ referenced in the column *taxon_id* and that the two values match.  Submission will not work if the user puts *host_scientific_name* or *host_taxid* instead.  Do not accept EBI null values. For null values use *scientific_name* “metagenome” and *taxon_id* “256318”
      6. *env_biome*, *env_feature*, *env_material*, *env_package*, for options `visit ENVO <http://ols.wordvis.com/>`__
      7. *elevation*, *latitude*, *longitude*
      8. *physical_specimen_location*
      9. *collection_timestamp*
      10. *empo_1*, *empo_2*, *empo_3*

         .. table::
            :widths: auto

            =============== ================= ======================= ================================================================================
            empo_1          empo_2            empo_3	                Examples
            Free-living	    Non-saline        Water (non-saline)      fresh water from lake, pond, or river (<5 psu)
            Free-living	    Non-saline        Sediment (non-saline)	  sediment from lake, pond, or river (<5 psu)
            Free-living	    Non-saline        Soil (non-saline)       soil from forest, grassland, tundra, desert, etc.
            Free-living	    Non-saline        Surface (non-saline)    biofilm from wet (<5 psu) or dry surface, wood, dust, or microbial mat
            Free-living	    Non-saline        Subsurface (non-saline) deep or subsurface environment
            Free-living	    Non-saline        Aerosol (non-saline)    aerosolized dust or liquid
            Free-living	    Saline            Water (saline)          salt water from ocean, sea, estuary, mangrove, or coral reef (>5 psu)
            Free-living	    Saline            Sediment (saline)       sediment from ocean, sea, estuary, mangrove, or beach (>5 psu)
            Free-living	    Saline            Hypersaline (saline)    water from hypersaline sample or brine (>50 psu)
            Free-living	    Saline            Surface (saline)        biofilm from wet or underwater surface or microbial mat (>5 psu)
            Free-living	    Saline            Aerosol (saline)        seaspray or other aerosolized saline material (>5 psu)
            Host-associated Animal-associated Animal distal gut       feces, stool
            Host-associated Animal-associated Animal proximal gut     digesta
            Host-associated Animal-associated Animal secretion        gut intestine, gizzard, crop, lumen, or mucosa
            Host-associated Animal-associated Animal surface          skin, sebum, mucus, slime
            Host-associated Animal-associated Animal corpus           tissue of sponge, coral, gill, siphon, carcass, etc. or whole small animal
            Host-associated Fungus-associated Fungus corpus           tissue of mushroom or other fungi
            Host-associated Fungus-associated Fungus surface          biofilm of mushroom
            Host-associated Plant-associated  Plant secretion         pollen or sap
            Host-associated Plant-associated  Plant surface          	leaf or kelp surface biofilm
            Host-associated Plant-associated  Plant rhizosphere       plant root system, may include some soil
            Host-associated Plant-associated  Plant corpus            tissue of leaf, stem, fruit, or algae
            Control         Negative          Sterile water blank     sterile water blank used as negative control for extraction, PCR, and sequencing
            Control         Positive          Mock community          known mixed community used as positive control
            Control         Positive          Single strain           known single strain control culture
            Unknown         Contradictory     Unknown (contradictory) unknown sample type because other metadata is contradictory
            Unknown         Missing           Unknown (missing)       unknown sample type because metadata is unavailable
            =============== ================= ======================= ================================================================================

    c. Extra minimal information for host associated studies:

      1. *host_body_habitat*, *host_body_site*, *host_body_product*
      2. *host_scientific_name*
      3. *host_common_name*
      4. *host_taxid*, `full list <https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi>`__
      5. *host_age*, *host_age_units*
      6. *host_height*, *host_height_units*
      7. *host_weight*, *host_weight_units*
      8. *host_body_mass_index* (human only)

    d. Double-check these fields:

      1. Check the date format, should be YYYY-MM-DD (hh:mm)
      2. Check null values
      3. Check that the values in each field make sense, for example that sex is not a numerical gradient, or that ph does not contain “male” or “female” values

  3. Verify the preparation information

    a. Check that the preparation information file complies with `the current Qiita metadata format <https://qiita.ucsd.edu/static/doc/html/gettingstartedguide/index.html#id1>`__
    b. Check that the correct Investigation type is selected on the prep info page
    c. Check for fill down errors in library_construction_protocol and target_subfragment; these are common.
    d. Minimal columns:

      1. *sample_name*
      2. *barcode*
      3. *primer* (include linker in this field)
      4. *platform*
      5. *experiment_design_description*
      6. *center_name*
      7. *center_project_name*
      8. *library_construction_protocol*
      9. *instrument_model*
      10. *sequencing_method*

      .. note::
        The current valid values for instrument_model per platform are - please contact us if you would like to add yours to this list:

        +---------------------+----------------------------------------------------------------------------------------------------------+
        | Platform            | Valid instrument_model options                                                                           |
        +=====================+==========================================================================================================+
        | ``LS454``           |  ``454 GS``, ``454 GS 20``, ``454 GS FLX``, ``454 GS FLX+``, ``454 GS FLX Titanium``, ``454 GS Junior``, |
        |                     |  ``454 GS Junior`` or ``unspecified``                                                                    |
        +---------------------+----------------------------------------------------------------------------------------------------------+
        | ``Illumina``        |  ``HiSeq X Five``, ``HiSeq X Ten``, ``Illumina Genome Analyzer``, ``Illumina Genome Analyzer II``,       |
        |                     |  ``Illumina Genome Analyzer IIx``, ``Illumina HiScanSQ``, ``Illumina HiSeq 1000``,                       |
        |                     |  ``Illumina HiSeq 1500``,, ``Illumina HiSeq 2000``, ``Illumina HiSeq 2500``, ``Illumina HiSeq 3000``,    |
        |                     |  ``Illumina HiSeq 4000``, ``Illumina MiSeq``, ``Illumina MiniSeq``, ``Illumina NovaSeq 6000``,           |
        |                     |  ``NextSeq 500``, ``NextSeq 550``, or ``unspecified``                                                    |
        +---------------------+----------------------------------------------------------------------------------------------------------+
        | ``Ion_Torrent``     |  ``Ion Torrent PGM``, ``Ion Torrent Proton``, ``Ion Torrent S5``, ``Ion Torrent S5 XL``                  |
        +---------------------+----------------------------------------------------------------------------------------------------------+
        | ``PacBio_SMRT``     |  ``PacBio RS``, ``PacBio RS II``, ``Sequel``, ``Sequel II``                                              |
        +---------------------+----------------------------------------------------------------------------------------------------------+
        | ``Oxford_Nanopore`` |  ``GridION``                                                                                             |
        +---------------------+----------------------------------------------------------------------------------------------------------+


    c. Additional minimal columns, if possible:

      1. *pcr_primers*
      2. *run_prefix*
      3. *run_center*
      4. *run_date*
      5. *target_gene*
      6. *target_subfragment*

  4. `EBI null values <http://www.ebi.ac.uk/ena/about/missing-values-reporting>`__ for use when data is not present:

    a. not applicable
    b. missing:

      1. not collected
      2. not provided
      3. restricted access
