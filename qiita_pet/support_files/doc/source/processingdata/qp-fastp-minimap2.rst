Adapter and host filtering
==========================

At the end of August 2023, we discovered that the parameters used by
qp-fastp-minimap2 did not trigger application of adapter filtering. By default,
fastp performs autodetection of adapters and filtering for single-end data. By
default, fastp does not perform these operations on paired-end data. This behavior
was not expected by us. It was discovered when manually assessing replicated
sequences, which on examination by BLAST against NT reported to be adapters.

Adapter filtering for paired-end data with fastp requires specifying either the
exact adapters to remove (i.e., no autodetection), or to explicitly specify “--detect_adapter_for_pe”. Qiita previously indicated to users that the
qp-fastp-minimap2 plugin was performing adapter autodetection and filtering.
However, because this flag was not specified, that behavior did not occur.

In the metagenomic dataset the adapters were discovered in, we observed a few
sequences with high replication, which assignments to a few genomes in RS210.
The coverage of those genomes, using all metagenomic short reads, was constrained
to very specific regions. The replicated sequences exhibited high identity to
known adapters. As such, we suspect the replicated sequences we observed were
adapters. We suspect the observed genomes either suffer from adapter contamination
themselves, or the constructs used in the samples we examined were derived from
real organisms. Although we cannot differentiate this definitively in the data
we examined, in either case these short reads are likely artifactual.

For the dataset we examined, removal of these false positives was important
for the biological interpretation of the results. However, whether the removal
is important likely depends on the dataset and question.

qp-fastp-minimap2 has been updated to perform adapter filtering on paired-end data.
The fastp autodetection is compile-time limited to `the first 256k sequences <https://github.com/OpenGene/fastp/blob/7784d047fdf0a8df4211967156f5c97920c6d2e8/src/evaluator.cpp#L410-L417>`_.
Because of this, we opted for a more conservative approach of not relying on
autodetection and instead we now test all adapters that fastp is aware of. Specifically,
we now provide fastp a known adapters FASTA which is a serialized representation
of their `known adapter list <https://github.com/OpenGene/fastp/blob/7784d047fdf0a8df4211967156f5c97920c6d2e8/src/knownadapters.h#L11>`_.

The new command is named: `Adapter and host filtering v2023.12`.
