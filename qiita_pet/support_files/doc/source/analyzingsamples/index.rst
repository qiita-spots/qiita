Analyzing Samples
=================

Qiita now uses `QIIME2 <http://qiime2.org>`__ plugins for analysis.
-------------------------------------------------------------------
Thanks to this, we've got new layout of the analysis panel and the following new features:

* `Alpha Diversity <https://docs.qiime2.org/2020.2/plugins/available/diversity/alpha/>`__ (including statistics calculations; example `here <https://view.qiime2.org/visualization/?type=html&src=https%3A%2F%2Fdocs.qiime2.org%2F2020.2%2Fdata%2Ftutorials%2Fmoving-pictures%2Fcore-metrics-results%2Ffaith-pd-group-significance.qzv>`__)
* `Beta Diversity <https://docs.qiime2.org/2020.2/plugins/available/diversity/beta/>`__ (including stats)
* Principal Coordinate Analysis (`PCoA <https://docs.qiime2.org/2020.2/plugins/available/diversity/pcoa/>`__), including ordination results and EMPeror plots (example `here <https://view.qiime2.org/visualization/?type=html&src=https%3A%2F%2Fdocs.qiime2.org%2F2020.2%2Fdata%2Ftutorials%2Fmoving-pictures%2Fcore-metrics-results%2Funweighted_unifrac_emperor.qzv>`__)
* `Rarefaction <https://docs.qiime2.org/2020.2/plugins/available/feature-table/rarefy/>`__
* `Filter Samples <https://docs.qiime2.org/2020.2/plugins/available/feature-table/>`__
* `Taxa Summary <https://docs.qiime2.org/2020.2/plugins/available/taxa/barplot/>`__ (example `here <https://view.qiime2.org/visualization/?type=html&src=https%3A%2F%2Fdocs.qiime2.org%2F2020.2%2Fdata%2Ftutorials%2Fmoving-pictures%2Ftaxa-bar-plots.qzv>`__)

Creating A New Analysis
-----------------------

.. figure::  create_analysis.png
   :align:   center

* **Create New Analysis Page**

  * **Filter results by column data (Title, Abstract, PI, etc.)**: Searches for studies with the title/abstract/PI/etc. that you inputted
  * **Filter study by Study Tags**: Searches for studies with the tag you searched for
  * **Title**: Brings you to Study Information Page of that experiment
  * **Green Expand for Analysis Button**: Reveals the studies done on this data that can be used for further analysis
  * **Per Artifact Button**: Reveals the names of the artifacts, the number of samples in the prep info, and the files

    * **Add**: Adds data to be analyzed

      * More than 1 can be done at once to do large meta-data analysis

.. figure::  create_new_analysis.png
   :align:   center

* **Create New Analysis**: Creates the analysis using the data that has been added

  * **Analysis Name** (required): Name for the analysis that will be done
  * **Description** (optional): Description for the analysis that will be done

Single vs. Meta Analysis
------------------------------
* **Single analysis**: One study chosen to analyze
* **Meta-analysis**: Multiple studies chosen to analyze

  * *You can only merge like data*

Processing Network Page: Commands
---------------------------------

Rarefying Features
~~~~~~~~~~~~~~~~~~

.. figure::  rarefy.png
   :align:   center

* **Rarefy features**: Subsample frequencies from all samples without replacement so that the sum of frequencies in each sample is equal to the sampling-depth.

  *  **BIOM table** (required): Feature table containing the samples for which features should be rarefied
  *  **Parameter set**: Parameters at which the rarefication is run
  *  **Sampling depth** (required): Total frequency that each sample should be rarefied to, samples where sum of frequencies is less than sampling depth will not be included in resulting table

Note that rarefaction has some advantages for beta-diversity analyses
:ref:`[11]<reference11>`, but can have undesirable properties in tests of
differential abundance :ref:`[12]<reference12>`. To analyze your data with
alternative normalization strategies, you can easily download the raw biom
tables (see :doc:`../downloading`) and load them into an analysis
pipeline such as `Phyloseq <https://bioconductor.org/packages/release/bioc/html/phyloseq.html>`__.

Filtering Samples by Metadata
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. figure::  filtering.png
   :align:   center

* **Filter samples by metadata**: Filters samples from an OTU table on the basis of the number of observations in that sample, or on the basis of sample metadata

  * **BIOM table** (required): Feature table containing the samples for which features should be filtered
  * **Maximum feature frequency across samples** (optional): Maximum total frequency that a feature can have to be retained
  * **Maximum features per sample** (optional): Maximum number of features that a sample can have to be retained
  * **Minimum feature frequency across samples** (optional): Minimum total frequency that a feature must have to be retained
  * **Minimum features per sample** (optional): Minimum number of features that a sample can have to be retained
  * **SQLite WHERE-clause** (optional): Metadata group that is being filtered out

    * If you want to filter your samples by body_site and you want to only keep the tongue samples, fill the clause this way: ``body_site = 'UBERON:tongue'``
    * If you want to filter your samples by body_site and you want to only remove the tongue samples, fill the clause this way: ``body_site != 'UBERON:tongue'``

Summarizing Taxa
~~~~~~~~~~~~~~~~

.. figure::  summarize_taxa.png
   :align:   center

* **Summarize Taxa**: Creates a bar plot of the taxa within the analysis

  * *Can only be performed with closed-reference data*
  * **BIOM table** (required): Feature table containing the samples to visualize at various taxonomic levels

Calculating Alpha Diversity
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. figure::  alpha_diversity.png
   :align:   center

* **Calculate alpha diversity** :ref:`[13]<reference13>` : Measures the diversity within a sample

  * **BIOM table** (required): Feature table containing the samples for which alpha diversity should be computed

    * **Diversity metric** (required): Alpha diversity metric to be run

      * **Abundance-based Coverage Estimator (ACE) metric** :ref:`[14]<reference14>` : Calculates the ACE metric

        * Estimates species richness using a correction factor

      * **Berger-Parker Dominance Index** :ref:`[15]<reference15>` : Calculates Berger-Parker dominance index

        * Relative richness of the abundant species

      * **Brillouin’s index** :ref:`[16]<reference16>` : Calculates Brillouin’s index

        * Measures the diversity of the species present

        * Use when randomness can’t be guaranteed

      * **Chao1 index** :ref:`[14]<reference14>` : Calculates Chao1 index

        * Estimates diversity from abundant data
        * Estimates number of rare taxa missed from undersampling

      * **Dominance measure**: Calculates dominance measure

        * How equally the taxa are presented

      * **Effective Number of Species (ENS)/Probability of intra-or interspecific encounter (PIE) metric** :ref:`[17]<reference17>` : Calculates Effective Number of Species (ENS)/Probability of intra-or interspecific encounter (PIE) metric

        * Shows how absolute amount of species, relative abundances of species, and their intraspecific clustering affect differences in biodiversity among communities

      * **Faith’s phylogenetic diversity** :ref:`[18]<reference18>` : Calculates faith’s phylogenetic diversity

        * Measures of biodiversity that incorporates phylogenetic difference between species
        * Sum of length of branches

      * **Fisher’s index** :ref:`[19]<reference19>` : Calculates Fisher’s index

        * Relationship between the number of species and the abundance of each species

      * **Gini index** :ref:`[20]<reference20>` : Calculates Gini index

        * Measures species abundance
        * Assumes that the sampling is accurate and that additional data would fall on linear gradients between the values of the given data

      * **Good’s coverage of counts** :ref:`[21]<reference21>` : Calculates Good’s coverage of counts.

        * Estimates the percent of an entire species that is represented in a sample

      * **Heip’s evenness measure** :ref:`[22]<reference22>` : Calculates Heip’s evenness measure.

        * Removes dependency on species number

      * **Lladser’s point estimate** :ref:`[23]<reference23>` : Calculates Lladser’ point estimate

        * Estimates how much of the environment contains unsampled taxa
        * Best estimate on a complete sample

      * **Margalef’s richness index** :ref:`[24]<reference24>` : Calculates Margalef’s richness index

        * Measures species richness in a given area or community

      * **Mcintosh dominance index D** :ref:`[25]<reference25>` : Calculates McIntosh dominance index D

        * Affected by the variation in dominant taxa and less affected by the variation in less abundant or rare taxa

      * **Mcintosh evenness index E** :ref:`[22]<reference22>` : Calculates McIntosh’s evenness measure E

        * How evenly abundant taxa are

      * **Menhinick’s richness index** :ref:`[24]<reference24>` : Calculates Menhinick’s richness index

        * The ratio of the number of taxa to the square root of the sample size

      * **Michaelis-Menten fit to rarefaction curve of observed OTUs** :ref:`[26]<reference26>` : Calculates Michaelis-Menten fit to rarefaction curve of observed OTUs.

        * Estimated richness of species pools

      * **Number of distinct features** :ref:`[27]<reference27>` : Calculates number of distinct OTUs
      * **Number of double occurrences**: Calculates number of double occurrence OTUs (doubletons)

        * OTUs that only occur twice

      * **Number of single occurrences**: Calculates number of single occurrence OTUs (singletons)

        * OTUs that appear only once in a given sample

      * **Pielou’s evenness** :ref:`[28]<reference28>` : Calculates Pielou’s eveness

        * Measure of relative evenness of species richness

      * **Robbins’ estimator** :ref:`[29]<reference29>` : Calculates Robbins’ estimator

        * Probability of unobserved outcomes

      * **Shannon’s index** :ref:`[30]<reference30>` : Calculates Shannon’s index

        * Calculates richness and diversity using a natural logarithm
        * Accounts for both abundance and evenness of the taxa present

      * **Simpson evenness measure E** :ref:`[31]<reference31>` : Calculates Simpson’s evenness measure E.

        * Diversity that account for the number of organisms and number of species

      * **Simpson’s index** :ref:`[31]<reference31>` : Calculates Simpson’s index

        * Measures the relative abundance of the different species making up the sample richness

      * **Strong’s dominance index (Dw)** :ref:`[32]<reference32>` :  Calculates Strong’s dominance index

        * Measures species abundance unevenness

    * **Phylogenetic tree** (required for Faith PD): Phylogenetic tree to be used with alpha analyses (only include when necessary)

      * Currently the only tree that can be used is the GreenGenes 97% OTU based phylogenetic tree

Calculating Beta Diversity
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. figure::  beta_diversity.png
   :align:   center

* **Calculate beta diversity** :ref:`[13]<reference13>` : Measured the diversity between samples

  * **BIOM table** (required): Feature table containing the samples for which beta diversity should be computed
  * **Adjust variance** :ref:`[33]<reference33>` (phylogenetic only): Performs variance adjustment

    * Weighs distances based on the proportion of the relative abundance represented between the samples at a given node under evaluation

  * **Alpha value** (Generalized UniFrac only): Controls importance of sample proportions

    * 1.0 is weighted normalized UniFrac. 0.0 is close to unweighted UniFrac, but only if the sample  are dichotomized.

  * **Bypass tips** (phylogenetic only): In a bifurcating tree, the tips make up about 50% of the nodes in a tree. By ignoring them, specificity can be traded for reduced compute time. This has the effect of collapsing the phylogeny, and is analogous (in concept) to moving from 99% to 97% OTUs
  * **Diversity metric** (required): Beta diversity metric to be run

    * **Bray-Curtis dissimilarity** :ref:`[34]<reference34>` : Calculates Bray–Curtis dissimilarity

      * Fraction of overabundant counts

    * **Canberra distance** :ref:`[35]<reference35>` : Calculates Canberra distance

      * Overabundance on a feature by feature basis

    * **Chebyshev distance** :ref:`[36]<reference36>` : Calculates Chebyshev distance

      * Maximum distance between two samples

    * **City-block distance** :ref:`[37]<reference37>` :  Calculates City-block distance

      * Similar to the Euclidean distance but the effect of a large difference in a single dimension is reduced

    * **Correlation coefficient** :ref:`[38]<reference38>` : Measures Correlation coefficient

      * Measure of strength and direction of linear relationship between samples

    * **Cosine Similarity** :ref:`[39]<reference39>` : Measures Cosine similarity

      * Ratio of the amount of common species in a sample to the mean of the two samples

    * **Dice measures** :ref:`[40]<reference40>` : Calculates Dice measure

      * Statistic used for comparing the similarity of two samples
      * Only counts true positives once

    * **Euclidean distance** :ref:`[41]<reference41>` : Measures Euclidean distance

      * Species-by-species distance matrix

    * **Generalized Unifrac** :ref:`[42]<reference42>` : Measures Generalized UniFrac

      * Detects a wider range of biological changes compared to unweighted and weighted UniFrac

    * **Hamming distance** :ref:`[43]<reference43>` : Measures Hamming distance

      * Minimum number of substitutions required to change one group to the other

    * **Jaccard similarity index** :ref:`[44]<reference44>` : Calculates Jaccard similarity index

      * Fraction of unique features, regardless of abundance

    * **Kulczynski dissimilarity index** :ref:`[45]<reference45>` : Measures Kulczynski dissimilarity index

      * Describes the dissimilarity between two samples

    * **Matching components** :ref:`[46]<reference46>` : Measures Matching components

      * Compares indices under all possible situations

    * **Rogers-tanimoto distance** :ref:`[47]<reference47>` : Measures Rogers-Tanimoto distance

      * Allows the possibility of two samples, which are quite different from each other, to both be similar to a third

    * **Russel-Rao coefficient** :ref:`[48]<reference48>` : Calculates Russell-Rao coefficients

      * Equal weight is given to matches and non-matches

    * **Sokal-Michener coefficient** :ref:`[49]<reference49>` : Measures Sokal-Michener coefficient

      * Proportion of matches between samples

    * **Sokal-Sneath Index** :ref:`[50]<reference50>` : Calculates Sokal-Sneath index

      * Measure of species turnover

    * **Species-by-species Euclidean** :ref:`[41]<reference41>` : Measures Species-by-species Euclidean

      * Standardized Euclidean distance between two groups
      * Each coordinate difference between observations is scaled by dividing by the corresponding element of the standard deviation

    * **Squared Euclidean** :ref:`[41]<reference41>` : Measures squared Euclidean distance

      * Place progressively greater weight on samples that are farther apart

    * **Unweighted Unifrac** :ref:`[51]<reference51>` : Measures unweighted UniFrac

      * Measures the fraction of unique branch length

    * **Weighted Minkowski metric** :ref:`[52]<reference52>` : Measures Weighted Minkowski metric

      * Allows the use of the k-means-type paradigm to cluster large data sets

    * **Weighted normalized UniFrac** :ref:`[53]<reference53>` : Measures Weighted normalized UniFrac

      * Takes into account abundance
      * Normalization adjusts for varying root-to-tip distances.

    * **Weighted unnormalized UniFrac** :ref:`[53]<reference53>` : Measures Weighted unnormalized UniFrac

      * Takes into account abundance
      * *Doesn't correct for unequal sampling effort or different evolutionary rates between taxa*

    * **Yule index** :ref:`[19]<reference19>` : Measures Yule index

      * Measures biodiversity
      * Determined by the diversity of species and the proportions between the abundance of those species.

  * **Number of jobs**: Number of workers to use
  * **Phylogenetic tree** (required for Weighted Minkowski metric and all UniFrac metrics): Phylogenetic tree to be used with beta analyses (only include when necessary)

    * Currently the only tree that can be used is the GreenGenes 97% OTU based phylogenetic tree

Calculating Alpha Correlation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. figure::  alpha_correlation.png
   :align:   center

* **Calculate alpha correlation** :ref:`[54]<reference54>` : Determines if the numeric sample metadata category is correlated with alpha diversity

  * **Alpha Vectors** (required): Vector of alpha diversity values by sample
  * **Correlation Method** (required): Correction test being applied

    * **Spearman** :ref:`[55]<reference55>` : Measures if there is a linear relationship between 2 variables
    * **Pearson** :ref:`[56]<reference56>` : Measures how strong the linear relationship is between 2 variables

Performing Principal Coordinate Analysis
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. figure::  pcoa.png
   :align:   center

* **Perform Principal Coordinate Analysis (PCoA)** :ref:`[57]<reference57>` : Visualizes the similarities and differences between samples using Emperor Plots :ref:`[58]<reference58>`

  * **Distance matrix** (required): Distance matrix on which the PCoA should be computed

Calculating Beta Group Significance
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. figure::  beta_group_significance.png
   :align:   center

* **Calculate beta group significance**: Determines whether groups of samples are significantly different from one another using a permutation-based statistical test

  * **Distance matrix** (required): Matrix of distances between pairs of samples
  * **Comparison Type** (required): Perform or not perform pairwise tests between all pairs of groups in addition to the test across all groups
  * **Metadata category** (required): Category from metadata file or artifact viewable as metadata
  * **Method** (required): Correlation test being applied

    * **Anosim** :ref:`[59]<reference59>` :  Describes the strength and significance that a category has in determining the distances between points and can accept either categorical or continuous variables in the metadata mapping file
    * **Permanova** :ref:`[60]<reference60>` : Describes the strength and significance that a category has in determining the distances between points and can accept categorical variables

  * **Number of permutations** (required): Number of permutations to be run when computing p-values

Calculating Beta Correlation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. figure::  beta_correlation.png
   :align:   center

* **Calculate beta correlation**: Identifies a correlation between the distance matrix and a numeric sample metadata category

  * **Distance-matrix** (required): Matrix of distances between pairs of samples
  * **Correlation method** (required): Correlation test being applied

    * **Spearman** :ref:`[55]<reference55>` : Measures if there is a linear relationship between 2 variables
    * **Pearson** :ref:`[56]<reference56>` : Measures how strong the linear relationship is between 2 variables

  * **Metadata-category** (required): Category from metadata file or artifact viewable as metadata
  * **Number of permutations** (required): Number of permutations to be run when computing p-values

Processing Network Page: Results
--------------------------------

Taxa Bar Plot
~~~~~~~~~~~~~

.. figure::  taxa_barplot.png
   :align:   center

* **Taxonomic Level**: How specific the taxa will be displayed

  * 1- Kingdom, 2- Phylum, 3- Class, 4- Order, 5- Genus, 6- Species, 7- Subspecies

* **Color Palette**: Changes the coloring of your taxa bar plot

  * **Discrete**: Each taxon is a different color
  * **Continuous**: Each taxon is a different shade of one color

* **Sort Sample By**: Sorts data by sample metadata or taxonomic abundance and either by ascending or descending order

Alpha Diversity Box Plots and Statistics
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. figure::  alpha_diversity_boxplot.png
   :align:   center

.. figure::  alpha_diversity_kruskal_wallis.png
   :align:   center

* **Boxplot**: Shows how different measures of alpha diversity correlate with different metadata categories
* **Category**: Choose the metadata category you would like to analyze
* **Kruskal-Wallis** :ref:`[61]<reference61>` : Result of Kruskal-Wallis tests

  * Says if the differences are statistically significant

Alpha Correlation Box Plots and Statistics
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. figure::  alpha_correlation_plot.png
   :align:   center

* **Boxplot**: Shows how different measures of alpha diversity correlate with different metadata categories

  * Gives the Spearman or Pearson result (rho and p-value)

Beta Diversity Distance Matrix
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. figure::  beta_diversity_plot.png
   :align:   center

* **Distance Matrix**: Dissimilarity value for each pairwise comparison

Principal Coordinate Analysis Plot
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. figure::  PCoA_plot.png
   :align:   center

* **Emperor Plot**: Visualization of similarities/dissimilarities between samples

  * **Color**: Choose colors for each group

    * **Color Category**: Groups each sample by the given category chosen by a given color

  * **Visibility** Allows for making certain samples invisible

    * *Does not remove them from the analysis*

      * Must perform filtering to do that

  * **Opacity**: Change the transparency of a given category
  * **Scale**: Change the size of a given category
  * **Shape**: Groups each sample by the given category chosen by a given shape
  * **Axes**: Change the position of the axis as well as the color of the graph
  * **Animations**: Traces the samples sorted by a metadata category

    * *Requires a gradient column (the order in which samples are connected together, must be numeric) and a trajectory column (the way in which samples are grouped together) within the sample information file*
    * *Works best for time series*

Beta Group Significance Box Plots and Statistics
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. figure::  beta_group_significance1.png
   :align:   center

.. figure::  beta_group_significance2.png
   :align:   center

* **Boxplot**: Shows how different measures of beta diversity correlate with different metadata categories
* Gives the Permanova or Anosim result (psuedo-F and p-value)

Beta Correlation
~~~~~~~~~~~~~~~~

.. figure::  beta_correlation1.png
   :align:   center

.. figure::  beta_correlation2.png
   :align:   center

* Gives the Spearman or Pearson result (rho and p-value)

  * **Spearman** :ref:`[55]<reference55>` : Measures if there is a linear relationship between 2 variables
  * **Pearson** :ref:`[56]<reference56>` : Measures how strong the linear relationship is between 2 variables

* Gives scatterplot of the distance matrix on the x-axis and the variable being tested on the y-axis

-------------------------------------------------------------------------------

Statistical Analysis to Justify Clinical Trial Sample Size Tutorial
-------------------------------------------------------------------

The goal of this tutorial is to demonstrate how to analyse public data similar to that one may obtain from one’s own proposed study; and use this to find the minimum sample size needed for appropriate/sufficient statistical power. This will allow relevant conclusions to be drawn for the minimum clinical trial size in one’s actual (own) study. The information obtained using this public data will therefore allow justification of the clinical trial format, and strengthen e.g. grant applications. 

This tutorial is based on Casals-Pascual et al 2020 and will be analysing the same data, to reproduce the figures and statistics found in the paper [1]_ . The tutorial continues on from the `Retrieving Public Data for Own Analysis Tutorial` (see under redbiom) and expects that you can find the example data from study 1629, using the Qiita redbiom plugin.

To reproduce the figures and results in Casals-Pascual et al 2020 we first need to process the raw data from study 1629 to obtain an Alpha_diversity artifact and a Beta_diverstiy artifact for the data. This stage of the tutorial will be completed within the Qiita processing interface, though note that it could be completed in QIIME 2 instead. We will also need the Metadata artifact from the original study. The second half of the process, producing the figures can then be completed either in python or in R.

Set up
~~~~~~

Please follow the instructions in the `Retrieving Public Data for Own Analysis Tutorial` (see under redbiom) for the first example to find the data required for this tutorial.

For later analysis you will require either a python script editor or R studio.
Python scripts can be written directly in the command line editor vi but if you are a beginner this is not very user friendly, and I would recommend installing spyder (``conda install spyder``, presuming you have `miniconda <https://docs.conda.io/en/latest/miniconda.html>`__ ) which can then be launched from the command line by typing ``spyder``.
R-studio can be downloaded via the command line using conda if you have miniconda/anaconda. It can also be downloaded and function independently of the command line (note you need to install both R and R-studio in this case). There are many tutorials for this online e.g. `here <https://www.datacamp.com/community/tutorials/installing-R-windows-mac-ubuntu>`__ or `here <https://techvidvan.com/tutorials/install-r/>`__ .

Find and process data in Qiita
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Once you have selected the study 1629 (see `Retrieving Public Data for Own Analysis Tutorial` under redbiom) there are four artifacts, these are:

#. *Pick closed-reference OTUs (reference-seq: /databases/gg/13_8/rep_set/97_otus.fasta) | Split libraries FASTQ*.
    * This tells us that the data is picked OTUs clustered by closed reference against /databases/gg/13_8/rep_set/97_otus.fasta and is now in a split library FASTQ format.
    * FASTQ stores both sequence and corresponding quality score see `here <https://emea.support.illumina.com/bulletins/2016/04/fastq-files-explained.html>`__ for more info (though note the data in FASTQ format does not have to be illumina sequencing data).
    * Split refers to demultiplexing where sequences from the same lane are split into samples based on barcodes (N.B. illumina can sequence multiple different samples at the same time, therefore sequence data has to be demultiplexed into the separate samples present in the same lane.)
#. *Pick closed-reference OTUs (reference-seq: /databases/gg/13_8/rep_set/97_otus.fasta) | Trimming (length: 90)*
    * This is essentially the same as the previous artifact but the reads have been trimmed to 90nt (see contexts for an explanation of why this is done).
#. *Deblur (Reference phylogeny for SEPP: Greengenes_13.8, BIOM: /projects/qiita_data/BIOM/60941/reference-hit.biom) | Trimming (length: 90)*
    * Deblur processed sequence data trimmed to 90nt and classified by taxonomy using the greengenes reference database. This artifact contains only those sequences which have been classified thus reference-**hit**.biom
    * SEPP is a phylogenetic placement program that can be used to place query sequences (reads e.g. of the V4 region of 16S) into the phylogeny of the full length gene’s tree (e.g. in this case using the Greengenes database).
#. *Deblur (Reference phylogeny for SEPP: Greengenes_13.8, BIOM: /projects/qiita_data/BIOM/60942/all.biom) | Trimming (length: 90)*
    * This artifact been processed in the same manner as the previous artifact, but all ASVs are present, including those that did not get placed (therefore **all**.biom).

For the Deblur data we will use the reference-hit.biom data as this represents those ASVs which were placed within the Greengenes database. Using the all.biom data would give all ASVs, but the unplaced sequences would have to be removed to allow later analysis with Unifrac (so that they may as well not be present) and therefore we select the reference-hit data from the start. N.B. unifrac uses phylogenetic distance (measures of relatedness), thus the need for placed sequences.
For the OTUs, the trimmed sequences are appropriate, as they represent a later step in the processing pipeline of the raw data.

With these two artifacts selected proceed to *create analysis*. Both samples will need to be rarefied and then have alpha and beta diversity artifacts created. For a general overview of processing data in the Qiita processing interface see this `Qiita docs <https://qiita.ucsd.edu/static/doc/html/index.html>`__ . To rarefy the data select the artifact -> *process* -> *rarefy*, modify the options of rarefy so that total frequency is a 10000 for both -> *add command* -> *run*.
The cut off frequency is an individual choice, but the use of 10 000 strikes a compromise between losing data from samples with large library sizes and discarding samples with smaller library size. One can look at the frequency tables of the biom artifacts to get an idea of what would be an appropriate cut off. In this case 10 000 will allow most samples to be used, while maintaining quality. Once rarefaction has completed the `rarefied_table` artifact can be used for alpha and beta diversity calculations. Select the `rarefied_table` artifact, *process* -> *alpha diversity (phylogenetic) [alpha_phylogenetic]* and in options use the default option of Faith’s index then *add command* -> *run*. Beta Diversity can be calculated with *Beta Diversity (phylogenetic)* (this uses Unifrac). For the OTU artifact one can specify the phylogenetic tree from the database (as closed OTUs inherently have taxonomy data). For the Deblur artifact use the ‘artifact tree, if exists’ option. The artifact we are using has been aligned to a reference database, but not all deblur data will necessarily have associated taxonomy data.
The distance matrix produced by the Beta Diversity process will allow us to run a principal coordinate analysis, while this is not necessary for reproducing the plots, it allows one to visualise the data and so get an intuitive idea of what it represents.

Retrieve artifacts/data from Qiita and create figures
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To reproduce the plots in the paper we need to produce two figures (three plots). The first shows sample size against power (1 - P(type II error)) which is used to find statistically significant differences in alpha diversity. This allows one to calculate the standard sample size required to detect an effect between a group and the control population. This sample size will be affected by the effect size, so we need to plot power for at least three different effect sizes. Casals-Pascual et al 2020. use 0.55, 0.82, 1.00 because these represent a difference in Faith’s PD (a measure of phylogenetic distance) of 2, 3, and 4. The group being used to calculate alpha diversity is B1.
The second figure includes two plots: the first plots sample size against power (1 - P(type II error)) to find statistically significant differences in Beta diversity (in this case pairwise distances between the two groups). Again, multiple scenarios are used, in this case significance levels of 0.001, 0.01, 0.05 and 0.1. The second is a histogram showing the distribution of pairwise distances within and between the two sample groups. The groups are B1 and B2/3 (i.e. B1 samples are compared to all other samples).

Download data from Qiita
^^^^^^^^^^^^^^^^^^^^^^^^

This can be done in the command line using wget and the links from your Qiita study. Select an artifact followed by ‘generate download link’ if your study is private. If your study is public one can simply use the artifact ID as described in the [Retrieving Public Data tutorial](LINK TO THIS). Use the -O option to specify the output (downloaded) file’s name. We also need the study metadata, this can be retrieved from the study page, under sample information, copy the link address of the sample info download button.

.. code-block:: bash

    wget -O alpha_div_artifact.zip “<link for alpha diversity artifact>”
    wget -O beta_div_artifact.zip "<link for beta diversity artifact>"
    wget -O metadata.zip “<https://qiita.ucsd.edu/public_download/?data=sample_information&study_id=<study-id>”

To have this run ‘quietly’ (without showing any output) add the -q option. However, note that running in quiet mode might lead to missed error messages. Certain errors, suggesting that the zipfile is corrupt, can be `ignored <https://qiita.ucsd.edu/static/doc/html/faq.html#how-to-solve-download-or-unzip-errors>`__ .
When the files have been downloaded unzip them with ``unzip <file name>``.

If you did not merge samples when creating your analysis the sample IDs in the beta and alpha diversity artifacts may not match those of the metadata, as they will have your rarefied artifact ID appended to the sample ID. To make the sample IDs match, the simplest fix is to change the metadata file as it is an easily manipulatable .txt file. The code below will append your rarified table ID to the metadata IDs

.. code-block:: bash

    cat ./templates/<name of your metdata file> | sed “s/^1629/<rarified table in Qiita ID>.1629/g” > ./templates/metadata.txt

Check this has worked with ``cat templates/metadata.txt | less``.

Python workflow
~~~~~~~~~~~~~~~

This section works through the `code <https://github.com/knightlab-analyses/sample-size-stat-power-clinical-microbiome>`__ accompanying the aforementioned paper. Alternatively, you can skip this section and use R studio for the same end result figures.

Set up environment
^^^^^^^^^^^^^^^^^^

There are various modules required to complete this analysis in python.

* ``qiime2``: a bioinformatics platform for next generation microbiome data.
* ``pandas``: a data analysis and manipulation tool.
* ``Seaborn``: a data visualization library based on matplotlib which facilitates drawing statistical graphics.
* ``Matplotlib.pyplot``: a matplotlib interface (allows plotting in a manner similar to that in MATLAB which is a programming language).
* ``skbio/scikit-bio``: a python package which is used by QIIME 2 (i.e. a dependency), from which the DistanceMatrix function is required.
* ``statistics``: a python package for functions such as mean and stdev
* From ``statsmodels.stats.power`` the ``tt_ind_solve_power`` function is required - this is a function that allows calculation of the power of a two sample t-test given relevant data.

It is likely that these packages will already be present if you are using conda and have installed QIIME 2. If any are missing do an internet search for the package name + conda; one of the top hits will be from the anaconda cloud, and give instructions for installing the package. Alternatively, you can use ``conda search <package name>`` within the command line.

Open your preferred python IDE or script editor, and make a new script. To set-up the environment use:

.. code-block:: python

    import pandas as pd
    import qiime2 as q2
    import seaborn as sns
    import matplotlib.pyplot as plt

    from statsmodels.stats.power import tt_ind_solve_power
    from statistics import mean, stdev
    from skbio import DistanceMatrix

Process the artifact data
^^^^^^^^^^^^^^^^^^^^^^^^^

**Metadata**

The metadata file unpacks to a folder template, with one file 1629_20180101-113841.txt. If you have used the earlier command to append an artifact ID to the sample ID this name may be different. To assign the metadata to a variable use:

.. code-block:: python

    metadata = pd.read_csv('./templates/<metadata file name>', sep='\\t', dtype=str, index_col=0, engine='python')
    

This code assigns the metadata information to the variable metadata, using the pandas ``read_csv function``, the ``sep =`` sets the separator of the data columns, ``index_col`` specifies the column to use as the index, ``dtype`` specifies the data type for the columns, and ``engine`` specifies the parser. The variable metadata now consists of 38 columns specifying the metadata details of the 683 patients.

Next, using QIIME 2, the alpha_diversity artifact can be be added to the metadata variable in a new column (deblur alpha diversity):

.. code-block:: python

    metadata['deblur alpha diversity'] = q2.Artifact.load('./alpha_vector/<appropriate ID>/alpha_diversity.qza').view(pd.Series)
    metadata.dropna(subset=['deblur alpha diversity'], inplace=True)

The ``view(pd.Series)`` is used to view the artifact (loaded by QIIME 2) in panda series format - in this format the data can be appended to the metadata variable. A panda series is an array that can be made from data input such as csv files and existing storage. The last line of code drops those rows with NA (not applicable) values (i.e. missing values) in the deblur alpha diversity column from the data frame. Inplace specifies editing of the object in place rather than returning the output as a new dataframe.

When working through someone else's code it is often a good aid to understanding to print various variables along the way, this gives a better idea of what is happening, and will flag any possible errors. E.g. at this stage try

.. code-block:: python

    print(metadata[metadata ['deblur alpha diversity']])

Next we can divide the data into groups:

.. code-block:: python

    b1 = metadata[metadata.cd_behavior == 'Non-stricturing, non-penetrating (B1)']
    bother = metadata[(metadata.cd_behavior != 'Non-stricturing, non-penetrating (B1)') & (metadata.cd_behavior != 'not applicable')]

    dtx = q2.Artifact.load('<path to distance matrix artifact/distance artifact .qza>').view(DistanceMatrix)

    b1_dtx = dtx.filter(ids=b1.index).to_series().values
    bother_dtx = dtx.filter(ids=bother.index).to_series().values

This code makes a variable representing the b1 group. This variable (``b1``) contains all rows in the metadata object which have cd_behaviour equal to the B1 phenotype (Non-structuring, non-penetrating (B1). ``b1_dtx`` contains all the values in the distance matrix after filtering for b1. To do this required loading the distance matrix data into a variable using q2.Artifact.load. We also create variables containing all other non-B1 and present (not NA) data from the metadata and dtx variables.

**Alpha diversity data**

Now we have processed the data into a python readable format we can calculate variables such as the standard deviation and the mean:

.. code-block:: python
 
    sd1 = b1['deblur alpha diversity'].std()
    sd2 = bother['deblur alpha diversity'].std()
    sd12 = mean([sd1, sd2])

Again, print these to see if they look as expected, or, if you are using an appropriate IDE (such as spyder), you can look at their values and type in the inbuilt variable explorer. Next we will make a data frame containing the data for the first plot

.. code-block:: python

    # significance level
    alpha = 0.05 

    #create empty list
    data_alpha = [] 

    #in steps of 5 from 10 to 55
    for observations in range(10, 155, 5):
    #for differences in Faiths PD representative of effect sizes 0.55, 0.82, 1.00
        for difference in [2, 3, 4]:
            #effect size calculation	
       		effect_size = difference/sd12
       		x = tt_ind_solve_power(effect_size=effect_size,
                #number of observations, iterated by the loop
                nobs1=observations, 	
                #significance level
                alpha=alpha,
                #number of observations for second group presumed to be equal to first group's observations
                ratio=1.0,
                alternative='two-sided')	
            data_alpha.append({	
                #append parameters and output to list
                'alpha': alpha, 'Power (1-β)': x,
                'Total sample size (N)': observations * 2,
                'Difference': '%d (effect size %0.2f)' % (difference, effect_size)})

    #turn the list created in the loop into dataframe
    data_alpha = pd.DataFrame(data_alpha)							
    
    
``tt_ind_solve_power`` solves for any one parameter of a two sample t-test. In this case we are using it to find power given all data. It requires effect_size, nobs1, alpha, power and ratio; where exactly one needs to be None (and is calculated), while all others need numeric values.

* ``Effect_size`` is the standardized effect size, the difference between the two means divided by the standard deviation.
* ``Nobs1`` is the number of observations of sample 1 (which we generate with a loop, in steps of 5 from 10 to 55).
* ``Ratio`` is used to specify the ratio between the number of observations of group one and two; so that ``nobs2 = nobs1 * ratio``.
* ``Alpha`` is the significance level - that is the probability of a type I error; that is the probability of finding a significant effect when the null hypothesis is actually true.
* ``Power`` - is what we want to calculate, it is (1 - the probability of a type II error). A type II error is falsely finding a non-significant effect and accepting the null hypothesis (when there is in fact a significant effect).

Our extra parameter, alternative, ensures that the power is calculated for a two-tailed t-test (this is default in anycase).
The outcome of this code is therefore to calculate the power for a given alpha and difference over a range of sample sizes (represented by observation), and then append all parameters appropriately to a list which is then processed to form a data-frame which we can use as input for plotting.

**Beta diversity data**

The process for obtaining the points to plot for beta diversity is similar to that for alpha diversity but now we are considering two groups, and therefore the difference between them. The absolute difference in the two groups’ means divided by their mean standard deviation gives the effect size:

.. code-block:: python

    u2u1 = abs(mean(b1_dtx) - mean(bother_dtx))
    effect_size = u2u1/mean([stdev(b1_dtx), stdev(bother_dtx)])

Note here that ``stdev()`` is used rather than ``std()``. ``std()`` calculates population standard deviation, while ``stdev()`` calculates sample standard deviation. For alpha diversity we consider only the contents of the particular sample (i.e. we are not comparing to any other group but rather attempting to find whether the sample is significantly different from the entire population) and therefore, for the null hypothesis can treat it as the population. However, for beta-diversity comparison between groups means that no one group cannot be considered as necessarily representative of the whole population and so sample standard deviation is used.

Again, a list is created by appending iterated ``tt_ind_solve_power`` output and parameters, and this list is then converted to a dataframe. However, this time we iterate through different significance levels rather than effect levels.

.. code-block:: python

    data_beta = []
    for observations in range(10, 155, 5):
        for alpha in [.001, .01, .05, .1]:
            x = tt_ind_solve_power(effect_size=effect_size, nobs1=observations,
                    alpha=alpha, ratio=1.0,
                    alternative='two-sided')
            data_beta.append({
                    'Significance level (α)': alpha, 'Power (1-β)': x,
                    'Total sample size (N)': observations * 2,
                    'Difference': '%d (effect size %0.2f)' % (difference, effect_size)})
   data_beta = pd.DataFrame(data_beta)

We have now generated the necessary data to create the relevant plots.

Create Figures
^^^^^^^^^^^^^^

**Figure 1**

We will use ``fig``, which allows the creation of a background (blank canvas) upon which further commands will take effect, the rest of the first line formats this background. ``sns.set`` can be used to set aesthetic parameters of the graph including plotting context such as grid line width, adjust the parameters of the plotting line axes and specify the axes titles.

.. code-block:: python

    fig, ax1 = plt.subplots(figsize=(15, 9))

    sns.set(style="whitegrid")
    sns.set_context("paper", font_scale=2,
    rc={'lines.linewidth': 2, 'lines.markersize': 12})

    f = sns.lineplot(x='Total sample size (N)', y='Power (1-β)', markers=True, dashes=False, style='Difference', ax=ax1, data=data_alpha)		#plot the data itself
    
    #x.axis ticks every 20 units
    ax1.xaxis.set_major_locator(plt.MultipleLocator(20))

    plt.axhline(0.8, 0, data_alpha['Total sample size (N)'].max())

    fig.savefig('figure1.pdf')

**Figure 2**

Figure 2 has two graphs within it. This requires a grid to place them within, with three columns, two for the one graph, one for the other graph, on a single row. Then we can plot the two graphs, using similar syntax to the previous figure.

.. code-block:: python

    fig = plt.figure(figsize=(20, 8))
    grid = plt.GridSpec(ncols=3, nrows=1, hspace=0.2, wspace=0.2)

    # add two new plots to grid
    ax1 = fig.add_subplot(grid[0, :2])
    ax2 = fig.add_subplot(grid[0, 2:])

    #for plot 1 set the style, axes etc + specify the data
    sns.lineplot(x='Total sample size (N)', y='Power (1-β)',
        style='Significance level (α)',
        markers=True, dashes=False,
        ax=ax1, data=data_beta)

    # plot the data for plot 1, and set it’s x axis ticks to be every 20 units
    ax1.axhline(0.8, 0, data_beta['Total sample size (N)'].max())
    ax1.xaxis.set_major_locator(plt.MultipleLocator(20))

    # specify plot 2 parameters and plot
    sns.distplot(b1_dtx, label="B1 within distances", color="red", ax=ax2)
    ax2.axvline(mean(b1_dtx), 0, 6, color="red")
    sns.distplot(bother_dtx, label="B2-3 within distances", color="skyblue", ax=ax2)
    ax2.axvline(mean(bother_dtx), 0, 6, color="skyblue")
    ax2.xaxis.set_major_locator(plt.MultipleLocator(.1))
    plt.legend()

    fig.savefig('figure2.pdf')

You have now replicated the two figures in the Casals-Pascual et al 2020 paper, and should be able to repurpose this code to use for other data relevant to your own study.

R studio workflow
~~~~~~~~~~~~~~~~~

Set up environment
^^^^^^^^^^^^^^^^^^

In R-studio create a new project and copy the (equivalent) following files to it:

* metadata.txt
* alpha-diversity.tsv
* alpha_diversity.qza
* distance_matrix.qza
* distance-matrix.tsv

If you are using windows, and have the windows R-studio, the files can be copied from the linux subshell using ``cp <file.name> /mnt/c/Users/<your username>/<rest\ of\ path\ with\ back-slashes\ to\ escape\ spaces>/`` (this assumes you are in the directory containing the files, if not add the path to the file before the file name). Create a new script and set up your R environment:

.. code-block:: r

    # IBD example

    ##get packages
    if (!requireNamespace("installr", quietly = TRUE)){install.packages("installr")}
    library("installr")
    if (!requireNamespace("devtools", quietly = TRUE)){install.packages("devtools")}
    library(devtools)
    if (!requireNamespace("qiime2R", quietly = TRUE )) {devtools::install_github("jbisanz/qiime2R")}
    library(qiime2R)
    if(!requireNamespace("stats", quietly = TRUE)){install.packages("stats")}
    library("stats")
    if(!requireNamespace("ggplot2", quietly = TRUE)){install.packages("ggplot2")}
    library("ggplot2")
    if(requireNamespace("gridExtra", quietly = TRUE)){install.packages("gridExtra")}
    library("gridExtra")
    

Not all the above steps may be necessary, but do remember to load the libraries, even if they are already installed. After this is completed we can import the data and process it. We will use Qiime2R [2]_ to import the data into formats R can handle, then filter it into appropriate groups.

Import and process data
^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: r

    ## Import and prepare data
    ### metadata
    metadata <- read.table("metadata.txt", sep="\t", header = TRUE)

    ###Load alpha diversity artifact
    alpha <- read_qza("alpha_diversity.qza")
    metadata <- merge.data.frame(metadata, alpha$data, by.x = 'sample_name', by.y = 0 )
    metadata <- metadata[!is.na(metadata$faith_pd),]

    ####Make variables for each group
    b1 <- metadata[(metadata[ ,'cd_behavior'] == 'Non-stricturing, non-penetrating (B1)'), ]
    bother <- metadata[(metadata$cd_behavior != 'Non-stricturing, non-penetrating (B1)' & metadata$cd_behavior != 'not applicable'), ]

    ###Load beta diversity/distance matrix artifact
    beta <- read_qza("distance_matrix.qza")
    dtx <- as.matrix(beta$data)

    ####Make variables for each group
    b1_dtx <- as.vector(t(dtx[(metadata[(metadata$cd_behavior == 'Non-stricturing, non-penetrating (B1)'),"sample_name"]), ]))
    bother_dtx <- as.vector(t(dtx[(metadata[(metadata$cd_behavior != 'Non-stricturing, non-penetrating (B1)' & metadata$cd_behavior != 'not applicable'), "sample_name"]), ]))

The artifacts have now been loaded into R and the data separated by group. We can now perform the necessary processing to obtain data for plotting. Note that we do not use R’s sd function directly because it calculates sample standard deviation and we require population standard deviation when working with alpha diversity statistics (which consider the sample as the population).

.. code-block:: r

    ## Process data
    ### alpha
    n <- length(b1$faith_pd)

    # R's standard sd function uses denominator n -1 i.e. calculates sample standard deviation, therefore we do not use sd directly.

    sd1 <- sqrt((n-1)/n) * sd(b1$faith_pd) 
    sd2 <- sqrt((n-1)/n) * sd(bother$faith_pd)
    sd12 <- mean(sd1, sd2)

    #### power t-test has the parameters n, delta, sd, sig.level and power. Four must be specified and the final is then calculated

    #significance level
    sig <- 0.05

    #create and empty data frame
    data_alpha <- data.frame(NULL)
    
    #calculate the values for plotting and place them in a data frame
    #iterate through sample sizes
    for(obs in seq(from = 10, to = 155, by = 5)) {
    	#for each sample size iterate through different effect sizes
        for(diff in 2:4){
            x <- power.t.test(n=obs,
                                delta=diff,
                                sd=sd12,
                                sig.level=sig,
                                power=NULL,
                                alternative="two.sided")
    #place the calculated values into a dataframe
        xrow <- c(x$sig.level, x$power, (x$n * 2), x$delta, (x$delta / x$sd))
        data_alpha <- rbind(data_alpha, xrow)
        }
    }

    # Set column names of the created dataframe
    colnames(data_alpha) <- c('Significance level (α)', 'Power (1-β)', 'Total sample size (N)', 'Difference', 'Effect size')

    ###beta

    u2u1 <- abs(mean(b1_dtx) - mean(bother_dtx))
    
    # note here we do use sd() because now we do want to calculate the sample standard deviation
    sd_dtx <- mean(sd(b1_dtx), sd(bother_dtx)) 

    #create empty dataframe
    data_beta <- data.frame(NULL)

    #iterate through samples sizes
    for(obs in seq(from=10, to=155, by=5)){
    #for each sample size iterate through different significance levels
        for(sig in c(0.001, 0.01, 0.05, 0.1)){
            #calculate power for the set variable
            x <- power.t.test(n=obs,
                            delta=u2u1,
                            sd=sd_dtx,
                            sig.level=sig,
                            power=NULL,
                            type="two.sample",
                            alternative="two.sided")
            #place the calculated data into a data frame
            xrow <- c(x$sig.level, x$power, (x$n * 2), x$delta, (x$delta / x$sd))
            data_beta <- rbind(data_beta, xrow)
            }
    }

    #Name the columns of the data frame appropriately
    colnames(data_beta) <- c('Significance level (α)', 'Power (1-β)', 'Total sample size (N)', 'Difference', 'Effect size')

If you have also looked at the python version of this code you may notice that here we do not use effect size directly, rather the function accepts both the difference and the standard deviation and calculates the effect size itself.

Make Plots
^^^^^^^^^^

R’s default plotting function is perfectly adequate for exploratory analysis, but for publication level figures the package ggplot is more appropriate. ggplot uses 'layers', first the plot background is made, then points, lines, annotations etc can be added to it.

.. code-block:: r
    
    ## Make plots
    ### Figure 1
    p <- ggplot(data_alpha, aes(x =as.numeric(`Total sample size (N)`), y =as.numeric(`Power (1-ß)`), group = as.factor(`Difference`), color = as.factor(`Difference`), shape = as.factor(`Difference`))) +
        geom_hline(yintercept = 0.8, color = "blue", size = 0.5) +
        geom_point() +
        geom_line() +
        scale_x_continuous(breaks = seq(0, 320, by = 20)) +
        scale_y_continuous(breaks = seq(0, 1, by = 0.1)) +
        labs(x = "Total sample size (N)", y = "Power (1-ß)") +
        scale_shape_discrete(name = 'Difference', breaks = c("2", "3", "4"), labels = c("2 (effect size 0.55)", "3 (effect size 0.82)", "4 (effect size 1.09)")) +
        scale_colour_discrete(name = 'Difference', breaks = c("2", "3", "4"), labels = c("2 (effect size 0.55)", "3 (effect size 0.82)", "4 (effect size 1.09)")) +
        theme(legend.position = "bottom")

        #save the figure
        jpeg('Figure_1.jpg', width = 1306, height = 579)
        p
        dev.off()

While this code contains the necessary command to save an image automatically, a better quality image can be saved by running the line ``p`` alone so that the plot is present in the Rstudio plot viewer, and then using *export* -> *export as png* -> optionally alter image size and or ratio -> *save*. The same is true for figure 2 below, but in this case run the line ``grid.arrange(p1, p2, layout_matrix = lay)`` alone.

.. code-block:: r

    ### Figure 2
    #### First create the two graphs
    p1 <- ggplot(data_beta, aes(x =as.numeric(`Total sample size (N)`), y =as.numeric(`Power (1-ß)`), group = as.factor(`Significance level (a)`), color = as.factor(`Significance level (a)`), shape = as.factor(`Significance level (a)`))) +
        geom_hline(yintercept = 0.8, color = "blue", size = 0.5) +
        geom_point() +
        geom_line() +
        scale_x_continuous(breaks = seq(0, 320, by = 20)) +
        scale_y_continuous(breaks = seq(0, 1, by = 0.1)) +
        labs(x = "Total sample size (N)", y = "Power (1-ß)") +
        scale_shape_discrete(name = 'Significance level (α)', breaks = c("0.001", "0.01", "0.05", "0.1"), labels = c("0.001", "0.01", "0.05", "0.1")) +
        scale_colour_discrete(name = 'Significance level (α)', breaks = c("0.001", "0.01", "0.05", "0.1"), labels = c("0.001", "0.01", "0.05", "0.1")) +
        theme(legend.position = "bottom")

    ####prepare data so ggplot can use it for a histogram
    mu_b1 <- mean(b1_dtx)
    label <- 'b1'
    b1_dtx <- cbind(b1_dtx, label)
    mu_bother <- mean(bother_dtx)
    label <- 'bother'
    bother_dtx <- cbind(bother_dtx, label)
    merged <- as.data.frame(rbind(b1_dtx, bother_dtx))
    colnames(merged) <- c('dtx', 'Sample')


    ####plot the histogram

    p2 <- ggplot(data = merged, aes(x = as.numeric(dtx), group = Sample, fill = Sample)) +
        geom_histogram(aes(y=..density.., color = Sample), alpha = 0.1, binwidth = 0.01) +
        geom_density(alpha = 0.4) +
        scale_x_continuous(name = '', breaks = seq(0,1,0.1), expand = c(0.1, 0.1)) +
        scale_y_continuous(breaks = c(0:20)) +
        geom_vline(xintercept = mu_b1, color = 'red', linetype = 'dashed', size = 0.8) +
        geom_vline(xintercept = mu_bother, color = 'blue', linetype = 'dashed', size = 0.8) +
        theme(legend.position = "bottom") +
        scale_color_discrete(name = '', breaks = c('b1', 'bother'), labels = c("B1 within distances", "B2-3 within distances")) +
        scale_fill_discrete(name = '', breaks = c('b1', 'bother'), labels = c("B1 within distances", "B2-3 within distances"))

    #specify layout
    lay <- cbind(matrix(1), matrix(1), matrix(2))

    #save figure
    jpeg('Figure_2.jpg', width = 1500, height = 579)
    grid.arrange(p1, p2, layout_matrix = lay)
    dev.off()
    
These figures will look slightly different to those in Casals-Pascual et al 2020 because they have been made in R but they are essentially the same, and this code can be modified to one’s own data if R is preferred.

Conclusion
~~~~~~~~~~

You should now have two figures essentially the same as those found in Casals-Pascual et al 2020 as well as having obtained the data to quantitatively decide an appropriate sample size for an experiment which will allow you obtain similar data. The generic paragraph recommended by their publication is as follows:

*Generic Sample Size Justification Paragraph for Grants or Articles
The sample size has been determined based on statistical power, effect size, time, and available resources requested in this grant. A total number of 110 patients is realistic and achievable enrollment in our clinical setting. The diversity of microbial communities is a good indicator of dysbiosis in patients with CD1, and we have selected Faith’s PD as a suitable metric to calculate alpha diversity. In a similar study, we observed that this metric shows an approximately normal distribution with mean 13.5 and standard deviation 3.45. Thus, to find a significant reduction of 2 units of Faith’s PD (effect size, Cohen’s D: 0.55) with an alpha value (type I error) of 5% and a statistical power (1  beta) of 80%, we will have to enroll 110 patients (55 with B1 phenotype and 55 with B2/B3 phenotype).*



Bibliography
~~~~~~~~~~~~

.. [1]  Casals-Pascual C, González A, Vázquez-Baeza Y, Song SJ, Jiang L, Knight R. 2020 Microbial Diversity in Clinical Microbiome Studies: Sample Size and Statistical Power Considerations. Gastroenterology 158, 15241528. (doi:10.1053/j.gastro.2019.11.305)

.. [2] 2018 Tutorial: Integrating QIIME2 and R for data visualization and analysis using qiime2R. QIIME 2 Forum. See https://forum.qiime2.org/t/tutorial-integrating-qiime2-and-r-for-data-visualization-and-analysis-using-qiime2r/4121



