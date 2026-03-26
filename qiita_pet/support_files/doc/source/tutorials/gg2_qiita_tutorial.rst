USING GREENGENES2 THROUGH QIITA TO COMBINE 16S AND WGS DATA AND ASSIGN TAXONOMY TO 16S
========================================================================================

Background
----------

Greengenes2 (GG2) is built off a comprehensive backbone phylogeny which is based on the
second version of the Web of Life and is updated using the uDance algorithm to include
approximately 330,000 high-quality, full-length 16S rRNA sequences from the Living Tree
Project (LTP) and other full-length operons. Over 20 million 16S rRNA V4 amplicon sequence
variants (ASVs), derived from hundreds of thousands of samples in the Qiita platform, are
placed into the tree using a neural network-based method called DEPP.

Due to such a composition, GG2 offers a unified, comprehensive reference tree linking 16S and
WGS metagenomics. It is embedded into QIITA's processing pipelines as the reference
framework and can be used to assign taxonomy through a combination of QIITA and QIIME.
More details about Greengenes2 can be found in `this publication <https://www.nature.com/articles/s41587-023-01845-1>`_
and through the `Greengenes2 website <https://greengenes.secondgenome.com/>`_.

All the code mentioned in this document is taken from the `QIIME2 documentation <https://docs.qiime2.org/>`_.
In order to use this code, you will need to create the required environment through your
operating system's CLI.

Detailed instructions on downloading and installing Miniconda for environment management,
and creating and testing the QIIME 2 Amplicon environment are mentioned `here <https://docs.qiime2.org/2024.10/install/>`_.

The first few steps include launching the QIIME2 Amplicon environment through Terminal on
MacOS (or any application that lets you access your operating system's command line
interface). Then, we download the relevant feature tables for 16s and WGS sequenced samples
along with the metadata (from the "Sample Information" tab) in a .txt or .tsv format

.. code-block:: bash

   conda activate qiime2-amplicon-2024.10 ## Activate the environment
   cd ~/Downloads # (or the directory containing saved Artifacts; usually Downloads)
   qiime tools peek {filenames you wish to locate}

On the study page, select the desired data type (eg. 16S or Metagenomic) and the specific
preparation information you wish to select. Navigate to this preparations processing network
page where you can see processed and unprocessed data as artifacts. Each triangle represents
a BIOM feature table. Click on the specific table you wish to download and scroll down.
Download the .qza file format of that feature table.

For the purpose of this demonstration, I will be using data from Study ID 13662 as mentioned in
QIITA. The specific feature tables that I used can be accessed through this analysis.

Path to download the specific 16S artifacts used in this tutorial (you can follow the same path
for any other study too!):

Make sure you are logged into your QIITA account to access the study.

.. code-block:: text

   Study page in QIITA → Click on 16S in the "Data Type" panel → navigate to the processing
   network page → locate Trimmed Demultiplexed 150 (△ in QIITA denote artifacts) → locate
   Deblur 2021.09 → locate deblur reference hit table (BIOM) → Click on the filtered_feature_table
   (BIOM) artifact at the end of this branch → scroll down and download the
   filtered_feature_table.qza (qza) artifact

Path to download the specific Metagenomic artifacts used in this tutorial (or any other QIITA
study):

.. code-block:: text

   Study page in QIITA → Click on Metagenomic in the "Data Type" panel → navigate to the
   processing network page → locate Woltka v.0.1.7, paired-end (◯ in QIITA denote job status) →
   locate Per-genome predictions WoLr2 (BIOM) → Click on the filtered_feature_table (BIOM)
   artifact at the end of the branch → scroll down and download the filtered_feature_table.qza
   (qza) artifact

Path to download the specific metadata file used in this tutorial (or any other QIITA study):

.. code-block:: text

   Study page in QIITA → Click on Sample Information on the top-left side of the study page →
   Click on Sample Info → This will download a metadata file with a .txt extension on your device.

Repeat this for all your samples!

In case you wish to skip log in, the following code enables public download of all the artifacts
used for this tutorial without needing to log in to QIITA –

.. code-block:: bash

   curl -O https://qiita.ucsd.edu/public/?artifact_id=220227
   curl -O https://qiita.ucsd.edu/public/?artifact_id=227266
   curl -O https://qiita.ucsd.edu/public/?artifact_id=227256
   curl -O https://qiita.ucsd.edu/public/?artifact_id=227260
   curl -O https://qiita.ucsd.edu/public_download/?data=sample_information&study_id=13662

Merging multiple preparations into one feature table
-----------------------------------------------------

This study has two different preparations for both 16S and metagenomic data. However, since
both the 16S preparations target the V4 region, we can merge the two tables into one and sum
up the frequencies of any overlapping samples. Similarly, the two Metagenomic preparations
can also be merged into one feature table.

In bigger studies, it is common to sequence the same sample for 16S sequencing as well as for
shotgun metagenomics. This manifests in the form of the same sample ID showing up in both
16S and metagenomic feature tables. Since the metadata will only mention a singular study ID
once, we need to make sure that if it is sequenced for both 16S and WGS, we modify the
metadata so that each row in the metadata represents a unique observation that is either
sequenced through 16s rRNA or shotgun metagenomic sequencing. The code below creates
two new columns in the metadata file. One column prints out studyID_16S and the other reads
studyID_WGS for each studyID. This will later help us run a combined PCoA for our 16s and
metagenomic samples without any duplicate sample collision.

.. code-block:: bash

   qiime feature-table merge \ # merging different metagenomic preps
     --i-tables 220227_filtered_feature_table.qza \
     --i-tables 227266_filtered_feature_table.qza \
     --p-overlap-method sum \
     --o-merged-table meta_merged.qza

   qiime feature-table merge \ # merging different 16S preps
     --i-tables 227256_filtered_feature_table.qza \
     --i-tables 227260_filtered_feature_table.qza \
     --p-overlap-method sum \
     --o-merged-table 16s_merged.qza

   qiime metadata tabulate \ # can be used to visualize metadata
     --m-input-file 13662_20240618_103623.txt\
     --o-visualization metadata_preview.qzv

In a new terminal window:

.. code-block:: bash

   cd {folder where metadata is saved}
   awk 'NR==1 {print $0"\tnew_16S_id\tnew_WGS_id"; next} {print $0"\t"$1"_16S\t"$1"_WGS"}' 13662_20240618_103623.txt> metadata_added_cols.tsv

Back in QIIME2 Terminal window :

.. code-block:: bash

   qiime feature-table rename-ids \
     --i-table 16s_merged.qza \
     --m-metadata-file metadata_added_cols.tsv \
     --m-metadata-column new_16S_id \
     --p-axis sample \
     --o-renamed-table merged_16s_renamed.qza

   qiime feature-table rename-ids \
     --i-table meta_merged.qza \
     --m-metadata-file metadata_added_cols.tsv \
     --m-metadata-column new_WGS_id \
     --p-axis sample \
     --o-renamed-table merged_metagenomic_renamed.qza

Assigning taxonomy (v4):
-------------------------

For studies targeting the V4 region of the 16S rRNA gene, taxonomy can be derived directly
from the phylogeny without requiring use of Naive Bayes, which appears to yield a higher
resolution result relative to Naive Bayes.
(`https://forum.qiime2.org/t/introducing-greengenes2-2022-10/25291 <https://forum.qiime2.org/t/introducing-greengenes2-2022-10/25291>`_)

The structure of the database is such that if you have V4 data, there is a great chance that the
majority of your sequencing data is already represented by Greengenes2.
(`https://forum.qiime2.org/t/introducing-greengenes2-2022-10/25291 <https://forum.qiime2.org/t/introducing-greengenes2-2022-10/25291>`_)

Larger picture: Greengenes2 provides a huge reference tree which can be thought of like a
massive family tree where each branch or leaf has a tag of its taxonomy. This tree contains both
the 16s sequences from your samples as well as the WGS genomes. In the simplest of terms, to
assign taxonomy, we would try to locate each sequence on the family tree and note its tag
name. More specifically, we perform a set intersection between the contents of the
FeatureTable[Frequency] table and the database.

Important checks before starting the assignment-

- The 16s feature table: feature IDs are DNA sequences

.. code-block:: bash

   qiime tools export \
     --input-path 16s_merged.qza \
     --output-path exported_table

   biom head -i exported_table/feature-table.biom

 The output should look something like this (or at least of the same format)

This step determines the type of Greengenes2 file you will need to use for your particular
feature ID format. In this case, since the feature IDs are DNA sequences, we will choose the
.asv file. (look out for numbers? or MD5 hashes- .md5 files)

- WGS table: feature IDs are genome IDs (often look like G000012345)

Step 1: Download the reference trees from the internet
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The `Greengenes2 website <https://greengenes.secondgenome.com/>`_ provides both a tree version and a tab-delimited (.tsv) file variant.
However, for this tutorial I will be using the tree since it is more decompressed.

.. code-block:: bash

   wget ftp://ftp.microbio.me/greengenes_release/2024.09/2024.09.taxonomy.asv.nwk.qza
   wget ftp://ftp.microbio.me/greengenes_release/2024.09/2024.09.phylogeny.asv.nwk.qza

 
Step 2: Modifying metadata file to make it compatible with our combined PCoA workflow
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

At the moment, the metadata file has the following format:

.. code-block:: text

   sample_name [col1] [col2] ....... [coln-2] new_16s_id new_WGS_id

We need to create a new metadata table where every sample name has a unique identifier that
is either _16s or _WGS. This will ensure smooth merging of feature tables without flagging for
duplicates when we attempt doing a combined PCoA for 16s and WGS. While we are in the
process of updating the metadata, we can also add a sequencing_type column which will later
allow us to be able to color our PCoA visualization by the sequencing technique used for the
sample that is 16s or WGS.

As with all the other code in this post, you should be able to switch out the filenames for yours
and use the exact code.

- creating _16s metadata where the indices are now of the form sample-name_16s + add a sequencing_type column for better visualization

.. code-block:: bash

   awk 'BEGIN{FS=OFS="\t"}
   NR==1 {
     n=NF-1;
     printf "sample-id";
     for(i=2; i<=NF-2; i++) printf OFS $i;
     print OFS "sequencing_type"
   }
   NR>1 {
     n=NF-1;
     printf $n;
     for(i=2; i<=NF-2; i++) printf OFS $i;
     print OFS "16S"
   }' metadata_added_cols.tsv > metadata_16s.tsv

- creating a WGS metadata where the indices are now of the form sample-name_wgs + add a sequencing_type column for better visualization

.. code-block:: bash

   awk 'BEGIN{FS=OFS="\t"}
   NR==1 {
     printf "sample-id";
     for(i=2; i<=NF-2; i++) printf OFS $i;
     print OFS "sequencing_type"
   }
   NR>1 {
     printf $NF;
     for(i=2; i<=NF-2; i++) printf OFS $i;
     print OFS "WGS"
   }' metadata_added_cols.tsv > metadata_wgs.tsv

- creating metadata_combined.tsv by concatenating the 16s metadata and the WGS metadata

.. code-block:: bash

   cat metadata_16s.tsv > metadata_combined.tsv
   tail -n +2 metadata_wgs.tsv >> metadata_combined.tsv

Step 3: Filter features against the tree
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This step, although optional, is recommended. It allows us to filter our features from the
feature table against the GG2 tree of choice. It checks all the features against the ones in the
tree and outputs an updated table which only contains the features that match.

**16S:**

.. code-block:: bash

   qiime greengenes2 filter-features \
     --i-feature-table merged_16s_renamed.qza \
     --i-reference 2024.09.phylogeny.asv.nwk.qza \
     --o-filtered-feature-table 16s-filtered.qza \
     --verbose

**WGS:**

.. code-block:: bash

   qiime greengenes2 filter-features \
     --i-feature-table merged_metagenomic_renamed.qza \
     --i-reference 2024.09.phylogeny.asv.nwk.qza \
     --o-filtered-feature-table wgs-filtered.qza \
     --verbose

 
Step 4: Assigning taxonomy to 16S and WGS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Now that we are only working with features that are represented in the reference tree, we
can go ahead and grab taxonomy for those amplicon sequence variants and operational
genomic units.

**16S:**

.. code-block:: bash

   qiime greengenes2 taxonomy-from-table \
     --i-reference-taxonomy 2024.09.taxonomy.asv.nwk.qza \
     --i-table 16s-filtered.qza \
     --o-classification 16s-taxonomy.qza \
     --verbose

**WGS:**

.. code-block:: bash

   qiime greengenes2 taxonomy-from-table \
     --i-reference-taxonomy 2024.09.taxonomy.asv.nwk.qza \
     --i-table wgs-filtered.qza \
     --o-classification meta-taxonomy.qza \
     --verbose

 
Step 5: Create visualizations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**16S:**

.. code-block:: bash

   qiime metadata tabulate \
     --m-input-file 16s-taxonomy.qza \
     --o-visualization 16s-taxonomy.qzv

   qiime taxa barplot \
     --i-table merged_16s_renamed.qza \
     --i-taxonomy 16s-taxonomy.qza \
     --m-metadata-file metadata_16s.tsv \
     --o-visualization 16s-taxa-barplot.qzv

**WGS:**

.. code-block:: bash

   qiime metadata tabulate \
     --m-input-file meta-taxonomy.qza \
     --o-visualization meta-taxonomy.qzv

   qiime taxa barplot \
     --i-table merged_metagenomic_renamed.qza \
     --i-taxonomy meta-taxonomy.qza \
     --m-metadata-file metadata_wgs.tsv \
     --o-visualization meta-taxa-barplot.qzv

This is a snapshot of the 16s artifact visualization. The bar chart can be filtered for multiple
taxonomic levels ranging from Level 1 through Level 7.

All .qzv artifacts can be visualized at https://view.qiime2.org/ !

Creating a combined PCoA plot
------------------------------

Step 6: Merge feature tables and taxonomies
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   qiime feature-table merge \
     --i-tables merged_16s_renamed.qza \
     --i-tables merged_metagenomic_renamed.qza \
     --o-merged-table merged-16s-meta.qza

   qiime feature-table summarize \
     --i-tables merged-16s-meta.qza \
     --m-sample-metadata-file metadata_added_cols.qza \
     --o-merged-table merged-table-summary.qza

   qiime feature-table merge-taxa \
     --i-data 16s-taxonomy.qza \
     --i-data meta-taxonomy.qza \
     --o-merged-data merged-taxonomy.qza

   qiime taxa barplot \
     --i-table merged-16s-meta.qza \
     --i-taxonomy merged-taxonomy.qza \
     --m-metadata-file metadata_combined.tsv \
     --o-visualization merged-taxa-barplot.qzv

 
Step 7: Calculating distance matrices (using all distance metrics)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Using weighted UniFrac:

.. code-block:: bash

   qiime diversity beta-phylogenetic \
     --i-table merged-16s-meta.qza \ #5000 sequences per sample
     --i-phylogeny 2024.09.phylogeny.asv.nwk.qza \
     --p-metric weighted_unifrac \
     --o-distance-matrix merged-weighted-unifrac.qza \
     --verbose

Using unweighted UniFrac:

.. code-block:: bash

   qiime diversity beta-phylogenetic \
     --i-table merged-16s-meta.qza \
     --i-phylogeny 2024.09.phylogeny.asv.nwk.qza \
     --p-metric unweighted_unifrac \
     --o-distance-matrix merged-unweighted-unifrac.qza \
     --verbose

Using Bray-Curtis:

.. code-block:: bash

   qiime diversity beta \
     --i-table merged-16s-meta.qza \
     --p-metric braycurtis \
     --o-distance-matrix merged-bray-curtis.qza

 
Step 8: Combined 16s + WGS PCoA
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Using weighted UniFrac distance matrix:

.. code-block:: bash

   qiime diversity pcoa \
     --i-distance-matrix merged-weighted-unifrac.qza \
     --o-pcoa merged-weighted-unifrac-pcoa.qza

Using unweighted UniFrac distance matrix:

.. code-block:: bash

   qiime diversity pcoa \
     --i-distance-matrix merged-unweighted-unifrac.qza \
     --o-pcoa merged-unweighted-unifrac-pcoa.qza

Using Bray-Curtis distance matrix:

.. code-block:: bash

   qiime diversity pcoa \
     --i-distance-matrix merged-bray-curtis.qza \
     --o-pcoa merged-bray-curtis-pcoa.qza

 
Step 9: Emperor plots for PCoA visualization
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   qiime emperor plot \
     --i-pcoa merged-weighted-unifrac-pcoa.qza \
     --m-metadata-file metadata_combined.tsv \
     --o-visualization merged-weighted-unifrac-emperor.qzv

   qiime emperor plot \
     --i-pcoa merged-unweighted-unifrac-pcoa.qza \
     --m-metadata-file metadata_combined.tsv \
     --o-visualization merged-unweighted-unifrac-emperor.qzv

   qiime emperor plot \
     --i-pcoa merged-bray-curtis-pcoa.qza \
     --m-metadata-file metadata_combined.tsv \
     --o-visualization merged-bray-curtis-emperor.qzv

.. figure:: im4_braycurtis.png
   :alt: Bray-Curtis (Blue: 16s, Red: WGS)
   Bray-Curtis (Blue: 16s, Red: WGS)

.. figure:: im5_uwunifrac.png
   :alt: Unweighted UniFrac (Blue: 16s, Red: WGS)
   Unweighted UniFrac (Blue: 16s, Red: WGS)

.. figure:: im6_wunifrac.png
   :alt: Weighted UniFrac (Blue: 16s, Red: WGS)
   Weighted UniFrac (Blue: 16s, Red: WGS)

View all .qzv files at https://view.qiime2.org !

For non-V4 data, check out this `forum post <https://forum.qiime2.org/t/introducing-greengenes2-2022-10/25291>`_ by Daniel McDonald.

