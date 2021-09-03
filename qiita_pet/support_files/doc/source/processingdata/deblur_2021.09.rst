deblur version 2021.09
======================

The deblur version 2021.09 addresses a bug with the fragment insertion parsing and
cache that ignored some fragments for getting an accurate placement in the tree. In
summary, in some occasions SEPP will return multiple fragments in a single entry; which
was unexpected by the qp-deblur plugin parser, which assumed only one entry - the
extra features will be seen as missing by the plugin and that information was
sent and stored in the cache provided by Qiita, then propagated to future studies and
meta-analyses.

This bug was resolved in this `pull request <https://github.com/qiita-spots/qp-deblur/pull/60>`__.

Sample counts implications
--------------------------

At the time of writing Qiita had 978,052 16S deblured private or pubic samples.
In the figure below, we have at different trimming lengths how many samples we recover
based on the minimum number of sequences per sample - this is an important consideration
as we normally need to remove samples below a given threshold for beta diversity
calculations (via rarefactoin) or differential abundance testing.

.. figure::  deblur2021.09_private_public.png
   :align:   center

A few conclusions from this plot:

- The maximum number of samples that we will recover are 6,771 at `Trimming (length: 150)`
  and min_seqs of 1,500; which represents a 0.7% increment in private and public samples.
- At all Trimming lengths the curve tends to go up and then down based on min_seq,
  which is a common trend seen in rarefacion plots


Reaching out to affected study owners
-------------------------------------

As you saw in the previous section the effect of the missing fragments depends on the
study, the trimming length and the minimum per sample sequence count. As a
general rule of thumb, as a first analytical pass for meta-analysis for 16S data, we use
5,000 sequences per sample and we prefer 150 base pair trimming. Thus, we directly
contacted all study owners that would recover more than 5% of the samples in their study
(total 24).
