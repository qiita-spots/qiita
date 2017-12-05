Processing Workflow Page: Commands
===================================
* **Commands for Deblurred or Closed-Reference Data**:
  * **Rarefy features**: Subsample frequencies from all samples without replacement so that the sum of frequencies in each sample is equal to the sampling-depth
   *  **BIOM table** (required): the feature table containing the samples for which features should be rarefied
   *  **Parameter set**: the parameters at which the rarefication is run
   *  **Sampling depth** (required): total frequency that each sample should be rarefied to, samples where sum of frequencies is less than sampling depth will not be included in resulting table
   *  **Citation**: *Heck, K.L., Van Belle, G., Simberloff, D. (1975). “Explicit Calculatino of the Rarefaction Diversity Measurement and the Determination of Sufficient Sample Size”. Ecology. 56(6): 1459-1461*
* **Commands from Rarefied Data**:
 * **Filter samples by metadata**: Filters samples from an OTU table on the basis of the number of observations in that sample, or on the basis of sample metadata
  * **BIOM table** (required): the feature table containing the samples for which features should be filtered
  * **Maximum feature frequency across samples** (optional): the maximum total frequency that a feature can have to be retained
  * **Maximum features per sample** (optional): the maximum number of features that a sample can have to be retained
  * **Minimum feature frequency across samples** (optional): the minimum total frequency that a feature must have to be retained
  * **Minimum features per sample** (optional): the minimum number of features that a sample can have to be retained
  * **SQLite WHERE-clause** (optional): The metadata group that is being filtered out
 * **Summarize Taxa**: Creates a bar plot of the taxa within the analysis
  * *Can only be performed with closed-reference data*
  * **BIOM table** (required): the feature table containing the samples to visualize at various taxonomic levels
 * **Calculate alpha diversity**: Measures the diversity within a sample
  * **BIOM table** (required): the feature table containing the samples for which alpha diversity should be computed
   * **Diversity metric** (required): The alpha diversity metric to be run
    * **Abundance-based Coverage Estimator (ACE) metric**: Calculates the ACE metric
     * Inflates the number of rare taxa and inflates again the number of taxa with abundance 1.
     * Estimates species richness
     * **Citation**: *Chao, A. and Lee, S.M.. (1992). “Estimating the number of classes via sample coverage”. Journal of the American Statistical Association. (87): 210-217.*
    * **Berger-Parker Dominance Index**: Calculates Berger-Parker dominance index
     * Measure of the numerical importance of the most abundant species
     * **Citation**: *Berger, W.H. and F.L. Parker (1970). “Diversity of planktonic Foraminifera in deep sea sediments”. Science. (168): 1345-1347.*
    * **Brillouin’s index**: Calculates Brillouin’s index 
     * Measures the diversity of the species present
     * Use when randomness can’t be guaranteed
     * **Citation**: *Pielou E. C. (1969). “An introduction to mathematical ecology”. New York: Wiley.*
    * **Chao1 confidence interval**: Calculates chao1 confidence interval
     * Confidence interval for richness estimator, chao1
     * **Citation**: *Colwell, R. K., Mao, C. X., Chang, J. (2004). “Interpolating, extrapolating, and comparing incidence-based species accumulation curves.” Ecology. (85), 2717-2727.*
    * **Chao1 index**: Calculates chao1 index
     * Estimates diversity from abundant data
     * Assumes that the number of observations for taxa has a Poisson distribution
      * corrects for variance
     * **Citation**: *Chao, A. (1984). “Non-parametric estimation of the number of classes in a population”. Scandinavian Journal of Statistics (11): 265-270.*
    * **Dominance measure**: Calculates dominance measure
     * How equally the taxa are presented
    * **Effective Number of Species (ENS)/Probability of intra-or interspecific encounter (PIE) metric**: Calculates Effective Number of Species (ENS)/Probability of intra-or interspecific encounter (PIE) metric
     * shows how absolute amount of species, relative abundances of species, and their intraspecific aggregations affect differences in biodiversity among communities
     * **Citation**: *Chase, J.M., and Knight, R. (2013). “Scale-dependent effect sizes of ecological drivers on biodiversity: why standardised sampling is not enough”. Ecology Letters (16): 17-26.*
    * **Etsy confidence interval**: Calculates Esty’s confidence interval
     * Confidence interval for how many singletons in total individuals
     * **Citation**: *Esty, W. W. (1983). “A normal limit law for a nonparametric estimator of the coverage of a random sample”. Ann Statist. (11): 905-912.*
     * **Faith’s phylogenetic diversity**: Calculates faith’s phylogenetic diversity 
      * Measures of biodiversity that incorporates phylogenetic difference between species
      * Sum of length of branches
      * **Citation**: *Faith. D.P. (1992). “Conservation evaluation and phylogenetic diversity”. Biological Conservation. (61) 1-10.*
     * **Fisher’s index**: Calculates Fisher’s index
      * Relationship between the number of species and the number of individuals in those species.
      * **Citation**: *Fisher, R. A., Corbet, A. S. and Williams, C. B. (1943). “The relation between the number of species and the number of individuals in a random sample of an animal population”. Journal of Animal Ecology. (12): 42-58.*
     * **Gini index**: Calculates Gini index
      * Assumes that the sampling is accurate and that more features of data would fall on linear gradients between the values of this data.
      * Measures species abundance
      * **Citation**: *Gini, C. (1912). “Variability and Mutability”. C. Cuppini, Bologna. 156.*
     * **Good’s coverage of counts**: Calculates Good’s coverage of counts.
      * Estimating what percent of the entire species is exemplified in a sample
      * **Citation**: *Good. I.J (1953) “The populations frequency of Species and the Estimation of Populations Parameters”. Biometrika. 40(3/4):237-264*
     * **Heip’s evenness measure**: Calculates Heip’s evenness measure.
      * Removes dependency on species number 
      * **Citation**: *Heip, C. (1974). “A new index measuring evenness”. J. Mar. Biol. Ass. UK. (54): 555-557.*
     * **Kempton-Taylor Q index**: Calculates Kempton-Taylor Q index
      * Measured diversity based off the distributions of species 
      * Makes abundance curve based off all species and IQR of this curve is used to measure diversity
      * **Citation**: *Kempton, R. A. and Taylor, L. R. (1976). “Models and statistics for species diversity”. Nature (262): 818-820.*
     * **Lladser’s confidence interval**: Calculates Lladser’s confidence interval
      * Single confidence interval of the conditional uncovered probability
      * **Citation**: *Lladser, M. E., Gouet, R., Reeder, R. (2011). “Extrapolation of Urn Models via Poissonization: Accurate Measurements of the Microbial Unknown”. PLoS.*
     * **Lladser’s point estimate**: Calculates Lladser’ point estimate
      * Single point estimate of conditional uncovered probability
      * Estimate how much of the environment belongs to the unsampled taxa
      * Best estimate on a complete sample
      * **Citation**: *Lladser, M.E., Gouet, R., Reeder, J. (2011). “Extrapolation of Urn Models via Poissonization: Accurate Measurements of the Microbial Unknown”. PLoS.*
     * **Margalef’s richness index**: Calculates Margalef’s richness index
      * Measures species richness
      * **Citation**: *Magurran, A. E. (2004). “Measuring biological diversity”. Blackwell. 76-77.*
     * **Mcintosh dominance index D**: Calculates McIntosh dominance index D
      * Affected mostly by variation in dominant taxa and less affected by the variation in less abundant or rare taxa
      * **Citation**: *McIntosh, R. P. (1967). “An index of diversity and the relation of certain concepts to diversity”. Ecology (48): 392-404.*
      * **Mcintosh evenness index E**: Calculates McIntosh’s evenness measure E
       *How even taxa are in numbers
       * **Citation**: *Heip, C. (1974). “A new index measuring evenness”. J. Mar. Biol. Ass. UK. (54) 555-557.*
•	Menhinick’s richness index: Calculates Menhinick’s richness index
o	Species richness
o	Citation: Magurran, A. E. (2004). “Measuring biological diversity”. Blackwell. 76-77.
•	Michaelis-Menten fit to rarefaction curve of observed OTUs: Calculates Michaelis-Menten fit to rarefaction curve of observed OTUs.
o	Estimated richness of species pools
o	Citation: Raaijmakers, J. G. W. (1987). “Statistical analysis of the Michaelis-Menten equation”. Biometrics. (43): 793-803.
•	Number of distinct features: Calculates number of distinct OTUs
o	Citation: DeSantis, T. Z., Hugenholtz, P., Larsen, N., Rojas, M., Brodie, E. L., Keller, K. Huber, T., Davis, D., Hu, P., Andersen, G. L. (2006). “Greengenes, a Chimera-Checked 16S rRNA Gene Database and Workbench Compatible with ARB”. Applied and Environmental Microbiology (72): 5069–5072. 
•	Number of double occurrences: Calculates number of double occurrence OTUs (doubletons)
o	OTUs that only occur twice
•	Number of observed features, including singles and doubles: Calculates number of observed OTUs, singles, and doubles.
o	Observed OTUs Citation: DeSantis, T. Z., Hugenholtz, P., Larsen, N., Rojas, M., Brodie, E. L., Keller, K. Huber, T., Davis, D., Hu, P., Andersen, G. L. (2006). “Greengenes, a Chimera-Checked 16S rRNA Gene Database and Workbench Compatible with ARB”. Applied and Environmental Microbiology. 72 (7): 5069–5072.
•	Singles: Calculates number of single occurrence OTUs (singletons)
o	OTUs that appear only once in a given sample
•	Pielou’s evenness: Calculates Pielou’s eveness
o	Measure of relative evenness of species richness
o	Citation: Pielou, E. (1966). “The measurement of diversity in different types of biological collections”. J. Theor. Biol. (13): 131-144.
•	Robbins’ estimator: Calculates Robbins’ estimator
o	Probability of unobserved outcomes.
o	Citation: Robbins, H. E., (1968). “Estimating the Total Probability of the unobserved outcomes of an experiment”. Ann Math. Statist. 39(1): 256-257.
•	Shannon’s index: Calculates Shannon’s index
o	Accounts for both abundance and evenness of the species present
o	Citation: Shannon, C. E. and Weaver, W. (1949). “The mathematical theory of communication”. University of Illonois Press, Champaign, Illonois. 
•	Simpson evenness measure E: Calculates Simpson’s evenness measure E.
o	Measures the relative abundance of the different species making up the sample richness
o	Citation: Simpson, E.H. (1949). “Measurement of Diversity”. Nature. (163): 688
•	Simpson’s index: Calculates Simpson’s index
o	Diversity that account for the number of species present and the relative abundance of each species
o	Citation: Simpson, E. H. (1949). “Measurement of diversity". Nature. (163): 688. 
•	Strong’s dominance index (Dw): Calculates Strong’s dominance index 
o	Assesses species abundance unevenness or dominance concentration 
o	Citation: Strong, W. L., (2002). “Assessing species abundance uneveness within and between plant communities”. Community Ecology (3): 237-246.
	Phylogenetic tree (required for certain alpha diversities, ie. Faith PD): The phylogenetic tree to be used with alpha analyses (only include when necessary ie. Faith PD)
•	currently only tree that can be used is the GreenGenes 97% OTU based phylogenetic tree
	Alpha Diversity Citation: Whittaker, R. H. (1960). “Vegetation of the Siskiyou Mountains, Oregon and California”. Ecological Monographs. (30)” 279–338. 
