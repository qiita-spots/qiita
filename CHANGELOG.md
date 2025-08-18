# Qiita changelog

Version 2025.07
---------------

Deployed on July 15th, 2025

* During EBI-ENA submissions now we automatically renmae `country` to `geographic location (country and/or sea)` and `collection_date` to `collection date`; as the ENA requirements changed.
* Added platform `DNBSEQ1` and instruments: `DNBSEQ-G400`, `DNBSEQ-T7`, `DNBSEQ-G800` for EBI-ENA submissions.
* Other general fixes [#3474](https://github.com/qiita-spots/qiita/pull/3474), [#3475](https://github.com/qiita-spots/qiita/pull/3475).
* SPP: merged and deprecated [mg-scripts](https://github.com/qiita-spots/mg-scripts) to [qp-knight-lab-processing](https://github.com/qiita-spots/qp-knight-lab-processing).
* SPP: Added integration tests via a couple of PRs: [#129](https://github.com/qiita-spots/qp-knight-lab-processing/pull/129) & [#131](https://github.com/qiita-spots/qp-knight-lab-processing/pull/131).
* SPP: Added new command `Human Filter & QC existing Prep` to facilitate human-filtering existing preparations.
* SPP: Cleaned and centralized sequencers information to [kl-metapool](https://github.com/biocore/kl-metapool) & added `MiSeq i100`, thank you @AmandaBirmingham.
* SPP: Added a new [subsample method](https://github.com/qiita-spots/qp-knight-lab-processing/pull/138) to randomly select sequences from paired files when they are larger than expected: 720,000,000.
* SPP: Storing `TellReadJob/QC_Analysis_TellReadJob.html` in the results folder.



Version 2025.04
---------------

Deployed on April 11th, 2025

* General improvements for automatic environment generation by @sjanssen2 (thank you!): [#3462](https://github.com/qiita-spots/qiita/pull/3462), [#3463](https://github.com/qiita-spots/qiita/pull/3463), [3464](https://github.com/qiita-spots/qiita/pull/3464), [#3465](https://github.com/qiita-spots/qiita/pull/3465).
* When ProcessingJob.resource_allocation_info fails, it will now be [set as the error for the job](https://github.com/qiita-spots/qiita/pull/3466).
* SPP: General updates and clean up: [#169](https://github.com/biocore/mg-scripts/pull/169), [#101](https://github.com/qiita-spots/qp-knight-lab-processing/pull/101).
* `Remove SynDNA plasmid, insert, & CP026085 reads` superseded `Remove SynDNA inserts & plasmid reads`; which now removes SynDNA plasmids, inserts, and CP026085 reads, in this order.


Version 2025.02
---------------

Deployed on February 24th, 2025

* Replaced os.rename for shutil.move in the code to fix [#3455](https://github.com/qiita-spots/qiita/issues/3455).
* Via qp-spades, replaced the legacy `spades` command for `cloudSPAdes` for TellSeq.
* `FASTA_preprocessed` within qtp-sequencing now allows for results to be named using their sample-name, extra from run-prefix.
* `Remove SynDNA inserts & plasmid reads` superseded `Remove SynDNA reads`, which now removes SynDNA inserts and plasmids.
* `update_resource_allocation_redis` now relies on using equations stored in the database vs. hardcoded; thank you @Gossty!
* SPP: Updated prep-info file generation to identify and report filtered fastq files that could not be matched to a sample-id instead of silently ignoring them.
* SPP: Removed legacy test code and example files for amplicon processing. Some other tests updated and repurposed.
* SPP: jobs are now easier to restart.
* SPP: MultiQC report generation is now a separate slurm job & use jinja2 templates; also FastQC use jinja2 templates.


Version 2025.01
---------------

Deployed on January 15th, 2025

* The Analysis owner is now displayed in the analysis list and the individual analysis page.
* Admins can now use the per-preparation "Download Data Release" button to get a "BIOM" release; this version is focus on NPH data releases.
* Improved complete_job creation time, which should result in Qiita jobs ([multiple steps](https://qiita.ucsd.edu/static/doc/html/dev/resource_allocation.html) finishing faster; for bencharks visit [patch 93.sql](https://github.com/qiita-spots/qiita/blob/master/qiita_db/support_files/patches/93.sql).
* SPP improvements: TellSeq support added; plugin refactored to allow for easier additions like TellSeq in the future. Job restart greatly improved. Much improved handling of sample-names and ids that contain substrings like ‘I1’ and ‘R2’. New SequenceCount job can count sequences and base-pairs in parallel for any list of fastq files.
* Other general fixes [#3440](https://github.com/qiita-spots/qiita/pull/3440), [#3445](https://github.com/qiita-spots/qiita/pull/3445), [#3446](https://github.com/qiita-spots/qiita/pull/3446),


Version 2024.10
---------------

Deployed on October 14th, 2024

* Added update_resource_allocation_redis and companion code, so resource allocations summaries are available for review. Thank you @Gossty!
* Now is possible to have default workflows with only one step.
* `qiita_client.update_job_step` now accepts an ignore_error optional parameter. Thank you @charles-cowart!
* Initial changes in `qiita_client` to have more accurate variable names: `QIITA_SERVER_CERT` -> `QIITA_ROOTCA_CERT`. Thank you @charles-cowart!
* Added `get_artifact_html_summary` to `qiita_client` to retrieve the summary file of an artifact.
* Re-added github actions to `https://github.com/qiita-spots/qiita_client`.
* `SortMeRNA v4.3.7` superseded `Sortmerna v2.1b`, which relies on Silva 138 and now produced even mates. Thank you @ekopylova and @biocodz for the support.
* `Remove SynDNA reads` superseded `SynDNA Woltka`, which now generates even mates.
* `Woltka v0.1.7, paired-end` superseded `Woltka v0.1.6` in `qp-woltka`; [more information](https://qiita.ucsd.edu/static/doc/html/processingdata/woltka_pairedend.html). Thank you to @qiyunzhu for the benchmarks!
* Other general fixes, like [#3424](https://github.com/qiita-spots/qiita/pull/3424), [#3425](https://github.com/qiita-spots/qiita/pull/3425), [#3439](https://github.com/qiita-spots/qiita/pull/3439), [#3440](https://github.com/qiita-spots/qiita/pull/3440).
* General SPP improvements, like: [NuQC modified to preserve metadata in fastq files](https://github.com/biocore/mg-scripts/pull/155), [use squeue instead of sacct](https://github.com/biocore/mg-scripts/pull/152), , [job aborts if Qiita study contains sample metadata columns reserved for prep-infos](https://github.com/biocore/mg-scripts/pull/151), [metapool generates OverrideCycles value](https://github.com/biocore/metagenomics_pooling_notebook/pull/225).
* We updated the available parameters for `Filter features against reference [filter_features]`, `Non V4 16S sequence assessment [non_v4_16s]` and all the phylogenetic analytical commands so they can use `Greengenes2 2024.09`.



Version 2024.07
---------------

Deployed on July 15th, 2024

* On June 14th, 2024 we modified the SPP to use ["fastp & minimap2 against GRCh38.p14 + Phi X 174 + T2T-CHM13v2.0, then Movi against GRCh38.p14, T2T-CHM13v2.0 + Human Pangenome Reference Consortium release 2023"](https://github.com/cguccione/human_host_filtration) to filter human-reads.
* Full refactor of the [DB patching system](https://github.com/qiita-spots/qiita/blob/master/CONTRIBUTING.md#patch-91sql) to make sure that a new production deployment has a fully empty database.
* Fully removed Qiimp from Qiita.
* Users can now add `ORCID`, `ResearchGate` and/or `GoogleScholar` information to their profile and the creation (registration) timestamp is kept in the database. Thank you @jlab.
* Admins can now track and purge non-confirmed users from the database via the GUI (`/admin/purge_users/`). Thank you @jlab.
* Added `qiita.slurm_resource_allocations` to store general job resource usage, which can be populated by `qiita_db.util.update_resource_allocation_table`.
* Added `qiita_db.util.resource_allocation_plot` to generate different models to allocate resources from a given software command based on previous jobs, thank you @Gossty !
* The stats page map can be centered via the configuration file; additionally, the Help and Admin emails are defined also via the configuration files, thank you @jlab !
* ``Sequel IIe``, ``Revio``, and ``Onso`` are now valid instruments for the ``PacBio_SMRT`` platform.
* Added `current_human_filtering` to the prep-information and `human_reads_filter_method` to the artifact to keep track of the method that it was used to human reads filter the raw artifact and know if it's up to date with what is expected via the best practices.
* Added `reprocess_job_id` to the prep-information so we keep track if a preparation has been reprocessed with another job.
* Other general fixes, like [#3385](https://github.com/qiita-spots/qiita/pull/3385), [#3397](https://github.com/qiita-spots/qiita/pull/3397), [#3399](https://github.com/qiita-spots/qiita/pull/3399), [#3400](https://github.com/qiita-spots/qiita/pull/3400), [#3409](https://github.com/qiita-spots/qiita/pull/3409), [#3410](https://github.com/qiita-spots/qiita/pull/3410).


Version 2024.02
---------------

Deployed on February 27th, 2024

* Default workflows now accept commands with multiple inputs.
* The loading time of the main study page was improved [#3350](https://github.com/qiita-spots/qiita/pull/3350).
* SPP improvements - mainly @charles-cowart, thank you! Errors are now show to the user in the GUI [#127](hhttps://github.com/biocore/mg-scripts/pull/127), admins can restart jobs [#129](hhttps://github.com/biocore/mg-scripts/pull/129), adapter-trimmer files now are stored and their sequence counts are part of the prep-info [#126](hhttps://github.com/biocore/mg-scripts/pull/126), and support for per instrument/data-type configuration [#123](hhttps://github.com/biocore/mg-scripts/pull/123).
* The internal Sequence Processing Pipeline is now using the https://www.gencodegenes.org human transcripts v44 for Metatranscriptomic data - additional to the human pan-genome reference, with the GRCh38 genome + PhiX and T2T-CHM13v2.0 genome - for human host filtering.
* Added a command to qp-woltka: 'Calculate RNA Copy Counts'.
* Other fixes - mainly by @sjanssen2, thank you!: [#3345](https://github.com/qiita-spots/qiita/pull/3345),[#3224](https://github.com/qiita-spots/qiita/pull/3224),  [#3357](https://github.com/qiita-spots/qiita/pull/3357), [#3358](https://github.com/qiita-spots/qiita/pull/3358), [#3359](https://github.com/qiita-spots/qiita/pull/3359), [#3362](https://github.com/qiita-spots/qiita/pull/3362), [#3364](https://github.com/qiita-spots/qiita/pull/3364).


Version 2023.12
---------------

Deployed on January 8th, 2024

* The sample and preparation information pages will display the timestamp of their last update.
* Added a ProcessingJob.complete_processing_job method to retrieve the job that is completing the current job.
* Added a ProcessingJob.trace method to trace all the jobs of a processing_job.
* Analyses now accept SLURM reservation's via the GUI; this will be [helpful for workshops or classes](https://qiita.ucsd.edu/static/doc/html/faq.html#are-you-planning-a-workshop-or-class).
* Admins can now add per-user-level SLURM submission parameters via the DB; this is helpful to prioritize wet-lab and admin jobs.
* Workflow definitions can now use sample or preparation information columns/values to differentiate between them.
* Updated the Adapter and host filtering plugin (qp-fastp-minimap2) to v2023.12 addressing a bug in adapter filtering; [more information](https://qiita.ucsd.edu/static/doc/html/processingdata/qp-fastp-minimap2.html).
* Other fixes: [3334](https://github.com/qiita-spots/qiita/pull/3334), [3338](https://github.com/qiita-spots/qiita/pull/3338). Thank you @sjanssen2.
* The internal Sequence Processing Pipeline is now using the human pan-genome reference, together with the GRCh38 genome + PhiX and T2T-CHM13v2.0 genome for human host filtering.
* Added two new commands to qp-woltka: 'SynDNA Woltka' & 'Calculate Cell Counts'.


Version 2023.10
---------------

* Added a new notebooks folder to the repository to allocate the resource-allocation code and plotting.
* Allowed dynamic resource allocations for time (before it was only for memory), and allowed complex formulas (via eval).
* Deployed the new resource allocation formulas. This included changes on how the ProcesingJob.shape method calculates its variables, which include: (a) `build_analysis_files`: only use the `biom` file (vs. all of them); and (b) the SPP counts the input-file number of lines know the number of samples.
* qp-woltka generates a new file: coverates.tgz, which contains: (a) artifact.cov: the coverages of this artifact, can be used with other coverages to generate combined coverages; (b) coverage_percentage.txt: the total percentage coverage per-genome of this artifact; and (c) coverages folder: the per-sample coverage.
* The SPP now supports replicates within the same lane/run and creates multiple preparations as needed.
* The SPP automatically adds and executes the default pipeline after it is done generating and linking the raw data.
* Other fixes: [#3300](https://github.com/qiita-spots/qiita/issues/3300), [metapool #135](https://github.com/biocore/metagenomics_pooling_notebook/pull/135), [metapool #136](https://github.com/biocore/metagenomics_pooling_notebook/pull/136), [qtp-sequencing #47](https://github.com/qiita-spots/qtp-sequencing/pull/47).


Version 2023.06
---------------

* EBI-ENA submissions require a sample metadata column: **geographic location (country and/or sea)**, Qiita will automatically rename **country** to satisfy this requirement.
* The qp-knight-lab-processing was [refactored for better performance and testing](https://github.com/qiita-spots/qp-knight-lab-processing/pull/60); mainly contributed by @charles-cowart.
* Admin Sample Validation now uses tube_id; mainly contributed by @CatFish47.
* Registered users cannot start sample deletion jobs within public studies.
* The qp-knight-lab-processing now links the SPP job to the preparation it creates and links the created files to that preparation. Note that no files are being moved to the upload folder.
* Fixed the following issues [#3227](https://github.com/qiita-spots/qiita/issues/3227), [#3279](https://github.com/qiita-spots/qiita/issues/3280), [#3227](https://github.com/qiita-spots/qiita/issues/3280).
* Added ProcessingJob.external_id to status-report messages generated, and added sending an email to our system-admin when a (wet-lab) admin job errors.


Version 2023.05
---------------

**_NOTE:_** Human-associated shotgun samples have been determined to leak human
DNA, even with state of the art human read filtering mechanisms in place. To
address this critical privacy concern as soon as possible, we are limiting
per-sample FASTQ downloads to admins and study owners for human-associated
shotgun samples, and in parallel we are (a) working with EBI-ENA to address
submitted data and (b) updating Qiita to only allow download of sequence data
that positively matches to a microbial specific database.

* Added "Artifact.has_human" to check if an artifact has samples that can potentially contain human sequences.


Version 2023.03
---------------

* Added "Sample Validation" for all Admin levels.
* Tools and Plugins can add preparation information via the endpoint: `/qiita_db/prep_template/`.
* Users can now access specific preparations via the URL by adding it as a parameter: `/study/description/<study_id>?prep_id=<prep_id>`.
* The internal [Sequence Processing Pipeline](https://github.com/qiita-spots/qp-knight-lab-processing) now automatically inserts new BLANKs to the sample information file, adds the preparation information file to Qiita, and keeps a record of which preparations were inserted to which studies.
* Added the possibility of processing BIOM artifacts in the processing pipeline.
* Added qiime2.2023.2 to the system; which updated these plugins: qp-qiime2, qtp-biom, qtp-diversity, qtp-visualization.
* Added q2-greengeenes2 to the system, specifically actions: `filter_features` and `non_v4_16s`. This is the first processing (vs. analysis) plugin added to the system.
* Fixed the [diversity pcoa_biplot](https://github.com/qiita-spots/qiita/issues/3266) functionality and added the [emperor biplot](https://github.com/qiita-spots/qiita/issues/3255) action.
* The system can now validate QIIME 2 `FeatureData[Sequences]` via `qtp-diversity`.
* Fixed the following issues [#3249](https://github.com/qiita-spots/qiita/issues/3249), [#3264](https://github.com/qiita-spots/qiita/issues/3264), [#3245](https://github.com/qiita-spots/qiita/issues/3245), [#3243](https://github.com/qiita-spots/qiita/issues/3243).

Version 2023.02
---------------

* Added "Software and Data Licensing" to the Qiita FAQ page.
* External resources can now add new sample metadata categories to a study via
the `/api/v1/study/` endpoint.
* Added preparation-id to the GUI list of artifacts used in an analysis.
* Added automatic lower-casing to INSDC null values [#3246](https://github.com/qiita-spots/qiita/issues/3246).
* ArtifactHandler now returns the file size and full path of the files available in
an Artifact. This change had two consequences: (1) the plugins now can control
their behavior based on the file sizes, and (2) all plugins had to be updated to use this new feature.
* Added [qiita_client.artifact_and_preparation_files](https://github.com/qiita-spots/qiita_client)
to help plugins filter per_sample_FASTQ based on size and ignore small file sizes.
* Added qiime2.2022.11 to the system; which updated these plugins: qp-qiime2, qtp-biom, qtp-diversity, qtp-visualization.
* Added q2-mislabeled and composition's ancom to the qiime2.2022.11 deployment.
* Added support for Amplicon data to the internal [Sequence Processing Pipeline](https://github.com/qiita-spots/qp-knight-lab-processing).


Version 2022.11
---------------

* Adding new Woltka v0.1.4 and WoLr2 - WoLr1 and RS210 (updated version of rep200) are available but not default.
* Update qp-woltka so it runs faster, contribution with @wasade. Add newest improvements for woltka processing so it runs faster.
* Fix qp-qiime2, "filter features" bug that expects a "feature metadata" value from the dropdown.
* Avoid having [multiple git version](https://github.com/qiita-spots/qiita/issues/3216) commands running in the system - this in theory should fix some of the slow downs.
* Fix sample_name in per preparation sample information files.
* Now the sequencing artifacts (like per-sample-FASTQ, FASTA, etc) accept log files.
* SortMeRNA via qp-meta will generate processing logs and will be added to their artifacts - note that this will only be available in newer runs AKA you can delete the outputs of past runs and rerun it.
* Added new "Admin Sample Validation" to validate a list of sample names against what's available in a study, contributed by @sarayupai.

Version 2022.09
---------------

* Moved Qiita's code base and plugins to SLURM (from Torque). The plugins updated are: qiita-spots/qp-woltka, biocore/mg-scripts, qiita-spots/qp-spades, qiita-spots/qp-meta, qiita-spots/qp-fastp-minimap2.
* Pinned the paramiko version to < 2.9 [as newer versions were causing issues with older systems](https://github.com/paramiko/paramiko/issues/1961#issuecomment-1008119073).
* Pinned the scipy version to < 1.8 to avoid issues with the biom-format library.
* Updates to the INSTALL instructions (thank you @aliu104 !)

Version 2022.07
---------------

* Users can opt-in to get emails when their jobs change status in their User Information preferences.
* Added BIOM artifact archiving to the system; this unlinks artifacts from the main processing but leaves them in the system in case they are needed in the future.
* Added [qiime2.2022.02](https://github.com/qiita-spots/qp-qiime2/pull/68) to the system; which updated these plugins: qp-qiime2, qtp-biom, qtp-diversity, qtp-visualization
* Users can now select multiple artifacts for analysis [qp-qiime2](https://github.com/qiita-spots/qp-qiime2/pull/69), which gives access to new commands like PCoA biplots.
* [qtp-sequencing](https://github.com/qiita-spots/qtp-sequencing/pull/41/files) now uses fqtools to count the number of sequences in fastq/fastq.gz files as part as the artifact summary.
* Artifact summaries can now be updated [qiita-spots #3205](https://github.com/qiita-spots/qiita/pull/3205).
* Added to the internal [Sequence Processing Pipeline](https://github.com/qiita-spots/qp-knight-lab-processing) the CHM13 genome so human studies are now filtered by GRCh38 genome + PhiX and CHM13 genome.

Version 2022.05
-----------------

* Added `Artifact.iter()` for easier Artifact interactions.
* Fixed the SCP Qiita transfer; [this was the problem and solution](https://github.com/paramiko/paramiko/issues/1961).
* Added `User.email` to the Admin Job Processing listing.

Version 2022.04
---------------

* Moved from Python 3.6 to 3.9.
* Added support for Pandas 1.4.0, [details here](https://github.com/qiita-spots/qiita/pull/3174).
* Updated all available JavaScript libraries, [details here](https://github.com/qiita-spots/qiita/pull/3177).
* Users can select which metadata to use when creating a new analysis. By default only overlapping metadata in all studies is selected.
* Now we can fully delete users in the backend.
* Updated documentation to reflect the new EMPO version 2.
* Fixed outstanding issues to add default workflow to a preparation, [details here](https://github.com/qiita-spots/qiita/issues/3158).
* Fixed the following issues: [3183](https://github.com/qiita-spots/qiita/issues/3183), [3182](https://github.com/qiita-spots/qiita/issues/3182), [3170](https://github.com/qiita-spots/qiita/issues/3170), [3193](https://github.com/qiita-spots/qiita/pull/3193).
* We deprecated the use of specimen_id from Qiita; this is no longer required in the backend or the GUI.
* Moved [qp-fastp-minimap2](https://github.com/qiita-spots/qp-fastp-minimap2/) to per sample parallelization. Now an iSeq processing takes ~20min, while before it took close to 2hrs.
* Fixed the following issues [qp-knight-lab-processing #15](https://github.com/qiita-spots/qp-knight-lab-processing/issues/15), [qp-knight-lab-processing #16](https://github.com/qiita-spots/qp-knight-lab-processing/issues/16), [qp-knight-lab-processing #17](https://github.com/qiita-spots/qp-knight-lab-processing/issues/17), [qp-knight-lab-processing #19](https://github.com/qiita-spots/qp-knight-lab-processing/issues/19), [mg-scripts #60](https://github.com/biocore/mg-scripts/issues/60), [mg-scripts #62](https://github.com/biocore/mg-scripts/issues/62) from the [Knight Lab Sequence Processing Pipeline](https://github.com/qiita-spots/qp-knight-lab-processing).


Version 2021.11
---------------

* Upgrading PostgreSQL from 9.5 to 13.4 as 9.5 is no longer supported
* Updated SortMeRNA within qt-meta to filter RNA reads to run as job arrays to speed up processing. A full NovaSeq run will now take ~15hrs vs. ~161hrs.
* Added qiime2.2021.11 to the system; which updated these plugins: qp-qiime2, qtp-biom, qtp-diversity, qtp-visualization.
* Jobs no longer need to be linked to studies or analyses; this allows us to create general purpose jobs like "admin like" jobs that can be fully traced in Qiita.
* Added a new user level: "wet-lab admin" so they can start "admin like" jobs in the system without having to be an actual admin.
* Added a new plugin: "qp-knight-lab-processing" that provides the general Knight Lab sequence processing: from BCL to per_sample_FASTQ to the upload folders in Qiita.
* Added "Oxford_Nanopore" as a valid "platform" with "GridION" as valid "instrument_model" to the system; this allows submission of this data to EBI-ENA.
* Allow chucked download of metadata files in analyses; this allows to process large meta-analysis (like those for The Microsetta Initiative) without worker blockage.
* Added to the qp-qiime2 plugin the possibility of filtering tables based on system available "FeatureData[Sequence]"; to start we added 90/100/150 bps bloom tables.
* Now we can instantiate a study via their title (Study.from_title); this will facilitate orchestration with qebil.
* Speed up Study listing for admins and general users; the admin study display came down from 20 to 2 seconds.
* Fixed the following issues: [3142](https://github.com/qiita-spots/qiita/issues/3142), [3149](https://github.com/qiita-spots/qiita/issues/3149), [3150](https://github.com/qiita-spots/qiita/issues/3150), [3119](https://github.com/qiita-spots/qiita/issues/3119), and [3160](https://github.com/qiita-spots/qiita/issues/3160).


Version 2021.09
---------------

* Updated the qp-deblur plugin to version 2021.09 addressing a bug in fragment insertion parsing and caching; [more information](https://qiita.ucsd.edu/static/doc/html/processingdata/deblur_2021.09.html).
* Double the number of possible connections for the Qiita database: 100 -> 200 simultaneous connections.
* Added a new data type: "Job Output Folder" and artifact type definition: "job-output-folder" to initially support admin-only standalone commands in Qiita.
* The study listing is now sorted by descending study id and then ascending number of available artifacts.
* Removed old code from the Sample Information update method that regenerated all preparations in that study - this is no longer necessary as the per preparation sample information files are built on the fly.
* Fixed a bug that did not copy the raw files when adding a new artifact via the CLI.
* Fixed the following issues: [#3124](https://github.com/qiita-spots/qiita/issues/3124), [#3122](https://github.com/qiita-spots/qiita/issues/3122), [#3134](https://github.com/qiita-spots/qiita/issues/3134).


Version 2021.07
---------------

* Added a new "Add Default Workflow" button to the preparation tab so we automatically add all the "recommended" steps in a preparation based on our workflows.
* New Preparation Listing GUI + searching within preparation types, thank you @AmandaBirmingham!
* We limit the parameters displayed to the user per command based on which have already been run successfully; for example if a preparation has already a "Trim 100" job, this option will not be shown.
* Re-added Coveralls to Qiita and removed codecov.
* We are limiting the number of samples in a [preparation file to 800](https://qiita.ucsd.edu/static/doc/html/faq.html#how-should-i-split-my-samples-within-preparations).
* Added User.update_email which allows to update a Users email.
* Fixed the following issues: [#3113](https://github.com/qiita-spots/qiita/issues/3113), and [#3079](https://github.com/qiita-spots/qiita/issues/3079).

Version 2021.05
---------------

* Replaced vis.js for cytoscape.js to display the processing networks.
* The commands available to users, originally only filtered by input type, are now also limited by the preparation type. The options are taken from the [recommended workflows](https://qiita.ucsd.edu/workflows/).
* Added a new [spades](https://github.com/ablab/spades) assembly pipeline for "Genome Isolate".
* Fixed the following issues: [#3070](https://github.com/qiita-spots/qiita/issues/3070), [#3089](https://github.com/qiita-spots/qiita/issues/3089), [#2968](https://github.com/qiita-spots/qiita/issues/2968), [#3102](https://github.com/qiita-spots/qiita/issues/3102), and [#3079](https://github.com/qiita-spots/qiita/issues/3079).

Version 2021.03
---------------

* Fixed [issue](https://github.com/qiita-spots/qtp-target-gene/issues/32) that left behind non gz per sample FASTQ files.
* [Recommended Workflows](https://qiita-rc.ucsd.edu/workflows/) are now stored in the database.
* Added a new button only for owners and admins within the Study page to display a list of all the Analyses generated with that study; helpful to clean up Studies and for general information.
* The Qiita CI now runs as [GitHub Actions](https://github.com/qiita-spots/qiita/actions); moving away from Travis CI.
* Prep information file object now stores its creation and modification timestamps.
* Improved creation time for all information files via the to_dataframe() method.
* Split the "other" category of the storage stats plot (https://qiita.ucsd.edu/stats/) into "other" and "biom" so biom can be its own category.
* Added a processing_jobs property to qiita_db.software.Command to easily retrieve all jobs in the system that have ran the given command.
* Fixed the following issues: [#3068](https://github.com/qiita-spots/qiita/issues/3068), [#3072](https://github.com/qiita-spots/qiita/issues/3072), [#3076](https://github.com/qiita-spots/qiita/issues/3076), and [#3070](https://github.com/qiita-spots/qiita/issues/3070).

Version 2021.01
---------------

* Moved the qiita repo from biocore to [qiita-spots](https://github.com/qiita-spots/qiita/).
* Created the [Qiita portal for the Cancer Microbiome](https://qiita.ucsd.edu/cancer/).
* The EBI-ENA code now verifies that the sample information file has a description column; this wasn't previously required because it was automatically prefilled by the QIIME 1 mapping file.
* Now it is possible to download the per preparation sample information file and the sample-preparation summary.
* Added a faster metagenomic/metatranscriptomic adaptor and host removal step based on fastp and minimap2. The previous version, using atropos and bowtie2 for QC host filtering, is now deprecated.
* Added qiime2.2020.11 to the system; which updated these plugins: qp-qiime2, qtp-biom, qtp-diversity, qtp-visualization.
* Added [WoL](https://biocore.github.io/wol/) tree for phylogenetic analyses (/projects/wol/release/databases/qiime2/phylogeny.qza) with per-genome WoL artifacts.
* Fixed the following issues: [#3060](https://github.com/qiita-spots/qiita/issues/3060), [#3049](https://github.com/qiita-spots/qiita/issues/3049), and [#2751](https://github.com/qiita-spots/qiita/issues/2751).

Version 2020.11
---------------

* Deprecated the automatic creation of the per template QIIME1 mapping file. If you want to merge a preparation and a BIOM table you must first create a meta-analysis.
* Added a new autoloaded boolean flag to the Study object so we can control if a study was autoloaded via an automatic EBI-ENA or SRA loading job.
* We stopped adding the CRC32 information from mod_zip, which should remove the warnings about CRC incorrect checksums.
* Removed the show/hide button from an analysis while the analysis was being built to avoid possible confusion.
* A new per-sample, fast, bowtie2 and Woltka plugin for WGS and Metatrascriptomics processing has been added, deprecating the Shogun plugin and moving the rest of the commands to a new qp-meta plugin.
* Added the possibility for plugins to submit and control their own jobs vs. Qiita automatically submitting for them. For specifics of this new functionality, visit (![#3040](https://github.com/biocore/qiita/pull/3040/files))
* We increased the number of workers in qiita.ucsd.edu for the web interface (from eight to twenty), redbiom (from eight to ten), and the plugin interactions (from eight to twenty). This should speed up responses and improve general performance.
* For the qp-qiime2 plugin, we removed some unsupported alpha rarefaction metrics from the options, following QIIME2 guidelines.
* For the qp-qiime2 plugin, if the user selects a tree but it doesn't exist, it will not try to parse and skip it.

Version 092020
--------------

* Added a new endpoint to inject artifacts to existing preparations or jobs: `/qiita_db/artifact/`
* Outdated commands with the exact same name than newer commands will be marked as not outdated. This is helpful for cases where the commands haven't changed between version
* Added the `add_ebi_accessions` to the `to_dataframe()` method of the information files so it can be used to `redbiom`. This will allow searching via sample or experiment accessions
* Added the `release_validator_job` method to `ProcessingJob` method to easily retrieve the `release_validator` job of a `processing_job`
* Re-added `STUDY_TYPE` to the EBI-ENA submission as they are required but deprecated so just adding as Other
* Added qiime2.2020.08 to the system; which updated these plugins: qp-qiime2, qtp-biom, qtp-diversity, qtp-visualization
* Shogun processing using Woltka will now produce 2 extra artifacts: a per genome and per gene artifacts

Version 072020
--------------

* Added per preparation LIBRARY_STRATEGY and removed the study wide STUDY_TYPE values for EBI-ENA submissions to comply with newer metadata standards
* Changed `Ion Torrent` to `Ion_Torrent` as described by EBI-ENA
* Added a VALIDATOR job_type to be able to specify job validator resources
* Added a job.shape method that returns the number of columns, samples and input size of each job based its input artifacts
* Added the possibility of requesting memory resources for a job based on the input size, number of samples and/or columns
* Warnings from commands will only use the message part of the warning/errors (#2898)
* Fixed error when deleting multiple artifacts with summaries and support_files
* Button now will be disabled when submitting a workflow via GUI to avoid double clicking from users
* Jobs will now display their "external job id" to users, in practice their barnacle job id
* Fixed bug that prevented delete of full analyses when the processing tree had multiple paths
* Added initial script for nightly auto-processing of workflows
* Removed legacy future dependencies from Python2.7
* Users can see the available system plugins, their commands and resource allocations: https://qiita.ucsd.edu/software/
* Added qiime2.2020.06 to the system; which updated these plugins: qp-qiime2, qtp-biom, qtp-diversity, qtp-visualization
* Shogun v1.0.8 for Metagenomic and Metatrascriptomics processing; this new version includes bowtie2 v2.4.1 as aligner and [Web of Life](https://biocore.github.io/wol/) and [rep200](ftp://ftp.ncbi.nlm.nih.gov/refseq/release/).

Version 052020
--------------

* Added Metatrascriptomics as a data type, added a Ribosomal read filtering step and documentation on how to use it in the processing recommendations
* Fixed issue that prevented creating new artifacts when it was the children of a public parent
* Qiita now keeps track of artifact deletion jobs, prevents submitting duplicated deletions, and the GUI is updated when an artifact is being deleted
* We now display the `redbiom` DB release date in the redbiom Qiita page
* Fixed EBA-ENA duplicated sample submission in multiple preparations - this could happen when a sample existed in more than one preparation
* Add the ability to deprecate a preparation; this is useful when there is an unsuccessful run or preparation
* The study page now has a markdown `Notes` section so users add problematic samples, explaining certain metadata columns, etc
* Added user documentation to better explain how to split your samples in preparations
* Fix a bug where repeated sample names were incorrectly handled during meta-analysis (#2978). Removed unused-legacy code to deal with duplicated sample names while building analyses
* Improved headings in the stats page to avoid confusions
* Fixed issue that only deleted selected samples within the page's viewing frame
* Qiita now uses `gnu=True` in the `humanize.naturalsize` so the size display matches what a user sees when they `ls` the file
* Updated code so it works with `pandas v1.0.3`
* Added qiime2.2020.02 to the system; which updated these plugins: qp-qiime2, qtp-biom, qtp-diversity, qtp-visualization

Version 012020
--------------

* Fixed issues with adding sample information files directly to the study and skipping the upload folder
* Added the option to generate unique URL (per artifact) for sandboxed or private studies; see https://qiita.ucsd.edu/static/doc/html/downloading.html
* Added the possibility of just downloading sample or preparation information files
* Updated vis.js and vis-network.js to version 6.5.2; this fixed some network display issues
* Deployed Atropos v1.1.24 and Shogun v1.0.7 for Metagenomic processing; this new version includes bowtie2 v2.3.5, burst15 v0.99.8 and utree v2.0RF as aligners and [Web of Life](https://biocore.github.io/wol/) and [rep94](ftp://ftp.ncbi.nlm.nih.gov/refseq/release/) ([more info](https://github.com/knights-lab/BURST/blob/master/bin/README.md) on processing) as databases

Version 112019
--------------

* Added PacBio_SMRT to the list of platform and PacBio RS, PacBio RS II, Sequel, Sequel II as valid instrument models
* Improved downloads for public data (BIOM, raw data, etc.; see https://qiita.ucsd.edu/static/doc/html/downloading.html)
* Added the possibility of just downloading sample or preparation information files
* During a meta-analysis if `sample_name` and `sample_id`/`sample-id` are present, Qiita will drop the columns `sample_id`/`sample-id` to avoid issues with QIIME2
* The redbiom webpage only accepts ' or " for escaping strings
* Added qiime2.2019.10 to the system; which updated these plugins: qp-qiime2, qtp-biom, qtp-diversity, qtp-visualization

Version 092019
--------------

* Improved stats Qiita page
* Fixed Glossary Terms in Help pages (thanks, @JTFouquier)
* Fixed redbiom Help pages that prevented from copy/pasting examples
* Fixed broken code that prevented downloading biom/archive releases
* Added new public page for study and artifact summaries
* qtp-target-gene validates that the input files are not empty (for example FASTQ)

Version 072019
--------------

* Fixed annoying bugs due to Python 2->3 conversion: https://github.com/biocore/qiita/issues/2901
* Created a new all/per-data-type raw/biom endpoint; see FAQs in help page
* Added a new button to reconcile sample and prep info files within study (delete all samples in the sample information file that has no preparation)
* Fixed but where trying to delete multiple samples within the sample information file will fail

Version 042019
--------------

* Qiita code and Travis builds have been moved to Python 3.6, we no longer support 2.7 and use the Xenial distribution
* Qiita relies on the latest versions of all its dependencies
* Fixed bug preventing to just update values within a Sample Information file: https://github.com/biocore/qiita/issues/2806
* Analyses now display the artifact and processing information that were used to create it
* Study listing now shows preparation type and allows to filter by it
* Fixed bug preventing deletion of multiple artifacts at once: https://github.com/biocore/qiita/issues/2734
* Analysis metadata will have the artifact id in the `qiita_artifact_id` column
* Adding new samples to a sample information file will only regenerate prep info files that have them; if no overlap, nothing will be generated except sample information file
* In Travis, we now generate a real configuration file for the BIOM plugin (needed for analysis testing) vs. having it hardcoded
* Qiita now can be ran via supervisord, which is being used in Travis together with nginx for regular testing
* redbiom in Qiita only works with main site; portal redirect to main site
* Qiita now stores QZA (Qiime Zip Artifacts) as part of the artifacts and they are used as input when present; this provides Qiime2 provenance and references for those artifacts
* Removed legacy SQLConnectionHandler code and moved everything to the TRN method
* Removed emp_person and number_samples_promised as study requirements
* We only show the "Request approval" button starting on the second artifact in the processing, preventing users to request revision of unprocessed data
* "Request approval" will send an email to qiita.help@gmail.com so we can keep better track of these requests
* All single filepaths in Qiita now display their CRC32 and file size
* Artifact id is now prepended to the downloaded filepaths
* Large download will resume using nginx/mod_zip CRC32 features
* Sample information files can be uploaded/updated directly from the Sample Information page
* Qiime2 reserved sample/feature id column names are not allowed in information files
* New table and restrictions were added to Qiita's sample and prep info files. See new documentation for details
* Added Qiime2 2019.4.0

Version 012019
--------------

* Updated PostgreSQL from 9.3 to 9.5
* Information files storage is now jsonb key-value pairs
* Improved sample insertion by only updating the preparation information files that overlap with the updated/new samples
* Qiita uses the latests redbiom (0.3.0)
* Solved Qiita-redbiom issue where it returned all artifacts (https://github.com/biocore/qiita/issues/2569)
* Deleting an artifact will delete its children
* Map in the stats section only uses public data and shows the study id of the sample
* Added functionality to do archiving release; for example: full Qiita deblur trees
* Improved job submission and tracking; new cool things to come!
* IonTorrent EBI-ENA submission is available
* Fixed and not allowing special chars for PI names
* Help section now has a new Meta-Analyses Help & EBI-ENA submission checklist
* The "Download public BIOM and metadata files" now includes software version, target_gene, platform and merging scheme for the artifacts
* Improved the processing graph display to make it more user friendly: artifacts are triangles and jobs are circles

Version 112018
--------------

* Updated qp-deblur to generate a phylogenetic tree during analysis
* Updated analysis to use the qiime2 2018.11.0
* EBI-ENA submissions will check if the submission XML files are larger
  than 8.5M (EBI-ENA max is 10M), in that case, it will remove columns with
  single values and columns with a single value in all rows, and try again
* EBI-ENA submissions will submit forward and reverse reads for per sample FASTQ
* Users now can make their raw data public for public artifacts
* Replaced Google map for OpenLayers in the stats page
* Stats page now shows the total number of jobs ran in the system
* Changed footer to point to Qiita's publication https://doi.org/10.1038/s41592-018-0141-9
* Allowed xlsx files in the prep info files
* Qiita now allows plugins to run any given command at the end of building
  analyses to generate extra artifacts, for example to generate a deblur tree

Version 092018
--------------

* Study listing performance was improve and now public studies are only shown once for Admins.
* The study listing page used to show all artifacts for public studies, even the private ones, now we show based on their permissions.
* Users now can allow access from Qiita to copy (scp/sftp) their files from their own servers.
* Sample deletion from the sample information file now is done in bulk.
* The Sample-Prep Summary now can be sorted.
* Admins now have a page to check the status of the plugins.
* We now support unique tube identifies for samples, helpful for connections with LIMS systems.
* Resorted the top menus so they are clearer for new users.
* Study titles cannot have special, non UTF-8, chars.
* The password check and reset has been fixed.
* Plugin software now have a new column deprecated to highlight artifacts that were generated with outdated software.
* EBI-ENA submissions was improved by only scanning the samples in the prep information file vs. all samples in the study.
* We now check that the sample information file does not contain regular prep info file columns and that the prep does not have QIIME specific mapping file columns.
* The qtp-target-gene has been updated to support multiple SFF files
* The qp-deblur was updated to use deblur-1.1.0

Version 062018
--------------

* We haven't updated the ChangeLog for a while (since circa 2015). Anyway, we will ask developers to add an entry for any new features in Qiita.
* Now you can select or unselect all files in the upload folder.
* Added circle color explanation in the processing network.
* Fixed error in the sample info category summary (https://github.com/biocore/qiita/issues/2610).
* Qiimp has been added to the Qiita GUI.
* We added the qt-shogun plugin.
* Adding qiita_db.processing_job.ProcessingJob.validator_jobs to remove duplicated code.

Version 0.2.0-dev
-----------------

* Users can now change values and add samples and/or columns to sample and prep templates using the <kbd>Update</kbd> button (see the prep template and sample template tabs).
* The raw files of a RawData can be now updated using the `qiita db update_raw_data` CLI command.
* instrument_model is now a required prep template column for EBI submissions.
* PostgreSQL 9.3.0 is now the minimum required version because we are using the SQL type JSON, included for first time in 9.3.0.
* The objects `RawData`, `PreprocessedData` and `ProcessedData` have been removed from the system and substituted by a general `Artifact` object.
* The CLI commands `load_raw`, `load_preprocessed` and `load_processed` have been removed from the system and substituted by `load_artifact`.
* We incorporated the idea of plugins into the system. Now, all processing could be plugins.
* QIIME workflows for splitting libraries (SFF/FASTA-QUAL and FASTQ/per-sample-FASTQ) and for picking OTUs has been moved to a new target gene plugin.
* An initial RESTapi has been introduced as a result of the plugin system, in which OAuth2 authentication is required to access the data.
* The system has been ported to use HTTPS instead of HTTP.
* The website now supports Mozilla Firefox 48 and above.

Version 0.2.0 (2015-08-25)
--------------------------

* Creating an empty RawData is no longer needed in order to add a PrepTemplate.
Now, the PrepTemplate is required in order to add a RawData to a study. This is
the normal flow of a study, as the PrepTemplate information is usually
available before the RawData information is available.
* A user can upload a QIIME mapping file instead of a SampleTemplate. The
system will create a SampleTemplate and a PrepTemplate from the information
present in the QIIME mapping file. The QIIME required columns for this
functionality to work are 'BarcodeSequence', 'LinkerPrimerSequence' and
'Description'. For more information about QIIME mapping files, visit
http://qiime.org/documentation/file_formats.html#mapping-file-overview.
* The command line interface has been reorganized:
 * `qiita_env` has been renamed `qiita-env`
 * `qiita_test_install` has been renamed `qiita-test-install`
 * `qiita ebi` has been moved to `qiita ware ebi`
 * `qiita log` has been moved to `qiita maintenance log`
 * A new `qiita pet` command subgroup has been created
 * `qiita webserver` has been moved to `qiita pet webserver`
* Cluster names now use dashes instead of underscores (e.g., `qiita_general` is now `qiita-general`)
* `qiita-general` is now used as a default argument to `qiita-env start_cluster` and `qiita-env stop_cluster` if no cluster name is specified
* Qiita now now allows for processing of already demultiplexed data without any technical (barcode and primer) section of the read.
* Qiita now includes full portal support, limiting study and analysis access at below the qiita_db level. This allows one database to act as if subsets of studies/analyses are their own specific interface. Commands added for portals creation and maintenance, under `qiita db portal ...` and `qiita-env`. Portal specific web user interface support has also been added; each portal is fully CSS customizable.
* 403 errors are now not logged in the logging table
* Qiita will execute all DB interactions in transactions. The queue code was moved and improved from SQLConnectionHandler to a new Transaction object. The system implements the singleton pattern. That is, there is only a single transaction in the system, represented by the variable `TRN`, and all DB interactions go through it.

Version 0.1.0 (2015-04-30)
--------------------------

Initial alpha release.
