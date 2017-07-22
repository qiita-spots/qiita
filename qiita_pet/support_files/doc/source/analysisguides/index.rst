Analysis Guides
===============


Qiita now uses `QIIME2 <http://qiime2.org>`__ plugins for analysis.
-------------------------------------------------------------------
Thanks to this, we've got new layout of the analysis panel and the following new features:

* `alpha diversity <https://docs.qiime2.org/2017.6/plugins/available/diversity/alpha/>`__ (including statistics calculations; example `here <https://view.qiime2.org/visualization/?type=html&src=https%3A%2F%2Fdocs.qiime2.org%2F2017.6%2Fdata%2Ftutorials%2Fmoving-pictures%2Fcore-metrics-results%2Ffaith-pd-group-significance.qzv>`__)  
* `beta diversity <https://docs.qiime2.org/2017.6/plugins/available/diversity/beta/>`__ (including stats)
* `rarefaction <https://docs.qiime2.org/2017.6/plugins/available/feature-table/rarefy/>`__
* `filter samples <https://docs.qiime2.org/2017.6/plugins/available/feature-table/filter_samples/>`__
* `taxa summary <https://docs.qiime2.org/2017.6/plugins/available/taxa/barplot/>`__ (example `here <https://view.qiime2.org/visualization/?type=html&src=https%3A%2F%2Fdocs.qiime2.org%2F2017.6%2Fdata%2Ftutorials%2Fmoving-pictures%2Ftaxa-bar-plots.qzv>`__)


Analysis workflow
-----------------

* creating new analysis
Select Analysis -> Create new analysis from the main Qiita toolbar. From the list of your studies, select which artifacts you want to add to your analysis.

[image]

The analysis workflow now has a similar layout to sample processing. By selecting artifacts and commands from the drop-down menu below the workflow visualization, an entire analysis workflow can be created.

* filtering samples

BIOM artifact can be filtered to include samples containing specific metadata categories, or minimum/maximum frequency or number of features.

* rarefying

BIOM artifact can be rarefied to a desired sampling depth and results in a new rarefied BIOM artifact.

* taxa summary



* alpha diversity

* beta diversity
