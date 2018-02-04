Glossary
=========

* **16S rRNA gene** :ref:`[38]<reference38>`

  * The 16s rRNA gene is a sequence of nucleotides present only in prokaryotic DNA. It codes for the protein structure of the 30th subunit in prokaryotic ribosomes. Its sequence remains relatively the same across all bacteria, because it has been highly conserved throughout evolutionary history. However, in microbiome research, we use the hypervariable V4 region of the gene as an identification marker for classifying bacteria. Genetically identifying organisms with techniques like 16s rRNA sequencing has only developed in the last twenty years and has begun to redefine the classification system of evolutionary identity for organisms like bacteria.
  * see also: Amplicon, Marker gene sequencing, DNA Sequencing, Shotgun Sequencing, qPCR, Hypervariable region, Illumina Sequencing

* **Actinobacteria** :ref:`[3]<reference3>`, :ref:`[5]<reference5>`, :ref:`[95]<reference95>`

  * Actinobacteria is a phylum of bacteria with high guanine to cytosine content and Gram positive cell walls. Many are aerobic with a few exceptions, and all actinobacteria are most famous for their fungi-like characteristics. Most produce mycelium and reproduce through sporulation like fungi; they also grow by extending their tips and branching their hyphae. Some examples are Bifidobacterium spp. and Streptomyces.
  * see also: HMP, Taxonomic Rank, Phylogeny, Taxonomy, Beta Diversity

* **Alpha Diversity** :ref:`[6]<reference6>`

  * Alpha diversity is a measurement of a bacterial community sample that determines the richness and evenness within that community. In other words, it measures how much of each bacterial species is in the community, and how equally distributed those bacterial organism counts are among each other in the sample. Higher alpha diversity, meaning higher richness and evenness, is associated with healthy ecosystems and communities because more functions can be performed and easier adaptations to the environment are possible. Statistical methods like Shannon and Pielou are used to calculate alpha diversity. For example, alpha diversity of the fauna at UCSD measures how much of each plant exists on campus and that count compares with the other plant numbers at UCSD.
  * see also: Beta Diversity, QIIME

* **Amplicon**

  * An amplicon is a DNA sequence produced from natural or artificial replication and can be used to identify individuals genetically. Amplification sequencing methods like polymerase chain reaction (PCR) and next-generation sequencing (also referred to as next-gen sequencing) help microbiome researchers profile microbial communities in cost-effective and time-efficient ways.
  * see also: Marker gene sequencing

* **Anaerobic microculture** :ref:`[23]<reference23>`

  * An anaerobic microculture is a method to grow different anaerobic bacterial communities (organisms that either can partly or must fully live in oxygen-free environments) in isolated plates. Scientists must replace the oxygen-rich atmosphere with a mixture of other gases like hydrogen, carbon dioxide and nitrogen. Then they dilute the solution of communities so much that there is a high probability that only one bacterial cell will be placed in the microculture plates to grow. Anaerobes are abundant in the gastrointestinal tract, and growing them in separate microcultures allows for scientists to sequence the whole genomes of a single species without it competing for resources with other organisms.
  * see also: Firmicutes, Gammaproteobacteria

* **Bacteroidetes** :ref:`[93]<reference93>`

  * Bacteroidetes is a phylum of Gram-negative bacteria that includes B. fragilis and Flavobacteria. They thrive in a wide variety of places like soil, sediment, and seawater, making them well-suited for the ecosystems present in the human gut. They specialize in breaking down organic matter like proteins and carbohydrates and are able to “gain energy from otherwise refractory carbohydrate sources”(1). Microbiome research is only just beginning to understand the metabolic and ecologic impact of Bacteroidetes in the human microbiome.
  * see also: HMP, Taxonomic Rank, Phylogeny, Taxonomy, Beta Diversity

* **Beta Diversity** :ref:`[9]<reference9>`

  * Beta diversity is a measurement that compares the species diversity between two community samples by identifying the differences and similarities in the species of those two communities. Lower beta diversity means there are lower numbers of shared organisms between the two communities; therefore, they are both environmentally different. For example, beta diversity of the fauna at UCSD measures the species of fauna on campus and compares them to the species at San Diego City College.
  * see also: Alpha Diversity, Principal Coordinates Analysis, Unifrac, QIIME

* **Biom format**

  * Biom format is a table that records the counts of OTUs for each bacteria in each different sample. A biom table can be created using QIIME and pandas, and it is an important component of distance matrix measurements.
  * see also: OTU, sOTU, Unifrac, QIIME, Principal Coordinates Analysis
  * GitHub Biocore|Biom Format: https://github.com/biocore/biom-format
  * Biom format official website: http://biom-format.org

* **DNA Sequencing** :ref:`[65]<reference65>`

  * DNA sequencing is the process of determining the order of nucleotides within a DNA molecule. Methods originate in Sanger sequencing, which uses PCR and gel electrophoresis to analyze the target DNA, but this approach is only able to do short length reads. Microbiome research has turned to next generation sequencing, which is an umbrella term for different techniques like whole genome sequencing and pyrosequencing, to analyze longer reads for a shorter amount of time at a relatively lower cost.
  * see also: Shotgun sequencing, Illumina sequencing, Amplicon, Marker Gene Sequencing

* **Demultiplexing** :ref:`[64]<reference64>`

  * Demultiplexing is a process in which the barcodes and primer sequences on a DNA fragment are removed so that the final result matches the amplified 16s rRNA gene. Barcodes are short DNA sequences unique to each sample. QIIME has demultiplexing tools that error correct the raw sequencing data back to the desired 16s rRNA gene.
  * see also: QIIME, 16s rRNA gene

* **Differential abundance and compositionality** :ref:`[47]<reference47>` , :ref:`[63]<reference63>` , :ref:`[96]<reference96>`

  * Differential abundance testing is a statistical testing method that determines the abundances of specific bacteria between two ecosystems. Compositionality is a statistical testing method that compares the proportions of species’ relative abundances in a sample, rather than the sample’s absolute abundances that differential abundance testing measures.
  * see also: Statistical Testing, Alpha Diversity

* **Firmicutes** :ref:`[54]<reference54>` , :ref:`[56]<reference56>` , :ref:`[93]<reference93>`

  * Firmicutes is a phylum of bacteria that includes species like Staphylococcus and Lactobacillus. In general, Firmicutes have Gram-positive cell walls, round cell shapes, and low guanine to cytosine content in their DNA. While some produce endospores to survive in extreme conditions, others reproduce through binary fission. They also have a wide variety of aerotolerance: some Firmicutes thrive in anaerobic environments, some in aerobic, and some in either. In microbiome research for example, higher proportions of Firmicutes in the intestinal human microbiome may be correlated with obesity (1).
  * see also: HMP, Taxonomic Rank, Phylogeny, Taxonomy, Beta Diversity

* **Gammaproteobacteria** :ref:`[100]<reference100>`

  * Gammaproteobacteria is one of the four classes of the phylum of Gram-negative proteobacteria. The phylum has a wide range of characteristics, from bacillus to cocci shaped, from chemoautotrophic to photoautotrophic, from aerobic to anaerobic, and from pathogenic to symbiotic relationships. “One feature alone, 16s rRNA sequence relationship, has been used to define the class”(1). Salmonella and E.coli are both gammaproteobacteria.
  * see also: HMP, Taxonomic Rank, Phylogeny, Taxonomy, Beta Diversity, Proteobacteria


* **HMP** :ref:`[67]<reference67>`, :ref:`[92]<reference92>`

  * The Human Microbiome Project (HMP) is “an interdisciplinary effort funded by the NIH Common Fund” to generate “resources that would enable the comprehensive characterization of the human microbiome and analysis of its role in human health and disease” (1). The HMP set five goals under a five-year-plan back in its 2008 inception: to develop a reference set of 3,000 isolate microbial genome sequences,” to produce research that estimates “the complexity of the microbial community at each body site,” “to determine the relationship between disease and changes in the human microbiome,” to invent new technologies for microbiome research analysis and establish a database resource center, and to examine the ethical, legal and social implications of studying and applying human microbiome research(1).
  * see also: OTU, Alpha Diversity, Beta Diversity, Metadata

* **Hypervariable region** :ref:`[101]<reference101>`

  * A hypervariable region is a location within a DNA molecule where the nucleotide sequence consists of highly repeated or substituted base pairs. The V4 region is one of nine hypervariable regions in the 16s rRNA gene of bacteria and has been used by microbiome researchers to classify species genotypically.
  * see also: 16s rRNA gene, Marker gene sequencing

* **Illumina sequencing** :ref:`[64]<reference64>` , :ref:`[39]<reference39>`

  * Illumina sequencing is a next-generation sequencing technique developed by the company Illumina that sequences tens of millions or billions of DNA fragments in a single sequencing run. With more DNA nucleotides comes a greater need for more analytical tools like QIIME in order to comprehend the longer reads.
  * see also: DNA sequencing, Shotgun sequencing, QIIME

* **Marker gene sequencing**  :ref:`[51]<reference51>` , :ref:`[81]<reference81>` , :ref:`[90]<reference90>`

  * Marker gene sequencing, also known as amplicon sequencing, is a technique that identifies a bacterial organism by its marker gene DNA sequence. In microbiome research, scientists use next-generation sequencing tools to amplify a sequence like the 16s rRNA gene, which is then used to infer the phenotypic makeup of that organism.
  * see also: Amplicon, 16s rRNA gene, Shotgun Sequencing, qPCR, HMP

* **Mass Spectrometry** :ref:`[40]<reference40>`

  * Mass spectrometry is a technique that ionizes atoms or molecules in a sample and measures their mass to charge ratios and relative abundances. The goal of mass spectrometry is to identify atoms or molecules by their masses. Microbiome researchers use mass spectrometry to identify the biochemical/metabolic exchange of microbes and their host environments.
  * see also: HMP

* **Metadata**

  * Metadata is data that provides information about multiple forms of data at once; for example, a clinical survey with a person’s personal information, their fecal sample raw sequences, and their psychological test scores are all linked as metadata for that one participant’s profile in a study. Gathering and organizing metadata is a fundamental step to data analysis because it allows for multivariable comparisons like how might one’s number of pets affect their gut microbiome?.
  * see also: HMP, Statistical Tests, Biom format
  * “Metadata Guide” Example: http://www.earthmicrobiome.org/protocols-and-standards/metadata-guide/

* **OTU** :ref:`[37]<reference37>`, :ref:`[66]<reference66>`

  * Operational taxonomic unit (OTU) is a term for the current organism being studied and is the newest form of classifying bacteria evolutionarily. It serves as an alternative to the common methods of taxonomy because it groups organisms together by 16s rRNA sequence rather than their phenotypic similarities. A 97% similarity match or higher is the commonly accepted threshold for relatedness.
  * see also: sOTU, 16s rRNA gene, Taxonomy

* **OTU picking** :ref:`[44]<reference44>` , :ref:`[78]<reference78>`

  * OTU picking is a high level strategy for defining OTU clusters, or groups of bacterial organisms, and there are currently three different methods for OTU picking: de novo, closed reference, and open reference. De novo lines up input sequences and clusters OTUs based on the user-specific percentage of similarity in the compared DNA sequences; closed reference aligns input sequences with predefined clusters from a reference database. “Finally, open-reference OTU picking combines the previous protocols. First, input sequences are clustered against a reference database in parallel in a closed-reference OTU picking process. However, rather than discarding sequences that fail to match the reference, these “failures” are clustered de novo in a serial process.”(1)
  * see also: OTU, sOTU, DNA sequencing

* **PCoA** :ref:`[9]<reference9>`

  * Principal Coordinates Analysis (PCoA) is a 3-D graphical approach to present the patterns of similarity and dissimilarity in a data set. It uses EMPeror as a program to visually graph a distance matrix like Unifrac into a 3-D form. It has three axes and each point on the graph represents a specific sample in the study set.
  * see also: Beta Diversity, QIIME, DNA sequencing

* **Phylogeny** :ref:`[33]<reference33>` , :ref:`[97]<reference97>`

  * Phylogeny is the study of the evolutionary histories of organisms. Phylogeny analyzes the genotypic and phenotypic characteristics to identify individuals and uses phylogenetic trees to visualize these relationships. Speciation, or where two groups of individuals developed differently into two new species, is represented by a branching stems on the diagram.
  * see also: Taxonomy, Taxonomic Rank, Unifrac

* **Proteobacteria** :ref:`[75]<reference75>`

  * Proteobacteria is a phylum of Gram-negative bacteria that share similar nucleotide sequences in their genomes. The phylum is divided into five classes, each with their own distinct capabilities from intracellular pathogens, to nitrogen-converters and sulfate reducers, to scavengers. Helicobacter, Campylobacter, E.coli, and Bordetella pertussis are all proteobacteria.
  * see also: HMP, Taxonomic Rank, Phylogeny, Taxonomy, Beta Diversity, Gammaproteobacteria

* **QIIME** :ref:`[64]<reference64>`

  * Qiime (pronounced chime) is an open-source bioinformatics pipeline that performs microbial analysis on raw DNA sequencing data in order to create comprehensible statistics and graphics for publication. It has been an ongoing project since its inception in 2010.
  * see also: Principal Coordinates Analysis, Illumina sequencing, Marker gene sequencing, Demultiplexing, Biom format, Unifrac, Alpha Diversity, Beta Diversity, DNA sequencing
  * QIIME 1.0 version website: http://qiime.org
  * QIIME 2 version website: https://docs.qiime2.org/2017.5/concepts/
  * “Official Repository for the QIIME 2 database”: https://github.com/qiime2/qiime2

* **Qiita**

  * Qitta (pronounced cheetah) is the open-source repository that enables scientists to rapidly analyze and store microbial ecology datasets. It is a bioinformatics resource that is built on the QIIME database, which is designed as a pipeline to generate publication-worthy presentations from raw sequencing data.
  * see also: QIIME, Biom format, Metadata
  * Access to QIITA source: https://github.com/biocore/qiita

* **qPCR** :ref:`[74]<reference74>`

  * qPCR, also known as quantitative PCR, is a sequencing technique that detects the quantities of amplicon DNA sequences as they are being amplified. It uses DNA-binding dyes or fluorescence-reporting probes to track the concentrations of adapters and DNA sequences being replicated. In microbiome research, it is important to know the concentrations of the amplicons for proceeding sequencing tools like next-generation sequencing.
  * see also: DNA sequencing, Marker gene sequencing, Illumina sequencing, Shotgun sequencing

* **Rarefraction**

  * Rarefraction is a technique that standardizes length of sequence reads and thereby the number of species measured in a sample. It is a necessary step in microbial bioinformatics because it narrows all the lengths of the raw DNA sequences to a set length; in doing so it allows for the quality of analyses to be refined and filtered and it accounts for statistical biases in the study’s procedures.
  * see also: QIIME, Principal Coordinates Analysis, OTU Picking, Demultiplexing

* **Shotgun sequencing** :ref:`[7]<reference7>` , :ref:`[23]<reference23>`

  * Shotgun sequencing is a DNA sequencing technique in which all the DNA molecules in a sample are sequenced. In this way, scientists can study not only the microbial communities, but also the functional genes that are present in a sample. Shotgun sequencing differs from whole genome sequencing (sometimes referred to as whole genome shotgun sequencing) because the latter analyzes the entire genome of only one isolated bacterial species in the sample. However, they use similar mechanisms in that both WGS and Shotgun sequencing uses enzymes to cut the DNA molecule into fragments that are more easily and efficiently amplified and analyzed.
  * see also: DNA sequencing, Marker gene sequencing, Illumina sequencing, qPCR

* **sOTU** :ref:`[10]<reference10>` , :ref:`[2]<reference2>`

  * Sub-operational taxonomic unit (sOTU) is an alternative approach to identify and classify bacterial species from raw DNA sequences at a higher resolution than the traditional OTUs. The 97% confidence rate for OTU clustering dismisses the 3% of the raw DNA sequences, so sOTUs identify and group single-nucleotide variation, allowing it to have a higher resolution for taxonomic identification. Deblur and DADA2 are the bioinformatic approaches used in the Knight Lab to get sOTUs from the data.
  * see also: OTU, QIIME, Biom format

* **Statistical tests** :ref:`[45]<reference45>`, :ref:`[46]<reference46>`

  * In microbiome research, we use statistical tests like regression, classification, PERMANOVA, and more to validate the chance that our conclusion is wrong based off the data.
  * see also: Differential abundance and compositionality

* **Taxonomy**

  * Taxonomy is a classification system for understanding how organisms are related to each other. Scientists use phylogenetic trees as one form of visualizing taxonomy. A phylogenetic tree takes organisms grouped by phenotypic (physical) and genotypic (genetic) similarities and connects them to their common ancestor from which they diverged evolutionarily. In microbiome research, we have developed tools like Unifrac to measure the evolutionary distance of relatedness of the organisms in two different samples.
  * see also: Phylogeny, Taxonomic Rank, OTU

* **Taxonomic Rank**

  * Taxonomic rank is a way of grouping organisms together based on their phenotypic and genotypic similarities. This ranking system originally proposed by Carl Linnaeus consists of seven levels: Domain, Kingdom, Phylum, Class, Order, Genus, Species. Humans, for examples, are described as Eukarya, Animalia, Chordata, Mammalia, Primate, Hominidae, Homo, H. sapiens. In microbiome research, we use sequencing techniques like amplicon sequencing which amplifies the 16s rRNA gene in bacteria to identify and classify microbes into their taxonomic ranks.
  * see also: Taxonomy, Phylogeny, Firmicutes, Proteobacteria, Gammaproteobacteria, Actinobacteria

* **Unifrac** :ref:`[57]<reference57>`, :ref:`[58]<reference58>`

  * Unifrac is a phylogenetic distance metric that compares multiple sample communities based on their locations to each other on the phylogenetic tree. The metric lies between a zero and a one: the former being no species are shared between the two samples and the latter being every species is shared between the two samples--meaning they are ecologically exactly the same. It measures the distance between communities as the percentage of phylogenetic branch length between the targeted communities. Unifrac is a computational tool to compare more than two species together simultaneously using multivariate statistics and nonparametric analyses.
  * see also: Beta Diversity, Alpha Diversity, Statistical Testings, Biom format, QIIME
