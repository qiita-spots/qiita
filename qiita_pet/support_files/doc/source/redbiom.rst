.. _redbiom:

.. index:: redbiom

redbiom
=======
* Allows you to search through public studies to find comparable data to your own
* Can search by: metadata, feature, or taxon

redbiom is a cache service which can be used to search databases for samples which contain particular taxonomic units or given features (e.g. environmental or clinical factors); either as a Qiita plugin, or as a separately installed command line package. redbiom can therefore be used to identify samples for a meta-analysis focused on some particular factor (or factors). The utility of searching by metadata or feature is that it allows the discovery and subsequent use of a potentially wide variety of samples. This may include data from studies with completely different research goals, which one would have otherwise been unlikely to realize could be used.

Note that a cache service is a high-speed data storage layer which stores a subset of data allowing a more rapid searching and retrieval experience. redbiom has a much smaller, sparse vector version of the Qiita database containing mainly metadata, which thus allows rapid searching. Samples found in a redbiom search can then be retrieved from the Qiita database through redbiom for subsequent analysis.

For more information, advanced queries and generating
`BIOM <http://biom-format.org/>`__ files go to the
`redbiom github page <https://github.com/biocore/redbiom/blob/master/README.md>`__.

Search Options
--------------
**1. Metadata**:

  * The search will be on the **full metadata**.
  * **Natural language processing:** The metadata search engine uses natural language processing to
    search for word stems within a sample metadata. A word stem disregards modifiers and plurals, so for instance,
    a search for *antibiotics* will actually perform a search for *antibiot*. Similarly, a search for *crying* will
    actually search for *cry*. The words specified can be combined with set-based operations, so for instance, a
    search for *antibiotics & crying* will obtain the set of samples in which each sample has *antibiot* in its metadata as
    well as *cry*.

    N.B., the specific category in which a stem is found is not assured to be the same, *antibiot* could be in one category
    and *cry* in another. A set intersection can be performed with "&", a union with "|" and a difference with "-".
  * **Value search:** In addition to the stem-based search, value based searches can also be applied. These use a Python-like
    grammar and allow for a rich set of comparisons to be performed based on a metadata category of interest. For example

    .. code-block:: bash

       where qiita_study_id == 10317

    will find all samples which have the *qiita_study_id* metadata category, and in which the value for that sample is *10317*.

  * **Examples:**

    * Find all samples in which both the word 'infant', as well as 'antibiotics' exist, and where the infants are under a year old:

    .. code-block:: bash

       infant & antibiotics where age_years <= 1

    * Find all samples only belonging to the EMP in which the pH is under 7, for a variety of sample types:

      * soil:

      .. code-block:: bash

         soil where ph < 7 and emp_release1 == 'True'

      * ocean water:

      .. code-block:: bash

         water & ocean where ph > 7 and emp_release1 == 'True'

      * non-ocean water:

      .. code-block:: bash

         water - ocean where ph > 7 and emp_release1 == 'True'

    * Or instead of pH you could search for a different metadata category:

    .. code-block:: bash

       water & ocean where salinity > 20

    * Some other interesting examples:

    .. code-block:: bash

       feces & canine

       (beer | cider | wine | alcohol)

       where sample_type == 'stool'

       usa where sample_type == 'stool' and host_taxid == 9606

**2. Feature**:

  * The search will be on all the features, in specific: **OTU ids for closed reference** or **exact sequences for deblur**.
  * **Examples:**

    * Find all samples in which the Greengenes feature 4479944 is found:

    .. code-block:: bash

       4479944

    * Find all samples in which the sequence exists:

    .. code-block:: bash

       TACGAAGGGTGCAAGCATTACTCGGAATTACTGGGCGTAAAGCGTGCGTAGGTGGTTCGTTAAGTCTGATGTGAAAGCCCTGGGCTCAACCTGGGAACTG

**3. Taxon**:

  * The search will be **only on closed reference data** and based on the taxonomies available. Only exact matches are returned. Note that currently **only the Greengenes taxonomy** is searchable, and that it requires nomenclature of a rank prefix, two underscores, and then the name.

  * **Examples:**

    * Find all samples in which the genera Escherichia is found:

    .. code-block:: bash

       g__Escherichia

    * Find all samples in which the phylum Tenericutes is found:

    .. code-block:: bash

       p__Tenericutes
