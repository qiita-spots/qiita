Analysis Guides
===============


Qiita now uses `QIIME2 <http://qiime2.org>`__ plugins for analysis.
-------------------------------------------------------------------
Thanks to this, we've got new layout of the analysis panel and the following new features:

* `alpha diversity <https://docs.qiime2.org/2017.6/plugins/available/diversity/alpha/>`__ (including statistics calculations; example `here <https://view.qiime2.org/visualization/?type=html&src=https%3A%2F%2Fdocs.qiime2.org%2F2017.6%2Fdata%2Ftutorials%2Fmoving-pictures%2Fcore-metrics-results%2Ffaith-pd-group-significance.qzv>`__)  
* `beta diversity <https://docs.qiime2.org/2017.6/plugins/available/diversity/beta/>`__ (including stats)
* principal coordinate analysis (`PCoA <https://docs.qiime2.org/2017.6/plugins/available/diversity/pcoa/>`__), including ordination results and EMPeror plots (example `here <https://view.qiime2.org/visualization/?type=html&src=https%3A%2F%2Fdocs.qiime2.org%2F2017.6%2Fdata%2Ftutorials%2Fmoving-pictures%2Fcore-metrics-results%2Funweighted-unifrac-emperor.qzv>`__)
* `rarefaction <https://docs.qiime2.org/2017.6/plugins/available/feature-table/rarefy/>`__
* `filter samples <https://docs.qiime2.org/2017.6/plugins/available/feature-table/filter_samples/>`__
* `taxa summary <https://docs.qiime2.org/2017.6/plugins/available/taxa/barplot/>`__ (example `here <https://view.qiime2.org/visualization/?type=html&src=https%3A%2F%2Fdocs.qiime2.org%2F2017.6%2Fdata%2Ftutorials%2Fmoving-pictures%2Ftaxa-bar-plots.qzv>`__)


Analysis workflow
-----------------

Each analysis out of taxa summary, alpha diversity and beta diversity produces a QIIME2 visualization which can be browsed within Qiita, as well as downloadable result files.  
Filtering samples and rarefaction produce downloadable BIOM artifacts.

* creating new analysis
Select Analysis -> Create new analysis from the main Qiita toolbar. From the list of your studies, select which studies and artifacts you want to add to your analysis.

.. figure::  images/figure1.png
   :align:   center

The analysis workflow now has a similar layout to sample processing. By selecting artifacts and commands from the drop-down menu below the workflow visualization, an entire analysis workflow can be created.

.. figure::  images/figure2.png
   :align:   center


* filtering samples

BIOM artifact can be filtered to include samples containing specific metadata categories, or minimum/maximum frequency or number of features.

* rarefying

BIOM artifact can be rarefied to a desired sampling depth and results in a new rarefied BIOM artifact.

* taxa summary

Takes BIOM artifact as input and returns an interactive stacked barchart which can be investigated on different taxonomic levels, as well as using metadata categories.

* alpha diversity

Takes BIOM artifact as input. Produces a vector of alpha diversity results (text file) and downloadable interactive boxplots. Visualizations can be investigated using metadata categories and appropriate statistics are generated for all groups and pairwise.

* beta diversity

Beta diversity analysis on a BIOM artifact can be performed using a variety of phylogenetic and non-phylogenetic distance metrics. Produces a distance matrix as output. 

* principal coordinate analysis

Takes beta diversity distance matrix (result of beta diversity) and generates an interactive EMPeror plot.
