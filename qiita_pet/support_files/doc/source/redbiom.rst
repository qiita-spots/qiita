Redbiom
=======
* Allows you to search through public studies to find comparable data to your own
* Can search by: metadata, feature, or taxon

Search Options
--------------
* **Metadata**:

  * The search will be on the full metadata.
  * The metadata search engine uses natural language processing to search for word stems within a samples metadata. A word stem disregards modifiers and plurals, so for instance, a search for "antibiotics" will actually perform a search for "antibiot". Similarly, a search for "crying" will actually search for "cry". The words specified can be combined with set-based operations, so for instance, a search for "antibiotics & crying" will obtain the set of samples in which each sample has "antibiot" in its metadata as well as "cry". N.B., the specific category in which a stem is found is not assured to be the same, "antibiot" could be in one category and "cry" in another. A set intersection can be performed with "&", a union with "|" and a difference with "-".
  * In addition to the stem-based search, value based searches can also be a applied. These use a Python-like grammar and allow for a rich set of comparisons to be performed based on a metadata category of interest. For example, "where qiita_study_id == 10317" will find all samples which have the qiita_study_id metadata category, and in which the value for that sample is "10317."
  * Examples:

    * Find all samples in which the word infant exists, as well as antibiotics, where the infants are under a year old:

      * *infant & antibiotics where age_years <= 1*

    * Find all samples only belonging to the EMP in which the ph is under 7 for a variety of sample types:

      * soil: *soil where ph < 7 and emp_release1 == 'True'*
      * ocean water: *water & ocean where ph > 7 and emp_release1 == 'True'*
      * non-ocean water: *water - ocean where ph > 7 and emp_release1 == 'True'*

    * Or instead of ph you could search for a different metadata category:

      * *water & ocean where salinity > 20*

    * Some other interesting examples:

      * *feces & canine*
      * *(beer | cider | wine | alcohol)*
      * *where sample_type == 'stool'*
      * *usa where sample_type == 'stool' and host_taxid == 9606*

* **Feature**:

  * The search will be on all the features, in specific: OTU ids for close reference and exact sequences for deblur.

    * Examples:

      * Find all samples in which the Greengenes feature 4479944 is found: "4479944"

* **Taxon**:

  * The search will be only on closed reference and based on the taxonomies available. Only exact matches are returned. Note that currently only the Greengenes taxonomy is searchable, and that it requires nomenclature of a rank prefix, two underscores, and then the name.

    * Examples:

      * Find all samples in which the genera Escherichia is found: "g__Escherichia"
      * Find all samples in which the order Clostridiales is found: "o__Clostridiales"

For more information go to the `Redbiom github page <https://github.com/biocore/redbiom>`__.
