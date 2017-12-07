Deblurring 
----------
* **Trimming**: Removes base pairs from the sequences
 * **Input Data** (required): Data being trimmed
 * **Parameter Set** (required): How many bases to trim off
  * **90 base pairs**- Removes first 90 base pairs from the sequences
  * **100 base pairs**- Removes first 100 base pairs from the sequences
  * **125 base pairs**- Removes first 125 base pairs from the sequences
  * **150 base pairs**- Removes first 150 base pairs from the sequences
  * **200 base pairs**- Removes first 200 base pairs from the sequences
  * **250 base pairs**- Removes first 250 base pairs from the sequences
  * **300 base pairs**- Removes first 300 base pairs from the sequences
* **Command from Trimmed Artifact**:
 * **Deblur Workflow**: Removes sequences due to error and does not take into account if sequences are found in a database
  * **Default Parameters** 
   * **Error probabilities for each Hamming distance** (required): List of error probabilities for each hamming distance
    * Length of list determines number of hamming distances taken into account
   * **Indexed negative filtering database** (required): Indexed version of the negative filtering database
   * **Indexed positive filtering database** (required): Indexed version of the positive filtering database
   * **Insertion/deletion (indel) probability** (required): Insertion/deletion probability
   * **Jobs to start** (required): Number of workers to start (if to run in parallel)
   * **Maximum number of insertion/deletion (indel)** (required): Maximum number of allowed insertions/deletions
   * **Mean per nucleotide error rate** (required): Mean per nucleotide error rate
    * Used for original sequence estimate if the the typical Illumina error wasn’t passed for the original
   * **Minimum dataset-wide read threshold** (required): Keep only the sequences which appear at this many times study wide (as opposed to per-sample)
   * **Minimum per-sample read threshold** (required): Keep only the sequences which appear at this many times per sample (as opposed to study wide)
   * **Negative filtering database** (required): Negative (artifacts) filtering database
    * Drops all sequences which align to any record in this
   * **Positive filtering database** (required): Positive reference filtering database
    * Keeps all sequences permissively aligning to any sequence
   * **Sequence trim length (-1 for no trimming)** (required): Sequence trim length
   * **Threads per sample** (required): Number of threads to use per sample
 * **Deblur 16S Only Table**: Only contains 16S deblurred sequences 
 * **Deblur Final Table**: Contains all the sequences.
* **Deblur Citation**: *Amir, A., McDonald, D., Navas-Molina, J.A., Kopylova, E., Morton, J., Xu, Z.Z., Kightley, E.P.,  Thompson, L.R., Hyde, E.R., Gonzalez, A., Knight, R. (2017) “Deblur rapidly resolves single-nucleotide community sequence patterns.” mSystems. 2 (2) e00191-16.*
