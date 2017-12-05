Processing Workflow Page: Commands
===================================
* **Commands for Deblurred or Closed-Reference Data**:
  * **Rarefy features**: Subsample frequencies from all samples without replacement so that the sum of frequencies in each sample is equal to the sampling-depth
   *  **BIOM table** (required): the feature table containing the samples for which features should be rarefied
   *  **Parameter set**: the parameters at which the rarefication is run
   *  **Sampling depth** (required): total frequency that each sample should be rarefied to, samples where sum of frequencies is less than sampling depth will not be included in resulting table
   *  *Citation*: Heck, K.L., Van Belle, G., Simberloff, D. (1975). “Explicit Calculatino of the Rarefaction Diversity Measurement and the Determination of Sufficient Sample Size”. Ecology. 56(6): 1459-1461.
•	Commands from Rarefied Data:
o	Filter samples by metadata: Filters samples from an OTU table on the basis of the number of observations in that sample, or on the basis of sample metadata
	BIOM table (required): the feature table containing the samples for which features should be filtered
	Maximum feature frequency across samples (optional): the maximum total frequency that a feature can have to be retained
	Maximum features per sample (optional): the maximum number of features that a sample can have to be retained
	Minimum feature frequency across samples (optional): the minimum total frequency that a feature must have to be retained
	Minimum features per sample (optional): the minimum number of features that a sample can have to be retained
	SQLite WHERE-clause (optional): The metadata group that is being filtered out
o	Summarize Taxa: Creates a bar plot of the taxa within the analysis
	Can only be performed with closed-reference data
	BIOM table (required): the feature table containing the samples to visualize at various taxonomic levels
