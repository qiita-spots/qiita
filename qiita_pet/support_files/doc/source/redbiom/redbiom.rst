.. _redbiom:

.. index:: redbiom

redbiom
=======
* Allows you to search through public studies to find comparable data to your own
* Can search by: metadata, feature, or taxon

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
       
       
       
       
       
Retrieving Public Data for Own Analysis Tutorial
------------------------------------------------

Introduction
~~~~~~~~~~~~

This tutorial aims to introduce Qiita [1A]_ and redbiom [2A]_ to new users as utilities for downloading public datasets for subsequent analyses of their own. This will be illustrated with two examples.

Set up
~~~~~~

This tutorial will start online using `Qiita <https://qiita.ucsd.edu/>`__ , for which one requires an account. If you do not, as yet, have a Qiita account you will need to create one (this is very simple, requiring only an email address); navigate to the `Qiita website <https://qiita.ucsd.edu/>`__ and use the sign up action box in the top right corner to do so.
Redbiom can be used as a plugin in Qiita but the redbiom programme has more functionality. We will therefore be installing redbiom in the command line to use with the second tutorial example which demonstrates this functionality. Windows requires some additional set-up, please refer to `Setting up Windows to use QIIME 2 <https://docs.qiime2.org/>`__ in the QIIME2 docs. The following set-up is relevant for linux, Mac and the Windows subsystem for Linux (setup explained in the `QIIME2 docs <https://docs.qiime2.org>`__ ):

If you have installed anaconda/miniconda then (in the command line) type:

.. code-block:: bash

    conda install -c conda-forge redbiom

If  you do not have miniconda or anaconda installed you can install miniconda as follows:

.. code-block:: bash

    wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
    bash Miniconda3-latest-Linux-x86_64.sh

Restart the terminal to have changes take effect, then create an environment to work in

.. code-block:: bash

    conda create --name <name of new environment>

Packages for this project can now be installed in this environment, keeping them separate from any other projects you may have, and ensuring that different dependencies do not clash. 

Alternatively, if you prefer not to install miniconda use:

.. code-block:: bash
    
    pip install numpy
    pip install redbiom


Introduction to the example data
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This tutorial will use two different datasets to highlight both the different questions that can be asked with existing, open source data, and the different methods we can use to do so.

The analysis of clinical microbiome data, selected for its similarity to the type of samples one plans to collect, allows one to produce example data before starting a study. This data can then be used for informing and justifying clinical trial format or experimental set-up [3A]_ . As this requires only a relatively small data set, and the question is of a less exploratory nature, it will be possible to carry out almost the entire process for this first example within Qiita.

The second example poses a meta-analysis type question about the microbiome which has not yet been fully addressed in the literature: does a person’s frequency of exercise affect their microbiome? To answer this type of exploratory meta-analysis question does not necessarily require a new study, it may be possible to re-purpose publicly available data for the analysis. This exploratory exercise-microbiome effect analysis will require a search through the data-base for any samples with information about a specific meta-data feature - frequency of exercise - this existing data can then be used to answer the novel question. This is a larger study and will require the use of the Redbiom programme, and coding tools beyond Qiita.

The following section will explain how to retrieve the data for these examples, beginning with the simpler clinical data example data retrieval on Qiita.

Retrieving Data
~~~~~~~~~~~~~~~

Contexts
^^^^^^^^

Processing and bioinformatic techniques can cause inherent biases in datasets, and so in Qiita and redbiom processed samples are partitioned into contexts representing these different methods. The protocol used to obtain samples and extract data may cause biases but, within any one context, data is expected to have the same biases and so be comparable. When retrieving data found in a redbiom search a context must be specified so ensuring the retrieved data is comparable.

Ultimately a context represents a processing pipeline, so if you are unfamiliar with the methods and processes used in such pipelines it may be worth reading this section: 

.. toctree::
    :maxdepth: 1

    understanding-contexts.rst

If you already have a decent understanding of sequencing and processing microbial genomic data then please proceed to the next section.

Commands to retrieve data
^^^^^^^^^^^^^^^^^^^^^^^^^

As previously discussed this tutorial will explore two methods by which one can retrieve data from publicly available studies. The simpler method, that is, completing everything within Qiita, will be outlined first, and this will be illustrated with our first example data set.

**Retrieving data using the redbiom plug-in within Qiita**

It is possible to search for data and studies directly on Qiita using the redbiom plug-in. This will be demonstrated by finding the data used in Gonzalez A et al.2018, which cites that the data used was retrieved from a study in Qiita with ID 1629 [3A]_ . On the Qiita website select the *Study -> View Study option*, specify metadata in the tab down menu next to the search box and search for 1629 to find the data for this first example. In most scenarios however, the study would not be known beforehand, and in this case the Redbiom plugin can be used to search by metadata attributes e.g. a search for IBD brings up 7 studies, including Study 1629. Note that next to the search box you can specify metadata, feature or taxon. Selecting the green plus for the study of interest reveals the study data, in the form of Qiita artifacts. All artifacts of one type can then be selected by using *add all*, or specific artifacts can be selected using *per artifact -> add*. These selected artifacts can then be used to create an analysis as outlined in the next section.

When browsing public studies to find appropriate data, more information on any study can be accessed by selecting it; this will open a new page which includes the study abstract and details as well as options to download the study data. All QIIME 2 maps and BIOMs, as well as EBI accession numbers and sample information can be downloaded directly from this main page. Selecting *data types*, and then the type of interest shows a diagram of the processing pipeline, further information, and list of samples within the dataset of that type. The sample information tab includes a list of all the metadata features (e.g. BMI) associated with the samples, and the option to download this metadata. Perusing these features may give a better indication of whether a study can be repurposed for one’s own analysis.

A search using the redbiom plugin within Qiita therefore allows one to either download data for study on another platform or to select artifacts for processing and analysis within Qiita. Once the artifacts have been added select *analysis* from the top bar and, from the drop down menu, select *create from selected samples*. This opens a window where one can view all selected artifacts and exclude blocks of samples or individual samples that are not required/relevant (first select a particular artifact to view these). Note if one chooses multiple studies that only like data can be merged.
Selecting *create analysis* and entering an analysis name (and optional description) will take one to Qiita’s graphical interface processing platform. Note that you should should *Merge samples with the same name - useful when merging multiple preparation artifacts* if you want to use the metadata from the studies the samples originated from.

Other tutorials (e.g. the [Statistical Analysis to Justify Clinical Trial Sample Size Tutorial](ADD LINK TO THIS TUTORIAL)) explain how to process the raw data that you have just selected within Qiita for analysis. After processing raw data with Qiita the artifacts can be downloaded by selecting an artifact and clicking ‘generate a download link’. This is also possible for another’s analysis as long as it is public. More generally, using wget or curl in the command line, one can use the general *https://qiita.ucsd.edu/public_artifact_download/?artifact_id=artifact-id notation*, provided the analysis is public. This is also useful in the situation where one wants to use the processed artifacts from a public study (simply click on an artifact in any public study’s processing network to view its artifact ID). To fetch specific types of data one can also use specific calls. The following notation can be used to fetch:

* All raw data: ``https://qiita.ucsd.edu/public_download/?data=raw&study_id=<study-id>``
* All BIOMs + mapping files: ``https://qiita.ucsd.edu/public_download/?data=biom&study_id=<study-id>``
* Only 16S raw data: ``https://qiita.ucsd.edu/public_download/?data=raw&study_id=<study-id>&data_type=16S``
* Only Metagenomic BIOMs + mapping files: ``https://qiita.ucsd.edu/public_download/?data=biom&study_id=<study-id>&data_type=Metagenomic``
* Only the sample information file: ``https://qiita.ucsd.edu/public_download/?data=sample_information&study_id=<study-id>``
* Only the preparation information file: ``https://qiita.ucsd.edu/public_download/?data=data=prep_information&prep_id=<prep-id>``

Where ``<study-id/prep-id>`` should be replaced with the appropriate study-id/prep-id.

**Retrieving Data with the Redbiom programme**

While the redbiom plugin for Qiita is useful for simple searches, and when finding data for processing and analysis within Qiita, the redbiom programme has increased functionality, and is particularly useful when data will be processed outside of Qiita. While artifacts, or raw study data, found within Qiita can then be downloaded after accessing the study and finding their ID, the redbiom programme allows searching and direct download all within the command line. The exercise frequency example will demonstrate how to use the redbiom programme.

**1. Background information :** [4A]_

Redbiom commands follow a specific syntax: ``redbiom [options] command [arguments]``; for example to search for a metadata feature: ``redbiom search metadata <the feature>``. The general structure of the search arguments is ``<set operations> where <value restrictions>``. Typing ``redbiom`` in the terminal will return its syntax and commands if ever in doubt. Similarly typing ``redbiom <command>`` will return the syntax and options of that redbiom command.

redbiom search has four commands, ``features``, ``metadata``, ``samples`` and ``taxon``. ``samples`` and ``features`` are complementary, ``features`` retrieves samples containing that feature while ``samples`` fetches the features present in the specified sample/s. In redbiom features are either closed reference OTU ids or exact sequences from deblur. In the future features will be expanded to include other unique attributes produced by processing pipelines. Both of these commands require a specified file and so are not as relevant to initial exploratory searches. ``taxon`` will return features associated with a taxon. ``metadata`` is particularly useful for our purposes. It accepts both ‘natural language’ (but uses stemming) and python-like grammar (separately or in combination). Some useful symbols include: ``&`` for intersection, ``|`` for union, ``-`` for difference and ``==`` for equal to. ``<``, ``>``, ``=>``, ``=<``, etc. can also be used. Using the option ``--categories`` one can search for metadata categories rather than values using the same syntax. For example, one could type ``redbiom search metadata --categories <keyword>`` to see the categories which include that keyword, one can then learn more about a specific category with ``summarize metadata-category --category <category-name> --counter``.

Querying and fetching sample data using Redbiom requires a specified context (``-context <your context>``). As contexts are relatively long it is useful to specify them beforehand: ``export CTX=<your context>`` and then use ``--context $CTX``. Contexts can be viewed by typing ``redbiom summarize contexts``, to view contexts with a particular keyword use ``redbiom summarize contexts | grep <your keyword>``. Which context is used will depend on the data one is looking for, if in doubt, one could choose the context with the most samples. In our case we will initially specify CTX as ``Deblur-NA-Illumina-16S-v4-90nt-99d1d8``, as this is appropriate for study 1629. See the section on understanding contexts for a reminder of their function and utility.

Making a directory to work in at this point (e.g. ``mkdir querying_redbiom; cd querying_redbiom``), will keep all the data retrieved and generated together and tidy.

**2. Retrieving data**

For the first example, as we know the specific study we are interested in using, we could use the syntax ``redbiom search metadata "where qiita_study_id == <study ID>"`` . To retrieve the data from this study we could pipe the previous command as follows:

.. code-block:: bash

    redbiom search metadata "where qiita_study_id == 1629" | redbiom fetch samples --context $CTX --output IBD.data.biom

Note here the use of our context. Alternatively, it is possible to write the contents of ``redbiom search metadata "where qiita_study_id == <study ID>"`` to a sample.lst file, in which case there will be a record of the samples we are using.

.. code-block:: bash

    redbiom search metadata "where qiita_study_id == 1629" > IBD.samples.lst
    redbiom fetch samples --from IBD.samples.lst --context $CTX --output IBD.data.biom

To illustrate the full functionality of redbiom we will now proceed to the exercise frequency example. The first step will be to search for studies that log exercise frequency, ``redbiom search metadata "exercise"`` yields 24 results. 
Or, using `NCBI <https://www.ncbi.nlm.nih.gov/Taxonomy/TaxIdentifier/tax_identifier.cgi>`__ to find the human taxa ID we could use ``redbiom search metadata "exercise where host_taxid==9606"`` which also gives 24 results. These results are studies, rather than individual samples (which is what was returned when we searched for a specific study).

When searching with a key word one cannot be sure how it is being used within the metadata, therefore, it is worth examining the categories which are returned by an exercise search: ``redbiom search metadata --categories exercise``. This searches for metadata categories containing exercise, of which there are eight at the time of writing.
``redbiom summarize metadata-category --category <your category> --dump`` gives all samples (not studies) in the category, pipe (``|``) this to ``wc -l`` to get the number of samples. For example, there are 161 samples in the category ``total_hours_exercise``. The ``--dump`` option returns all samples while the other option when searching for metadata categories is ``--counter``. THis gives the responses/variables within a category (e.g. for exercise frequency, one such value is *rarely*, another *frequently*) and also counts the number of samples matching to each of these responses.

We are interested in exercise frequency, and two categories contain this: ``exercise_frequency_unit`` with 1510 samples and ``exercise_frequency`` with 28017 samples (at the time of writing). One can use ``redbiom summarize metadata-category --category exercise_frequency --dump > exercise.list.txt`` to get a list of all the samples and confirm this worked with ``cat exercise.list.txt | wc -l`` which gives 28017 samples. The output is a file with not only the sample IDs but also the variable associated with each response; i.e. there are two columns. To use the file to fetch samples the second column must be removed: ``awk ‘{print $1}’ exercise.list.txt > exercise.samples.lst``. It is worth noting that these samples start with their study ID, e.g. 10317 (the American Gut Project (AGP) study ID). ``cat exercise.list.txt | grep 10317 | wc -l`` shows that 26027 of the samples are in fact from the AGP. Using the same code with the ``-v`` option for ``grep`` gives the samples from the other studies that logged exercise frequency.

As AGP has the most samples, we could consider using data only from this study. All the samples from a single study will have been collected and processed with the same protocol, and the measures of exercise frequency standardised, thus comparison will be less affected by biases than if multiple studies were used. First retrieve a list of the samples present in the AGP study: ``redbiom search metadata "where qiita_study_id == 10317" | grep -vi “blank” > AGP-samples``. ``grep`` is a selection tool, the option ``-v`` means to exclude any lines containing the specified keyword and the option ``-i`` causes the function to ignore case, in this way we only retrieve correctly ID’d (non blank) samples. This list (AGP-samples) can be used  to retrieve sample data. ``redbiom select`` would allow us to further refine the search if required. ``cat AGP-samples | redbiom summarize samples --category sample_type`` gives information on where the samples originate from e.g. one of the sample type categories is stool.
To fetch the sample metadata and data use ``redbiom fetch``:

.. code-block:: bash

    redbiom fetch sample-metadata --from AGP-samples --context $CTX --output AGP-metadata.tsv --all-columns
    redbiom fetch samples --from AGP-samples --context $CTX --output AGP.data.biom

Note that here the previous context for sample 1629 returns no results. Instead we need a context appropriate to the American Gut Project. AGP used the V4 region of the 16S rDNA gene sequenced by illumina, trimming to 150nt and deblur for binning. Setting ``export CTX=Deblur-Illumina-16S-V4-150nt-780653`` allows the data for the AGP samples in that context to be fetched (repeat the  commands above once the new context has been set).

For a small study ``redbiom summarize AGP-metadata.tsv``, and ``less AGP-metadata.tsv`` could be used to explore the data retrieved, however, for this large data set they give more details than are currently necessary. ``biom summarize-table -i AGP.data.biom | head`` gives some more condensed information about the sample (rather than meta) data, including a summary of counts.

Note that the AGP data-set is large. If these steps are slow, or if later steps are slow, then you can consider using a subset of the data. Replace:

.. code-block:: bash

    redbiom search metadata "where qiita_study_id == 10317" | grep -vi “blank” > AGP-samples

with

.. code-block:: bash

    redbiom search metadata "where qiita_study_id == 10317" | grep -vi “blank” | shuf -n <number of samples you want to use> > AGP-samples

Where shuf shuffles the lines piped to it and randomly selects the number of lines specified. All other commands remain the same but there will be less samples being analysed.

Conclusion
~~~~~~~~~~

This tutorial has demonstrated how to retrieve publicly available data with redbiom either through the Qiita plugin or the command line programme. If you are interested in learning how to process the raw data retrieved through the redbiom programme into a form appropriate for analysis please proceed to the next section of the tutorial. Alternatively, if you would like to learn how to use the data retrieved through the Qiita redbiom plugin to perform statistical analysis to justify clinical trial size please see the appropriate tutorial at :doc:`../analyzingsamples/index` for guidance on how to do so.

Bibliography
~~~~~~~~~~~~

.. [1A] Gonzalez A et al. 2018 Qiita: rapid, web-enabled microbiome meta-analysis. Nat. Methods 15, 796798. (doi:10.1038/s41592-018-0141-9)

.. [2A] McDonald D, Kaehler B, Gonzalez A, DeReus J, Ackermann G, Marotz C, Huttley G, Knight R. 2019 redbiom: a Rapid Sample Discovery and Feature Characterization System. mSystems 4. (doi:10.1128/mSystems.00215-19)

.. [3A] Casals-Pascual C, González A, Vázquez-Baeza Y, Song SJ, Jiang L, Knight R. 2020 Microbial Diversity in Clinical Microbiome Studies: Sample Size and Statistical Power Considerations. Gastroenterology 158, 15241528. (doi:10.1053/j.gastro.2019.11.305)

.. [4A] https://github.com/biocore/redbiom


 
Processing Public Data Retrieved With redbiom Tutorial
------------------------------------------------------


Introduction
~~~~~~~~~~~~~

This tutorial proceeds from the *Retrieving Data From Public Studies Tutorial*, and demonstrates how to process the raw AGP data retrieved through the redbiom API so that it can be used for analysis. The general work flow is transferable to any raw data retrieved through the redbiom API.

We will be using the AGP-samples, AGP-metadata.tsv and AGP.data.biom files retrieved using redbiom in the *Retrieving Data from Public Studies Tutorial*. As a reminder, AGP-samples contains a list of the samples retrieved by a search with specification "where qiita_study_id == 10317", this was then used to retrieve the biom table for those samples, and their associated metadata. A quick check to ensure that these are correct:

.. code-block:: bash

    biom summarize-table -i AGP.data.biom | head

Should give an output something like as follows:

.. code-block:: bash

    Num samples: 25,180
    Num observations: 1,028,814
    Total count: 524,626,716
    Table density (fraction of non-zero values): 0.000
    
    Counts/sample summary:
    Min: 2.000
    Max: 499,002.000
    Median: 14,772.500
    Mean: 20,835.056


Note this will be different if you are using a smaller subset of the data (which will speed up the tutorial). In the tutorial this retrieved data will be processed into an appropriate format for analysis using QIIME 2. QIIME 2 can be used in the command line or as an API for python. The command line is simpler to use, while the API allows more customization for complex processing. Note that while QIIME 2 artifacts cannot easily be viewed from either interface, one can use ``qiime tools peek <artifact name>`` to obtain some information on them in the command line or use the QIIME 2 `artifact viewer <https://view.qiime2.org/>`__ to view visualization type QIIME 2 artifacts (.qzv files).

Set up
~~~~~~

QIIME 2 is the latest version (at the time of writing) of a package necessary for handling the raw data retrieved through redbiom. It is a command line programme, therefore, if you have Windows OS you will need to use WSL2 for this tutorial. For instructions to set up WSL2 please see this [tutorial](LINK TO THE Windows set up tutorial). Instructions for QIIME 2 installation on Linux, Mac and Windows and the latest release of the software can be found `here <https://docs.qiime2.org/>`__ . If you have anaconda/miniconda then use the following commands:

Installation in a new environment:

* Visit the `QIIME 2 documentation <https://docs.qiime2.org/>`__ and navigate to *Natively installing QIIME 2* to find the link for the latest version of QIIME 2. 
* Then install as follows:

.. code-block:: bash

    wget <link from QIIME2 docs>
    conda env create -n qiime2 --file <RELEASENAME>.yml
    conda activate qiime2

*or*

Installation in an existing environment:

* Visit the `QIIME 2 documentation <https://docs.qiime2.org/>`__ and navigate to *Natively installing QIIME 2* to find the link for the latest version of QIIME 2. 
* Then install as follows:

.. code-block:: bash
    
    wget <link from QIIME2 docs>
    conda env update --file <RELEASE-NAME>.yml

If you do not have miniconda/anaconda then you can install miniconda as follows:

.. code-block:: bash

    wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
    bash Miniconda3-latest-Linux-x86_64.sh

Restart the terminal to have changes take effect, then create an environment to work in

.. code-block:: bash

    conda create --name <name for environment>

Packages for this project can now be installed in this environment, keeping them separate from any other projects you may have, and ensuring that different dependencies do not clash.

Command line workflow
~~~~~~~~~~~~~~~~~~~~~

For the command line version of the processing workflow, make sure you have activated the appropriate conda environment (i.e. the one in which you installed QIIME 2). The first step is to load the files retrieved with redbiom into QIIME 2 format files. Note that we don't need to load the metadata into a QIIME 2 format, as it can be used as is in the .tsv format.

.. code-block:: bash

    #Importing biom data, and converting into a QIIME 2 artifact and QIIME 2 visualization:

    qiime tools import --input-path ../AGP.data.biom --type 'FeatureTable[Frequency]' --input-format BIOMV210Format --output-path feature-table-AGP.qza

    qiime feature-table summarize --i-table feature-table-AGP.qza --o-visualization feature-table-AGP.qzv --m-sample-metadata-file ../AGP-metadata.tsv

Once the data has been imported into a QIIME 2 format, it needs to undergo quality control. Quality control will depend on the study but in this case we will first filter and discard samples which have a total feature count under a threshold of 1000, so ensuring that samples with a low number of reads (little data) are removed. Then further filtering to remove rare features, i.e. ASVs that only appear a few times in the whole dataset, will remove possible outliers. Furthermore, it is also important to only include samples from the same body site (we will use feces as this is where most of the samples originate) and exclude samples that do not have exercise frequency logged (while this is a category, some participants may not have answered this particular question when filling in the questionnaire). Finally, it may also be worth filtering out unhealthy individuals, who may bias the results (if health conditions limit exercise frequency then we may get a spurious result due to the correlation between ill health and low exercise frequency).

.. code-block:: bash

    #Filter frequency table using metadata and frequency criteria

    #filter out samples with a low number of reads
    qiime feature-table filter-samples --i-table feature-table-AGP.qza --p-min-frequency 1000 --o-filtered-table sample-frequency-filtered-table-AGP.qza

    #filter out features (ASVs) with a low frequency of occurrence
    qiime feature-table filter-features --i-table sample-frequency-filtered-table-AGP.qza --p-min-frequency 3 --o-filtered-table feature-filtered-table-AGP.qza

    #filter out samples which fall in unwanted metadata categories, or lack the metadata we require
    qiime feature-table filter-samples --i-table feature-filtered-table-AGP.qza --m-metadata-file ../AGP-metadata.tsv --p-where "([body_site]='UBERON:feces') AND ([subset_healthy] IN ('true', 'True', 'TRUE')) AND ([exercise_frequency] IN ('Never', 'Rarely (a few times/month)', 'Occasionally (1-2 times/week)', 'Regularly (3-5 times/week)', 'Daily'))" --o-filtered-table filtered-table-AGP.qza

    #visualise the filtered table
    qiime feature-table summarize --i-table filtered-table-AGP.qza --o-visualization filtered-table.qzv --m-sample-metadata-file ../AGP-metadata.tsv

We now have a filtered dataset, but will need to classify our features if we want to use analyses that take into account phylogenetic distance, and for more general taxonomic analysis. Therefore we need to extract sequences from the dataset and ‘insert’ them into a reference phylogenetic tree (this placement identifies their taxonomic position). The first step is to extract representative sequences from the data, and these can then be aligned with and inserted in a reference database. 
Obtain this reference data, as follows:
In the command terminal in your working directory (e.g. ``~/microbiome/exercise/``) create a directory for references (``mkdir reference``) and then use wget to download the data:

.. code-block:: bash

    mkdir reference
    cd reference
    # get the reference we need now
    wget https://data.qiime2.org/2020.2/common/sepp-refs-gg-13-8.qza
    # other reference files we will need later and may as well get now too
    wget https://github.com/BenKaehler/readytowear/raw/master/data/gg_13_8/515f-806r/human-stool.qza
    wget https://github.com/BenKaehler/readytowear/raw/master/data/gg_13_8/515f-806r/ref-seqs-v4.qza
    wget https://github.com/BenKaehler/readytowear/raw/master/data/gg_13_8/515f-806r/ref-tax.qza
    # return to the directory we have been working in
    cd .. 

Once these have downloaded one can proceed with the fragment insertion workflow.

.. code-block:: bash

    #generate representative sequences
    biom summarize-table --observations -i ../AGP.data.biom | tail -n +16 | awk -F ':' '{print ">"$1"\n"$1}' > rep_seqs.fna

Note that here we have made a fasta file, this is a very common file type for sequence storage where every sequence is preceded by a header line beginning with ``>``. Generally this header line contains information about the sequence such as it’s origin (species, gene etc) but as these are as yet unknown we use the sequence itself as an id for the sequence.

.. code-block:: bash

    #import these sequences into an artifact form
    qiime tools import --input-path rep_seqs.fna --output-path rep_seqs.qza --type 'FeatureData[Sequence]'

    #use the representative sequences artifact to create a fragment insertion placement tree
    qiime fragment-insertion sepp --i-representative-sequences ./rep_seqs.qza --i-reference-database ./sepp-refs-gg-13-8.qza --o-tree ./insertion-tree.qza --o-placements ./insertion-placements.qza

Aligning the fragments and creating an insertion tree is computationally costly, and will require at least 12GB ram and possibly several hours. If you are struggling to complete this step consider decreasing the sample size you are using (go back to the data retrieval section, and use the ``shuf -n`` option, then repeat the steps from there). 

One can also train a taxonomic classifier to classify the sequences. The fragment insertion generated a phylogeny, with the sequences inserted appropriately. The taxonomic classifier classifies the ASVs, assigning them to a particular clade (e.g. with good data to specific species) [1B]_ . While it is possible to use pre-trained classifiers these tend to give poorer results than those trained on data similar to that of the sample, therefore we will train  a classifier using human-stool samples.

.. code-block:: bash

    #create and train a taxonomic classifier
    qiime feature-classifier fit-classifier-naive-bayes --i-reference-reads ../reference/ref-seqs-v4.qza --i-reference-taxonomy ../reference/ref-tax.qza --i-class-weight ../reference/human-stool.qza --o-classifier classifier.qza

    qiime feature-classifier classify-sklearn --i-classifier classifier.qza --i-reads rep_seqs.qza --o-classification taxonomy.qza

You have now produced all the artifacts necessary for a basic exploratory analyses and could continue from here to analyse e.g. beta diversity and alpha diversity, as well as producing PCA plots. The next section details how to achieve the same result in python, rather than the command line.

Python Workflow
~~~~~~~~~~~~~~~

This section will demonstrate how to, using python, process data retrieved via redbiom into a form that can be used for further analysis.

Set up
^^^^^^

As well as QIIME 2 processing the data in python will require pandas (a data analysis and manipulation tool) and some QIIME 2 plugins:

* ``Feature_table`` allows us to filter, merge, transform and perform other operations on feature tables [2B]_ .
* ``Fragment_insertion`` improves phylogeny creation from sequence fragments by inserting the sequences into an existing high quality reference phylogeny rather than making a de novo phylogeny [3B]_ .
* ``Feature_classifier`` for taxonomic classification of QIIME 2 features [4B]_ .
* ``Metadata`` provides functionality for working with and visualizing metadata [5B]_ .

These are loaded into your IDE as follows:

.. code-block:: python

    #Set up
    Import biom
    import qiime as q
    import pandas as pd
    import sklearn
    from qiime2.plugins import feature_table, fragment_insertion, feature_classifier, metadata

If any of these are not present, install them through conda (search conda install <name of package> in your preferred internet browser for instructions on how to do so for said package).

Load and process data
^^^^^^^^^^^^^^^^^^^^^

The first step is to load the files retrieved using redbiom into QIIME 2 artifact type variables, these can then be recognised by QIIME 2 processing commands.

.. code-block:: python

    #load metadata
    meta = q.Metadata.load('<path to file>/<metadata file name>')

    #load sample data (biom table)
    sample_data = q.Artifact.import_data(type='FeatureTable[Frequency]',view='<path to file>/<biom table file name>', view_type='BIOMV210Format')

    #visualize the data
    vis_data = feature_table.visualizers.summarize(table=sample_data, sample_metadata=meta)

If you have trouble loading the metadata file then try use the keemie (google sheets) add-on to validate the metadata tsv file. It might also be worth re-fetching the sample, in case it has been corrupted by an incomplete download. The last command creates a feature table plot, like those in Qiita, which can help you decide how to filter the raw data. A feature in QIIME 2 is a unit of observation such as an OTU or ASV, or gene, or taxon.

You can (and should) save this visualization, and the generated QIIME 2 artifact feature table to your working directory using the following code:

.. code-block:: python

    sample_data.save("table.qza")
    vis_data.visualization.save("feature_table.qzv")

(It might be tidier to create a results directory, and then save the files to this by specifying the path to this directory in the command above.)

The next step is to perform quality control on the data: first filtering and discarding samples which have a total feature count under a threshold of 1000, so ensuring that samples with a low number of reads are removed. Further filtering to remove rare features i.e. ASVs that only appear a few times in the whole dataset should also be performed. Furthermore, it is also important to only include samples from the same body site (we will use feces as this is where most of the samples originate) and exclude samples that do not have exercise frequency logged (while this is a category, some participants may not have answered this particular question in the questionnaire). Finally, it may also be worth filtering out unhealthy individuals, who may bias the results (if health conditions limit exercise frequency then we may get a spurious result due to the correlation between ill health and low exercise frequency).

.. code-block:: python

    # Inclusion criterion
    criterion = "[body_site]='UBERON:feces'"\
    " AND [subset_healthy] IN ('true', 'True', 'TRUE')"\
    " AND [exercise_frequency] IN ('Never', 'Rarely (a few times/month)', 'Occasionally (1-2 times/week)', 'Regularly (3-5 times/week)', 'Daily')"

    # Keep only one sample if there are multiple samples from same subject
    ids_to_keep = meta.get_column('host_subject_id').to_series().drop_duplicates().index
    filtered_meta = meta.filter_ids(ids_to_keep)

    # Thresholds for filtering samples and features
    min_feature_per_sample= 1000
    min_per_feature = 3

    # Filter FeatureTable[Frequency] with feature-table filter-samples method to remove samples with a small library size
    sample_filtered_data = feature_table.methods.filter_samples(table=sample_data, min_frequency=min_feature_per_sample, metadata=filtered_meta, where=criterion)

    # Filter FeatureTable[Frequency] with feature-table filter-features method to remove very rare features
    feature_filtered_data = feature_table.methods.filter_features(table=filtered_data.filtered_table, min_frequency=min_per_feature)

    # Visualize the filtered table
    vis_filtered_data = feature_table.visualizers.summarize(table=filtered_data.filtered_table, sample_metadata=filtered_meta)


To save these to the results directory made in your working directory use the code below. By viewing the feature filtered with the QIIME 2 metadata plugin we can also extract the ids of those samples which have met all filtering criteria for future reference. The metadata format is converted to a dataframe, from which the indexes are extracted and each pasted on a new line to give a variable with the sample ids. These are then written to a file saved in the results directory - you can check this file in the command line with ``cat ./results/filtered.ids | head`` (from your working directory).

.. code-block:: python

    # save the filtered feature table and visualisations
    sample_filtered_data.filtered_table.save('./results/sample-filtered-table.qza')
    vis_sample_filtered.visualization.save('./results/sample-filtered-table.qzv')
    feature_filtered_data.filtered_table.save('./results/feature-filtered-table.qza')
    vis_feature_filtered.visualization.save('./results/feature-filtered-table.qzv')

    # for future reference save the ids of the samples that met filtering criteria
    filtered_table = feature_filtered_data.filtered_table.view(q.Metadata)
    filtered_ids = "\n".join(filtered_table.to_dataframe().index) + "\n"
    with open('./results/filtered.ids', 'w') as f:
    f.write(filtered_ids)

You have now obtained a filtered dataset, but will need to classify the features if you want to use analyses that take into account phylogenetic distance. Therefore we need to extract sequences from the dataset and ‘insert’ them into a reference phylogenetic tree (this placement identifies their taxonomic position). To extract representative sequences from the features we will use the ``feature_filtered_data`` (a frequency feature table) to make a fasta file (a universal DNA/protein sequence file format) of sequence feature data. You can view this file with ``less <file>`` or ``cat <file> | head``, as it is a plain text file. Often such files have information about the origin of the sequences (on the > line before the sequence), but we will use the sequence itself as an ID as the taxonomic data is currently unknown. Fragment insertion, mapping representative sequences from the samples to a reference database will allow taxonomic classification of the ASVs. First extract representative sequences from the data:

.. code-block:: python

    with open('./results/sequences.fna', 'w') as f:
    seqs = ''
    for i,seq in enumerate(feature_filtered_data.filtered_table.view(pd.DataFrame).columns):
        seqs = seqs + '>' + seq + '\n' + seq + '\n'
    f.write(seqs[:-1])

    # import the fasta file as a FeatureData[Sequence] artifact
    sequences = q.Artifact.import_data(type='FeatureData[Sequence]', view='./results/sequences.fna')


The first line here creates a writeable output file and assigns it to a variable. ``seqs = ‘’`` creates an empty string that is then filled in the following for loop. The for loop uses two variables ``i`` and ``seq`` representing the index and a column from the ``feature_filtered_data`` represented as a panda DataFrame. Each loop therefore writes a line with > and then the contents of the next column to seqs. Seqs is then written to the output file.We don’t necessarily know how many lines have been added to seqs but can specify to write out the slice from the first to the last index using [:-1] (or [0:-1]). 

Again, we can visualize this data and save it:

.. code-block:: python

    # visualize artifact and save both visualization and artifact
    vis_sequences = feature_table.visualizers.tabulate_seqs(data=sequences)
    sequences.save('./results/sequences.qza')
    vis_sequences.visualization.save('./results/sequences.qzv')

We can now create a tree to insert the fragments into. For this we will need reference data, this can be downloaded in the command terminal as follows: 
In your working directory (e.g. ``~/microbiome/exercise/``) create a directory for references (``mkdir reference``) and then use wget to download the data:

.. code-block:: bash

    mkdir reference
    cd reference
    # get the reference we need now
    wget https://data.qiime2.org/2020.2/common/sepp-refs-gg-13-8.qza
    # other reference files we will need later and may as well get now too
    wget https://github.com/BenKaehler/readytowear/raw/master/data/gg_13_8/515f-806r/human-stool.qza
    wget https://github.com/BenKaehler/readytowear/raw/master/data/gg_13_8/515f-806r/ref-seqs-v4.qza
    wget https://github.com/BenKaehler/readytowear/raw/master/data/gg_13_8/515f-806r/ref-tax.qza
    cd .. # return to the directory we have been working in


When the data is downloaded the sepp reference data can be loaded into your python IDE and the sample fragments inserted into the sepp tree. 

.. code-block:: python

    ### Fragment insertion
    # Load the reference data and insert sequences into sepp tree
    sepp_ref = q.Artifact.load('./reference/sepp-refs-gg-13-8.qza')
    sepp_result = fragment_insertion.methods.sepp(representative_sequences=sequences,
                                              reference_database=sepp_ref,
                                              threads=8,
                                              debug=True)


Once the sequences have been placed save the tree and placements as with the same save function we have been using throughout this section:
This last command is computationally costly (requires at least 12GB ram), and will take a while. If you are having trouble consider using a subset of the entire AGP dataset - you do not need to change your script, simply copy it into a new directory, repeat the redbiom data retrieval steps with the same names for the output files but with the ``shuf -n <number of samples>`` command piped into the initial sample ID retrieval command, and then run your script again in this new directory. Another possible solution is to lower the number of threads, though the process will take longer. 

We can also train a taxonomic classifier to classify the sequences. The fragment insertion generated a phylogeny, with the sequences inserted appropriately. The taxonomic classifier classifies the ASVs, assigning them to a particular clade (e.g. with good data to specific species) [1B]_ . While it is possible to use pre-trained classifiers these tend to give poorer results than those trained on data similar to that of the sample, therefore we will train  a classifier using human-stool samples. First we load the other references and the representative sequence:

.. code-block:: python

    # Load the representative sequences
    rep_seqs = qiime2.Artifact.import_data(type='FeatureData[Sequence]', view='./sequences.fna`)
    
    # Load the Greengenes sequences and taxonomy and Clawback human stool weights
    human_stool_weights = q.Artifact.load('./reference/human-stool.qza')
    ref_seqs_v4 = q.Artifact.load('./reference/ref-seqs-v4.qza')
    ref_tax = q.Artifact.load('./reference/ref-tax.qza')

We can then generate a classifier and classify the sequences:

.. code-block:: python

    # Generate a classifier with the loaded reference data
    human_stool_v4_result = feature_classifier.methods.fit_classifier_naive_bayes(reference_reads=ref_seqs_v4, reference_taxonomy=ref_tax, class_weight=human_stool_weights)

    # Use classifier to classify sequences
    bespoke_taxonomy = feature_classifier.methods.classify_sklearn(reads=rep_seqs, classifier=human_stool_v4_result.classifier, n_jobs=-1)



The classifier training will give a warning
`The TaxonomicClassifier artifact that results from this method was trained using scikit-learn version 0.23.1. It cannot be used with other versions of scikit-learn.`
You can check your version of scikit-learn by typing:

.. code-block:: python

    print('The scikit-learn version is {}.'.format(sklearn.__version__))

in your python console. If you have the correct version, ignore the warning. If not, update to the correct version using conda.

The classifier and the classifications should be saved.

.. code-block:: python

    human_stool_v4_result.classifier.save('./results/gg138-v4-human-stool_classifier.qza')
    bespoke_taxonomy.classification.save('./results/bespoke-taxonomy.qza')

We can also visualise this classification as a table:

.. code-block:: python

    taxonomy_vis = metadata.visualizers.tabulate(bespoke_taxonomy.classification.view(q.Metadata))
    taxonomy_vis.visualization.save('./results/bespoke-taxonomy.qzv')

With the data processed it is now possible to begin analysis. We have generated a feature table, representative sequences, an insertion tree and taxonomic classification and these will be sufficient for most simple exploratory analyses. 

Conclusion
~~~~~~~~~~

This tutorial has demonstrated how to process raw data retrieved through redbiom, using QIIME 2, either directly in the command line or through the python API. The processed data can now be analysed e.g. by calculating alpha and beta diversity metrics. To learn how to analyse the data visit the `QIIME 2 docs <https://docs.qiime2.org/>`__ and select an appropriate tutorial e.g. the Moving Pictures tutorial (skip to the Alpha and Beta Diversity Analysis section).

Bibliography
~~~~~~~~~~~~~~~

.. [1B] Bokulich NA, Kaehler BD, Rideout JR, Dillon M, Bolyen E, Knight R, Huttley GA, Gregory Caporaso J. 2018 Optimizing taxonomic classification of marker-gene amplicon sequences with QIIME 2’s q2-feature-classifier plugin. Microbiome 6, 90. (doi:10.1186/s40168-018-0470-z)

.. [2B] QIIME 2 2020.6.0 documentation. See https://docs.qiime2.org/2020.6/plugins/available/feature-table/

.. [3B] Janssen S et al. 2018 Phylogenetic Placement of Exact Amplicon Sequences Improves Associations with Clinical Information. mSystems 3, e00021-18

.. [4B] Bokulich NA, Kaehler BD, Rideout JR, Dillon M, Bolyen E, Knight R, Huttley GA, Gregory Caporaso J. 2018 Optimizing taxonomic classification of marker-gene amplicon sequences with QIIME 2’s q2-feature-classifier plugin. Microbiome 6, 90. (doi:10.1186/s40168-018-0470-z)

.. [5B] QIIME 2 2020.6.0 documentation. See https://docs.qiime2.org/2020.6/plugins/available/metadata/
