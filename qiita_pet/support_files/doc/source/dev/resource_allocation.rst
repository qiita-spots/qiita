.. _resource_allocation:

.. index :: _resource_allocation

Qiita's per job resources allocation
====================================

Qiita will request specific resource allocations based on the name of the command,
the job type and it's definition in the database. These definitions are in the
qiita.processing_job_resource_allocation table in the database. This table has name
(the name of the job), a description, job_type (more below), and the allocation for
that job.

Job types
---------

The Qiita job types allows us to better group the jobs based on what they do and
separate possible name conflicts while at the same time kipping these separation
simple.

#. RESOURCE_PARAMS_COMMAND: This is the most common entry as it defines the allocation
   for an specific command name, like "Shogun v1.0.7" or "Beta diversity (phylogenetic)",
   for the complete list of commands visit: `Qiita Software <https://qiita.ucsd.edu/software/>`__
#. COMPLETE_JOBS_RESOURCE_PARAM: When a RESOURCE_PARAMS_COMMAND completes, it will define if the job
   finished successfully and a set of artifact(s) that need to be validated and then added to Qiita -
   move to the final locations and register them in the database. For these jobs the name is the actual
   artifact type that is being generated, for example: "per_sample_FASTQ" or "q2_visualization"
#. RELEASE_VALIDATORS_RESOURCE_PARAM: The complete job will create a new job to release and coordinate
   all the artifact validators for a given command
#. VALIDATOR: Each new artifact needs a validator and depends on the Qiita plugin that defined
   that artifact type. Similar to COMPLETE_JOBS_RESOURCE_PARAM here the name of the job is the
   artifact type being validated
#. REGISTER: Used to install or register a new plugin and their commands in the Qiita system

Note that all these job types have a default value (name of the entry is default) so if there is no definition
for that command or artifact it will use those resources

Resources allocation
--------------------

The allocation of each job is what a user will normally use to define resources when
submitting a job into a queueing system, for example: `-q qiita -l nodes=1:ppn=1 -l mem=8gb -l walltime=300:00:00`

We have defined some "internal" rules:

#. Always submitted to the qiita queue
#. Memory allocation should be done using: mem (memory for the full job); suggest using 1G as the
   minimum request (no benefit selecting 1G vs 700M)
#. The nodes and cores allocations should be in the form of: nodes=<num>:ppn=<num>
#. Always request walltime!
#. The queueing system uses mem for vacating jobs, not vmem, so focus on mem utilization (ignore
   vmem - at least for now)

Resources allocation by formula
-------------------------------

It is possible to define a memory allocation by a formula using the values: "{samples}" - the
number of samples in the information file, "{columns}" - the number of columns in the information file,
and "{input_size}" -  the total size of the artifact type (in bytes).

Some examples:

#. Request 1K per sample: samples*1000 -> "-q qiita -l nodes=1:ppn=5 -l mem={samples}*1000 -l walltime=130:00:00"
#. Request at least 4M and then add samples+columns and request 1M for each:
   ((samples+columns)*1000000)+4000000 -> "-q qiita -l nodes=1:ppn=5 -l mem=(({samples}+{columns})*1000000)+4000000
   -l walltime=130:00:00"
#. Request at least 2G and grow based on input size: {input_size}+(2*1e+9) -> "-q qiita -l nodes=1:ppn=5 -l
   mem={input_size}+(2*1e+9) -l walltime=130:00:00"
