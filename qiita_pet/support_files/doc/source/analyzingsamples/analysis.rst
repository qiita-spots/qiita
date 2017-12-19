Create New Analysis Page
========================
* **See Previous Analysis**
 * Shows past analysis done on your account, or shared with you.
* **Filter results by column data (Title, Abstract, PI, etc.)**: Searches for studies with the title/abstract/PI/etc. that you inputted
* **Filter study by Study Tags**: Searches for studies with the tag you searched for
* **Title**: Brings you to Study Information Page of that experiment
* **Green Expand for Analysis Button**: Reveals the studies done on this data that can be used for further analysis
 * **Add**: Adds data to be analyzed 
  * More than 1 can be done at once to do large meta-data analysis
* **Create New Analysis**: Creates the analysis using the data that has been added
 * **Analysis Name** (required): Name for the analysis that will be done
 * **Description** (optional): Description for the analysis that will be done
Single vs. Meta Analysis
------------------------------
* **Single analysis**: One study chosen to analyze 
* **Meta-analysis**: Multiple studies chosen to analyze
 * *You can only merge like data*

Processing Workflow Page: Commands
===================================
* **Commands for Deblurred or Closed-Reference Data**:
 * **Rarefy features**: Subsample frequencies from all samples without replacement so that the sum of frequencies in each sample is equal to the sampling-depth
  *  **BIOM table** (required): Feature table containing the samples for which features should be rarefied
  *  **Parameter set**: Parameters at which the rarefication is run
  *  **Sampling depth** (required): Total frequency that each sample should be rarefied to, samples where sum of frequencies is less than sampling depth will not be included in resulting table
  *  **Citation**: *Heck, K.L., Van Belle, G., Simberloff, D. (1975). “Explicit Calculation of the Rarefaction Diversity Measurement and the Determination of Sufficient Sample Size”. Ecology. 56(6): 1459-1461*
* **Commands from Rarefied Data**:
 * **Filter samples by metadata**: Filters samples from an OTU table on the basis of the number of observations in that sample, or on the basis of sample metadata
  * **BIOM table** (required): Feature table containing the samples for which features should be filtered
  * **Maximum feature frequency across samples** (optional): Maximum total frequency that a feature can have to be retained
  * **Maximum features per sample** (optional): Maximum number of features that a sample can have to be retained
  * **Minimum feature frequency across samples** (optional): Minimum total frequency that a feature must have to be retained
  * **Minimum features per sample** (optional): Minimum number of features that a sample can have to be retained
  * **SQLite WHERE-clause** (optional): Metadata group that is being filtered out
 * **Summarize Taxa**: Creates a bar plot of the taxa within the analysis
  * *Can only be performed with closed-reference data*
  * **BIOM table** (required): Feature table containing the samples to visualize at various taxonomic levels
 * **Calculate alpha diversity**: Measures the diversity within a sample
  * **BIOM table** (required): Feature table containing the samples for which alpha diversity should be computed
   * **Diversity metric** (required): Alpha diversity metric to be run
    * **Abundance-based Coverage Estimator (ACE) metric**: Calculates the ACE metric
     * Estimates species richness using a correction factor
     * **Citation**: *Chao, A. and Lee, S.M.. (1992). “Estimating the number of classes via sample coverage”. Journal of the American Statistical Association. (87): 210-217.*
    * **Berger-Parker Dominance Index**: Calculates Berger-Parker dominance index
     * Relative richness of the abundant species 
     * **Citation**: *Berger, W.H. and Parker, F.L. (1970). “Diversity of planktonic Foraminifera in deep sea sediments”. Science. (168): 1345-1347.*
    * **Brillouin’s index**: Calculates Brillouin’s index 
     * Measures the diversity of the species present
     * Use when randomness can’t be guaranteed
     * **Citation**: *Pielou, E. C. (1975). Ecological Diversity. New York, Wiley InterScience.*
    * **Chao1 confidence interval**: Calculates chao1 confidence interval
     * Confidence interval for richness estimator, Chao1
     * **Citation**: *Colwell, R.K., Mao, C.X., Chang, J. (2004). “Interpolating, extrapolating, and comparing incidence-based species accumulation curves.” Ecology. (85), 2717-2727.*
    * **Chao1 index**: Calculates Chao1 index
     * Estimates diversity from abundant data
     * Estimates number of rare taxa missed from undersampling 
     * **Citation**: *Chao, A. (1984). “Non-parametric estimation of the number of classes in a population”. Scandinavian Journal of Statistics (11): 265-270.*
    * **Dominance measure**: Calculates dominance measure
     * How equally the taxa are presented
    * **Effective Number of Species (ENS)/Probability of intra-or interspecific encounter (PIE) metric**: Calculates Effective Number of Species (ENS)/Probability of intra-or interspecific encounter (PIE) metric
     * Shows how absolute amount of species, relative abundances of species, and their intraspecific clustering affect differences in biodiversity among communities
     * **Citation**: *Chase, J.M., and Knight, R. (2013). “Scale-dependent effect sizes of ecological drivers on biodiversity: why standardised sampling is not enough”. Ecology Letters (16): 17-26.*
    * **Esty confidence interval**: Calculates Esty’s confidence interval
     * Confidence interval for how many singletons in total individuals
     * **Citation**: *Esty, W. W. (1983). “A normal limit law for a nonparametric estimator of the coverage of a random sample”. Ann Statist. (11): 905-912.*
    * **Faith’s phylogenetic diversity**: Calculates faith’s phylogenetic diversity 
     * Measures of biodiversity that incorporates phylogenetic difference between species
     * Sum of length of branches
     * **Citation**: *Faith. D.P. (1992). “Conservation evaluation and phylogenetic diversity”. Biological Conservation. (61) 1-10.*
    * **Fisher’s index**: Calculates Fisher’s index
     * Relationship between the number of species and the abundance of each species
     * **Citation**: *Fisher, R.A., Corbet, A.S. and Williams, C.B. (1943). “The relation between the number of species and the number of individuals in a random sample of an animal population”. Journal of Animal Ecology. (12): 42-58.*
    * **Gini index**: Calculates Gini index
     * Measures species abundance
     * Assumes that the sampling is accurate and that additional data would fall on linear gradients between the values of the given data
     * **Citation**: *Gini, C. (1912). “Variability and Mutability”. C. Cuppini, Bologna. 156.*
    * **Good’s coverage of counts**: Calculates Good’s coverage of counts.
     * Estimates the percent of an entire species that is represented in a sample
     * **Citation**: *Good. I.J (1953) “The populations frequency of Species and the Estimation of Populations Parameters”. Biometrika. 40(3/4):237-264*
    * **Heip’s evenness measure**: Calculates Heip’s evenness measure.
     * Removes dependency on species number 
     * **Citation**: *Heip, C. (1974). “A new index measuring evenness”. J. Mar. Biol. Ass. UK. (54): 555-557.*
    * **Kempton-Taylor Q index**: Calculates Kempton-Taylor Q index
     * Measured diversity based off the distributions of species 
     * Makes abundance curve based off all species and IQR is used to measure diversity
     * **Citation**: *Kempton, R.A. and Taylor, L.R. (1976). “Models and statistics for species diversity”. Nature (262): 818-820.*
    * **Lladser’s confidence interval**: Calculates Lladser’s confidence interval
     * Single confidence interval of the conditional uncovered probability
     * **Citation**: *Lladser, M.E., Gouet, R., Reeder, R. (2011). “Extrapolation of Urn Models via Poissonization: Accurate Measurements of the Microbial Unknown”. PLoS.*
    * **Lladser’s point estimate**: Calculates Lladser’ point estimate
     * Estimates how much of the environment contains unsampled taxa
     * Best estimate on a complete sample
     * **Citation**: *Lladser, M.E., Gouet, R., Reeder, J. (2011). “Extrapolation of Urn Models via Poissonization: Accurate Measurements of the Microbial Unknown”. PLoS.*
    * **Margalef’s richness index**: Calculates Margalef’s richness index
     * Measures species richness in a given area or community
     * **Citation**: *Magurran, A.E. (2004). “Measuring biological diversity”. Blackwell. 76-77.*
    * **Mcintosh dominance index D**: Calculates McIntosh dominance index D
     * Affected by the variation in dominant taxa and less affected by the variation in less abundant or rare taxa
     * **Citation**: *McIntosh, R.P. (1967). “An index of diversity and the relation of certain concepts to diversity”. Ecology (48): 392-404.*
    * **Mcintosh evenness index E**: Calculates McIntosh’s evenness measure E
     * How evenly abundant taxa are
     * **Citation**: *Heip, C. (1974). “A new index measuring evenness”. J. Mar. Biol. Ass. UK. (54) 555-557.*
    * **Menhinick’s richness index**: Calculates Menhinick’s richness index
     * The ratio of the number of taxa to the square root of the sample size
     * **Citation**: *Magurran, A.E. (2004). “Measuring biological diversity”. Blackwell. 76-77.*
    * **Michaelis-Menten fit to rarefaction curve of observed OTUs**: Calculates Michaelis-Menten fit to rarefaction curve of observed OTUs.
     * Estimated richness of species pools
     * **Citation**: *Raaijmakers, J.G.W. (1987). “Statistical analysis of the Michaelis-Menten equation”. Biometrics. (43): 793-803.*
    * **Number of distinct features**: Calculates number of distinct OTUs
     * **Citation**: *DeSantis, T.Z., Hugenholtz, P., Larsen, N., Rojas, M., Brodie, E.L., Keller, K. Huber, T., Davis, D., Hu, P., Andersen, G.L. (2006). “Greengenes, a Chimera-Checked 16S rRNA Gene Database and Workbench Compatible with ARB”. Applied and Environmental Microbiology (72): 5069–5072.*
    * **Number of double occurrences**: Calculates number of double occurrence OTUs (doubletons)
     * OTUs that only occur twice
    * **Number of observed features, including singles and doubles**: Calculates number of observed OTUs, singles, and doubles.
     * **Citation**: *DeSantis, T.Z., Hugenholtz, P., Larsen, N., Rojas, M., Brodie, E.L., Keller, K. Huber, T., Davis, D., Hu, P., Andersen, G.L. (2006). “Greengenes, a Chimera-Checked 16S rRNA Gene Database and Workbench Compatible with ARB”. Applied and Environmental Microbiology. 72 (7): 5069–5072.*
    * **Singles**: Calculates number of single occurrence OTUs (singletons)
     * OTUs that appear only once in a given sample
    * **Pielou’s evenness**: Calculates Pielou’s eveness
     * Measure of relative evenness of species richness
     * **Citation**: *Pielou, E. (1966). “The measurement of diversity in different types of biological collections”. J. Theor. Biol. (13): 131-144.*
    * **Robbins’ estimator**: Calculates Robbins’ estimator
     * Probability of unobserved outcomes
     * **Citation**: *Robbins, H.E. (1968). “Estimating the Total Probability of the unobserved outcomes of an experiment”. Ann Math. Statist. 39(1): 256-257.*
    * **Shannon’s index**: Calculates Shannon’s index
     * Calculates richness and diversity using a natural logarithm 
     * Accounts for both abundance and evenness of the taxa present
     * **Citation**: *Shannon, C.E. and Weaver, W. (1949). “The mathematical theory of communication”. University of Illonois Press, Champaign, Illonois.*
    * **Simpson evenness measure E**: Calculates Simpson’s evenness measure E.
     * Diversity that account for the number of organisms and number of species 
     * **Citation**: *Simpson, E.H. (1949). “Measurement of Diversity”. Nature. (163): 688*
    * **Simpson’s index**: Calculates Simpson’s index
     * Measures the relative abundance of the different species making up the sample richness
     * **Citation**: *Simpson, E.H. (1949). “Measurement of diversity". Nature. (163): 688.*
    * **Strong’s dominance index (Dw)**: Calculates Strong’s dominance index 
     * Measures species abundance unevenness
     * **Citation**: *Strong, W.L. (2002). “Assessing species abundance uneveness within and between plant communities”. Community Ecology (3): 237-246.*
   * **Phylogenetic tree** (required for certain alpha diversities, ie. Faith PD): Phylogenetic tree to be used with alpha analyses (only include when necessary ie. Faith PD)
    * Currently only tree that can be used is the GreenGenes 97% OTU based phylogenetic tree
   * **Alpha Diversity Citation**: Whittaker, R.H. (1960). “Vegetation of the Siskiyou Mountains, Oregon and California”. Ecological Monographs. (30)” 279–338. 
  * **Calculate beta diversity**: Measured the diversity between samples
   * **BIOM table** (required): Feature table containing the samples for which beta diversity should be computed
   * **Adjust variance** (phylogenetic only): Performs variance adjustment
    * Weighs distances based on the proportion of the relative abundance represented between the samples at a given node under evaluation
    * **Citatoin**: *Chang, Q., Luan, Y., & Sun, F. (2011). “Variance adjusted weighted UniFrac: a powerful beta diversity measure for comparing communities based on phylogeny”. BMC Bioinformatics.12(1): 118.*
   * **Alpha value** (Generalized UniFrac only): Value of alpha controls importance of sample proportions. 1.0 is weighted normalized UniFrac. 0.0 is close to unweighted UniFrac, but only if the sample  are dichotomized.
   * **Bypass tips** (phylogenetic only): In a bifurcating tree, the tips make up about 50% of the nodes in a tree. By ignoring them, specificity can be traded for reduced compute time. This has the effect of collapsing the phylogeny, and is analogous (in concept) to moving from 99% to 97% OTUs
   * **Diversity metric** (required): Beta diversity metric to be run
    * **Bray-Curtis dissimilarity**: Calculates Bray–Curtis dissimilarity
     * Fraction of overabundant counts
     * **Citation**: *Sorenson, T. (1948) "A method of establishing groups of equal amplitude in plant sociology based on similarity of species content." Kongelige Danske Videnskabernes Selskab 5.1-34: 4-7.*
    * **Canberra distance**: Calculates Canberra distance
     * Overabundance on a feature by feature basis
     * **Citation**: *Lance, Godfrey L.N. and Williams, W.T. (1967). "A general theory of classificatory sorting strategies II. Clustering systems." The computer journal 10 (3):271-277.*
    * **Chebyshev distance**: Calculates Chebyshev distance
     * Maximum distance between two samples
     * **Citation**: *Cantrell, C.D. (2000). “Modern Mathematical Methods for Physicists and Engineers”. Cambridge University Press.*
    * **City-block distance**:  Calculates City-block distance
     * Similar to the Euclidean distance but the effect of a large difference in a single dimension is reduced
     * **Citation**: *Paul, E.B. (2006). “Manhattan distance". Dictionary of Algorithms and Data Structures*
    * **Correlation coefficient**: Measures Correlation coefficient
     * Measure of strength and direction of linear relationship between samples
     * **Citation**: *Galton, F. (1877). "Typical laws of heredity". Nature. 15 (388): 492–495.*
    * **Cosine Similarity**: Measures Cosine similarity
     * Ratio of the amount of common species in a sample to the mean of the two samples
     * **Citation**: *Ochiai, A. (1957). “Zoogeographical Studies on the Soleoid Fishes Found in Japan and its Neighhouring Regions-II”. Nippon Suisan Gakkaishi. 22(9): 526-530.*
    * **Dice measures**: Calculates Dice measure
     * Statistic used for comparing the similarity of two samples
     * Only counts true positives once
     * **Citation**: *Dice, Lee R. (1945). "Measures of the Amount of Ecologic Association Between Species". Ecology. 26 (3): 297–302.*
    * **Euclidean distance**: Measures Euclidean distance
     * Species-by-species distance matrix
     * **Citation**: *Legendre, P. and Caceres, M. (2013). “Beta diversity as the variance of community data: dissimilarity coefficients and partitioning.” Ecology Letters. 16(8): 951-963.*
    * **Generalized Unifrac**: Measures Generalized UniFrac
     * Detects a wider range of biological changes compared to unweighted and weighted UniFrac
     * **Citation**: *Chen, F., Bittinger, K., Charlson, E.S., Hoffmann, C., Lewis, J., Wu, G. D., Collman, R.G., Bushman, R.D., Li,H. (2012). “Associating microbiome composition with environmental covariates using generalized UniFrac distances.” Bioinformatics. 28 (16): 2106-2113.*
    * **Hamming distance**: Measures Hamming distance
     * Minimum number of substitutions required to change one group to the other
     * **Citation**: *Hamming, R.W. (1950) “Error Detecting and Error Connecting Codes”. The Bell System Technical Journal. (29): 147-160.*
    * **Jaccard similarity index**: Calculates Jaccard similarity index
     * Fraction of unique features, regardless of abundance
     * **Citation**: *Jaccard, P. (1908). “Nouvellesrecherches sur la distribution florale.” Bull. Soc. V and. Sci. Nat., (44):223-270.*
    * **Kulczynski dissimilarity index**: Measures Kulczynski dissimilarity index
     * Describes the dissimilarity between two samples
     * **Citation**: *Kulcynski, S. (1927). “Die Pflanzenassoziationen der Pieninen. Bulletin International de l’Academie Polonaise des Sciences et des Lettres”. Classe des Sciences Mathematiques et Naturelles. 57-203.*
    * **Mahalanobis distance**: Calculates Mahalanobis distance
     * How many standard deviations one sample is away from the mean
     * Unitless and scale-invariant
     * Takes into account the correlations of the data set
     * **Citation**: *Mahalanobis, Chandra, P. (1936). "On the generalised distance in statistics". Proceedings of the National Institute of Sciences of India. 2 (1): 49–55.*
    * **Matching components**: Measures Matching components
     * Compares indices under all possible situations
     * **Citation**: *Janson, S., and Vegelius, J. (1981). “Measures of ecological association”. Oecologia. (49): 371–376.*
    * **Rogers-tanimoto distance**: Measures Rogers-Tanimoto distance
     * Allows the possibility of two samples, which are quite different from each other, to both be similar to a third
     * **Citation**: *Tanimoto, T. (1958). "An Elementary Mathematical theory of Classification and Prediction". New York: Internal IBM Technical Report.*
    * **Russel-Rao coefficient**: Calculates Russell-Rao coefficients
     * Equal weight is given to matches and non-matches
     * **Citation**: *Russell, P.F. and Rao, T.R. (1940). “On habitat and association of species of anopheline larvae in south-eastern Madras”. J. Malaria Inst. India. (3): 153-178.*
    * **Sokal-Michener coefficient**: Measures Sokal-Michener coefficient
     * Proportion of matches between samples
     * **Citation**: *Sokal, R.R. and Michener, C.D. (1958). “A statistical method for evaluating systematic relationships”. Univ. Kans. Sci. Bull. (38) 1409-1438.*
    * **Sokal-Sneath Index**: Calculates Sokal-Sneath index
     * Measure of species turnover
     * **Citation**: *Sokal, R.R. and Sneath, P.H.A. (1963). “Principles of Numerical Taxonomy”. W. H. Freeman, San Francisco, California.*
    * **Species-by-species Euclidean**: Measures Species-by-species Euclidean
     * Standardized Euclidean distance between two groups
     * Each coordinate difference between observations is scaled by dividing by the corresponding element of the standard deviation
     * **Citation**: *Legendre, P. and Caceres, M. (2013). “Beta diversity as the variance of community data: dissimilarity coefficients and partitioning.” Ecology Letters. 16(8): 951-963.*
    * **Squared Euclidean**: Measures squared Euclidean distance
     * Place progressively greater weight on samples that are farther apart
     * **Citation**: *Legendre, P. and Caceres, M. (2013). “Beta diversity as the variance of community data: dissimilarity coefficients and partitioning.” Ecology Letters. 16(8): 951-963.*
    * **Unweighted unifrac**: Measures unweighted UniFrac
     * Measures the fraction of unique branch length
     * **Citation**: *Lozupone, C. and Knight, R. (2005). "UniFrac: a new phylogenetic method for comparing microbial communities." Applied and environmental microbiology 71 (12): 8228-8235.*
    * **Weighted Minkowski metric**: Measures Weighted Minkowski metric
     * Allows the use of the k-means-type paradigm to cluster large data sets
     * **Citation**: *Chan, Y., Ching, W.K., Ng, M.K., Huang, J.Z. (2004). “An optimization algorithm for clustering using weighted dissimilarity measures”. Pattern Recognition. 37(5): 943-952.*
    * **Weighted normalized UniFrac**: Measures Weighted normalized UniFrac
     * Takes into account abundance
     * Normalization adjusts for varying root-to-tip distances.
    * **Citation**: *Lozupone, C. A., Hamady, M., Kelley, S. T., Knight, R. (2007). "Quantitative and qualitative beta diversity measures lead to different insights into factors that structure microbial communities". Applied and Environmental Microbiology. 73(5): 1576–85.*
   * **Weighted unnormalized UniFrac**: Measures Weighted unnormalized UniFrac
    * Takes into account abundance
    * *Doesn't correct for unequal sampling effort or different evolutionary rates between taxa*
    * **Citation**: *Lozupone, C. A., Hamady, M., Kelley, S. T., Knight, R. (2007). "Quantitative and qualitative beta diversity measures lead to different insights into factors that structure microbial communities". Applied and Environmental Microbiology. 73(5): 1576–85.*
   * **Yule index**: Measures Yule index
    * Measures biodiversity
    * Determined by the diversity of species and the proportions between the abundance of those species.
    * **Citation**: *Fisher, R.A., Corbert, A.S., Williams, C.B. (1943). “The Relationship Between the Number of Species and the Number of Individuals in a Random Sample of an Animal Population”. J. Animal Ecol. (12): 42-58.*
  * **Number of jobs**: Number of workers to use
  * **Phylogenetic tree** (required for some beta diversities, ie. UniFrac): Phylogenetic tree to be used with beta analyses (only include when necessary ie. UniFrac)
   * Currently only tree that can be used is the GreenGenes 97% OTU based phylogenetic tree
  * **Citation**: *Whittaker, R.H. (1960). “Vegetation of the Siskiyou Mountains, Oregon and California”. Ecological Monographs. (30)” 279–338.*
* **Commands from Alpha Diversity Data**
 * **Alpha Correlation**: Determines if the numeric sample metadata category is correlated with alpha diversity
  * **Correlation Method** (required): Correction test being applied
   * **Spearman**: Measures if there is a linear relationship between 2 variables
    * **Citation**: *Spearman, C. (1904). "The proof and measurement of association between two things". American Journal of Psychology. (15): 72–101.*
   * **Pearson**: Measures how strong the linear relationship is between 2 variables
    * **Citation**: *Pearson, K. (1895). "Notes on regression and inheritance in the case of two parents". Proceedings of the Royal Society of London. (58): 240–242.*
  * **Alpha Vectors** (required): Vector of alpha diversity values by sample
  * **Alpha Correlation Citation**: *Ronbach, L.J. (1951). "Coefficient alpha and the internal structure of tests". Psychometrika. 16 (3): 297–334.*
* **Commands from Beta Diversity Data**
 * **Perform Principal Coordinate Analysis** (PCoA): Visualizes the similarities and differences between samples using Emperor Plots
  * **Distance matrix** (required): Distance matrix on which the PCoA should be computed
  * **PCoA Plot Citation**: *Pearson, K. (1901). "On Lines and Planes of Closest Fit to Systems of Points in Space" Philosophical Magazine. 2 (11): 559–572.*
  * **Emperor Plot Citation**: *Vazquez-Baeza, Y., Pirrung, M., Gonzalez, A., Knight, R. (2013). “Emperor: A tool for visualizing high-throughput microbial community data”. Gigascience 2(1):16.*
 * **Beta Group Significance**: Determines whether groups of samples are significantly different from one another using a permutation-based statistical test
  * **Distance matrix** (required): Matrix of distances between pairs of samples
  * **Comparison Type** (required): Perform or not perform pairwise tests between all pairs of groups in addition to the test across all groups
  * **Metadata category** (required): Category from metadata file or artifact viewable as metadata
  * **Method** (required): Correlation test being applied
   * **Anosim**:  Describes the strength and significance that a category has in determining the distances between points and can accept either categorical or continuous variables in the metadata mapping file
    * **Citation**: *Clarke, K.R. (1993). "Non-parametric multivariate analyses of changes in community structure". Austral Ecology. 18 (1): 117–143.*
   * **Permanova**: Describes the strength and significance that a category has in determining the distances between points and can accept categorical variables
    * **Citation**: *Anderson, M.J. (2001). "A new method for non-parametric multivariate analysis of variance". Austral Ecology. 26 (1): 32–46*
  * **Number of permutations** (required): Number of permutations to be run when computing p-values 
 * **Beta Correlation**: Identifies a correlation between the distance matrix and a numeric sample metadata category
  * **Distance-matrix** (required): Matrix of distances between pairs of samples
  * **Correlation method** (required): Correlation test being applied
   * **Spearman**: Measures if there is a linear relationship between 2 variables
    * **Citation**: *Spearman, C. (1904). "The proof and measurement of association between two things". American Journal of Psychology. (15): 72–101.*
   * **Pearson**: Measures how strong the linear relationship is between 2 variables
    * **Citation**: *Pearson, K. (1895). "Notes on regression and inheritance in the case of two parents". Proceedings of the Royal Society of London. (58): 240–242.*
  * **Metadata-category** (required): Category from metadata file or artifact viewable as metadata
  * **Number of permutations** (required): Number of permutations to be run when computing p-values
Files Network Page: Results
=================================
* **Taxa Bar Plot**
 * **Taxonomic Level**: How specific the taxa will be displayed 
  * 1- Kingdom, 2- Phylum, 3- Class, 4- Order, 5- Genus, 6- Species, 7- Subspecies
 * **Color Palette**: Changes the coloring of your taxa bar plot
  * **Discrete**: Each taxon is a different color
 * **Continuous**: Each taxon is a different shade of one color
 * **Sort Sample By**: Sorts data by sample metadata or taxonomic abundance and either by ascending or descending order
* **Alpha Diversity Results** 
 * **Boxplot**: Shows how different measures of alpha diversity correlate with different metadata categories
 * **Category**: Choose the metadata category you would like to analyze
 * **Kruskal-Wallis**: Result of Kruskal-Wallis tests
  * Says if differences are statistically significant
  * **Citation**: *Kruskal, W.H. and Wallis, W.A. (1952). "Use of ranks in one-criterion variance analysis". Journal of the American Statistical Association. 47 (260): 583–621.*
* **Alpha Correlation**:
 * **Boxplot**: Shows how different measures of alpha diversity correlate with different metadata categories
 * Gives the Spearman or Pearson result (rho and p-value)
* **Beta Diversity Result**:
 * **Distance Matrix**: Dissimilarity value for each pairwise comparison
* **PCoA Result**:
 * **Emperor Plot**: Visualization of similarities/dissimilarities between samples
  * **Color Category**: Groups each sample by the given category chosen by a given color
  * **Colors**: Choose colors for each group
  * **Visibility** Allows for making certain samples invisible
   * *Does not remove them from the analysis*
    * Must perform filtering to do that
  * **Shape**: Groups each sample by the given category chosen by a given shape  
  * **Axis**: Change the position of the axis as well as the color of the graph
  * **Scale**: Change the size of a given category 
* **Beta Group Significance**:
 * **Boxplot**: Shows how different measures of beta diversity correlate with different metadata categories
 * Gives the Permanova or Anosim result (psuedo-F and p-value)
* **Beta Correlation**:
 * Gives the Spearman or Pearson result (rho and p-value)
  * **Spearman**: Measures if there is a linear relationship between 2 variables
   * **Citation**: *Spearman, C. (1904). "The proof and measurement of association between two things". American Journal of Psychology. (15): 72–101.*
  * **Pearson**: Measures how strong the linear relationship is between 2 variables
   * **Citation**: *Pearson, K. (1895). "Notes on regression and inheritance in the case of two parents". Proceedings of the Royal Society of London. (58): 240–242.*
 * Gives scatterplot of the distance matrix on the y and the variable being tested on the x-axis
