.. _empo:

Earth Microbiome Project Ontology (EMPO)
========================================

Qiita supports using the EMPO classification of samples as it provides and easy
way to group samples and has resulted extremely helpful for meta-analyses and
searching and finding similar samples in the database.

The current version can be found here: :ref:`checklist-for-ebi-ena-submission` and below
you can find older version, for your reference.

EMPO 1 (first release)
----------------------

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
