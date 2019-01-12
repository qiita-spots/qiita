-- January 4, 2019
-- add external_job_id column to record mapping of Torque Job IDs to Qiita Job IDs.
-- COMMENT ON COLUMN qiita.processing_job IS 'Store an external job ID (e.g. Torque job ID) associated this Qiita job.';

ALTER TABLE qiita.processing_job ADD external_job_id varchar;
COMMENT ON COLUMN qiita.processing_job.external_job_id IS 'Store an external job ID (e.g. Torque job ID) associated this Qiita job.';

CREATE TABLE qiita.processing_job_resource_allocation
(
	name	varchar,
	description	varchar,
	type	varchar,
	allocation	varchar
);

insert into qiita.processing_job_resource_allocation (name, description, type, allocation) values ('REGISTER', 'single-core-8gb', 'REGISTER', '-q qiita -l nodes=1:ppn=1 -l pmem=8gb -l walltime=50:00:00');
insert into qiita.processing_job_resource_allocation (name, description, type, allocation) values ('default', 'single-core-8gb', 'RELEASE_VALIDATORS_RESOURCE_PARAM', '-q qiita -l nodes=1:ppn=1 -l pmem=8gb -l walltime=50:00:00');
insert into qiita.processing_job_resource_allocation (name, description, type, allocation) values ('default', 'single-core-8gb', 'COMPLETE_JOBS_RESOURCE_PARAM', '-q qiita -l nodes=1:ppn=1 -l pmem=8gb -l walltime=50:00:00');
insert into qiita.processing_job_resource_allocation (name, description, type, allocation) values ('default', 'multi-core-vlow', 'RESOURCE_PARAMS_COMMAND', '-q qiita -l nodes=1:ppn=5 -l pmem=8gb -l walltime=168:00:00');
insert into qiita.processing_job_resource_allocation (name, description, type, allocation) values ('delete_analysis', 'single-core-8gb', 'RESOURCE_PARAMS_COMMAND', '-q qiita -l nodes=1:ppn=1 -l pmem=8gb -l walltime=50:00:00');
insert into qiita.processing_job_resource_allocation (name, description, type, allocation) values ('Calculate beta correlation', 'single-core-8gb', 'RESOURCE_PARAMS_COMMAND', '-q qiita -l nodes=1:ppn=1 -l pmem=8gb -l walltime=50:00:00');
insert into qiita.processing_job_resource_allocation (name, description, type, allocation) values ('delete_sample_template', 'single-core-8gb', 'RESOURCE_PARAMS_COMMAND', '-q qiita -l nodes=1:ppn=1 -l pmem=8gb -l walltime=50:00:00');
insert into qiita.processing_job_resource_allocation (name, description, type, allocation) values ('delete_study', 'single-core-8gb', 'RESOURCE_PARAMS_COMMAND', '-q qiita -l nodes=1:ppn=1 -l pmem=8gb -l walltime=50:00:00');
insert into qiita.processing_job_resource_allocation (name, description, type, allocation) values ('delete_sample_or_column', 'single-core-8gb', 'RESOURCE_PARAMS_COMMAND', '-q qiita -l nodes=1:ppn=1 -l pmem=8gb -l walltime=50:00:00');
insert into qiita.processing_job_resource_allocation (name, description, type, allocation) values ('create_sample_template', 'single-core-8gb', 'RESOURCE_PARAMS_COMMAND', '-q qiita -l nodes=1:ppn=1 -l pmem=8gb -l walltime=50:00:00');
insert into qiita.processing_job_resource_allocation (name, description, type, allocation) values ('update_prep_template', 'single-core-8gb', 'RESOURCE_PARAMS_COMMAND', '-q qiita -l nodes=1:ppn=1 -l pmem=8gb -l walltime=50:00:00');
insert into qiita.processing_job_resource_allocation (name, description, type, allocation) values ('copy_artifact', 'single-core-8gb', 'RESOURCE_PARAMS_COMMAND', '-q qiita -l nodes=1:ppn=1 -l pmem=8gb -l walltime=50:00:00');
insert into qiita.processing_job_resource_allocation (name, description, type, allocation) values ('delete_artifact', 'single-core-8gb', 'RESOURCE_PARAMS_COMMAND', '-q qiita -l nodes=1:ppn=1 -l pmem=8gb -l walltime=50:00:00');
insert into qiita.processing_job_resource_allocation (name, description, type, allocation) values ('download_remote_files', 'single-core-8gb', 'RESOURCE_PARAMS_COMMAND', '-q qiita -l nodes=1:ppn=1 -l pmem=8gb -l walltime=50:00:00');
insert into qiita.processing_job_resource_allocation (name, description, type, allocation) values ('list_remote_files', 'single-core-8gb', 'RESOURCE_PARAMS_COMMAND', '-q qiita -l nodes=1:ppn=1 -l pmem=8gb -l walltime=50:00:00');
insert into qiita.processing_job_resource_allocation (name, description, type, allocation) values ('submit_to_EBI', 'single-core-8gb', 'RESOURCE_PARAMS_COMMAND', '-q qiita -l nodes=1:ppn=1 -l pmem=8gb -l walltime=50:00:00');
insert into qiita.processing_job_resource_allocation (name, description, type, allocation) values ('Generate HTML summary', 'single-core-8gb', 'RESOURCE_PARAMS_COMMAND', '-q qiita -l nodes=1:ppn=1 -l pmem=8gb -l walltime=50:00:00');
insert into qiita.processing_job_resource_allocation (name, description, type, allocation) values ('update_sample_template', 'single-core-16gb', 'RESOURCE_PARAMS_COMMAND', '-q qiita -l nodes=1:ppn=1 -l mem=16gb -l walltime=10:00:00');
insert into qiita.processing_job_resource_allocation (name, description, type, allocation) values ('build_analysis_files', 'single-core-16gb', 'RESOURCE_PARAMS_COMMAND', '-q qiita -l nodes=1:ppn=1 -l mem=16gb -l walltime=10:00:00');
insert into qiita.processing_job_resource_allocation (name, description, type, allocation) values ('Custom-axis Emperor plot', 'single-core-16gb', 'RESOURCE_PARAMS_COMMAND', '-q qiita -l nodes=1:ppn=1 -l mem=16gb -l walltime=10:00:00');
insert into qiita.processing_job_resource_allocation (name, description, type, allocation) values ('Calculate alpha correlation', 'single-core-16gb', 'RESOURCE_PARAMS_COMMAND', '-q qiita -l nodes=1:ppn=1 -l mem=16gb -l walltime=10:00:00');
insert into qiita.processing_job_resource_allocation (name, description, type, allocation) values ('Summarize taxa', 'single-core-16gb', 'RESOURCE_PARAMS_COMMAND', '-q qiita -l nodes=1:ppn=1 -l mem=16gb -l walltime=10:00:00');
insert into qiita.processing_job_resource_allocation (name, description, type, allocation) values ('Perform Principal Coordinates Analysis (PCoA)', 'single-core-16gb', 'RESOURCE_PARAMS_COMMAND', '-q qiita -l nodes=1:ppn=1 -l mem=16gb -l walltime=10:00:00');
insert into qiita.processing_job_resource_allocation (name, description, type, allocation) values ('Split libraries', 'single-core-56gb', 'RESOURCE_PARAMS_COMMAND', '-q qiita -l nodes=1:ppn=1 -l mem=60gb -l walltime=25:00:00');
insert into qiita.processing_job_resource_allocation (name, description, type, allocation) values ('Calculate alpha diversity', 'single-core-56gb', 'RESOURCE_PARAMS_COMMAND', '-q qiita -l nodes=1:ppn=1 -l mem=60gb -l walltime=25:00:00');
insert into qiita.processing_job_resource_allocation (name, description, type, allocation) values ('Calculate beta diversity', 'single-core-56gb', 'RESOURCE_PARAMS_COMMAND', '-q qiita -l nodes=1:ppn=1 -l mem=60gb -l walltime=25:00:00');
insert into qiita.processing_job_resource_allocation (name, description, type, allocation) values ('Calculate beta group significance', 'single-core-56gb', 'RESOURCE_PARAMS_COMMAND', '-q qiita -l nodes=1:ppn=1 -l mem=60gb -l walltime=25:00:00');
insert into qiita.processing_job_resource_allocation (name, description, type, allocation) values ('Filter samples by metadata', 'single-core-56gb', 'RESOURCE_PARAMS_COMMAND', '-q qiita -l nodes=1:ppn=1 -l mem=60gb -l walltime=25:00:00');
insert into qiita.processing_job_resource_allocation (name, description, type, allocation) values ('Rarefy features', 'single-core-56gb', 'RESOURCE_PARAMS_COMMAND', '-q qiita -l nodes=1:ppn=1 -l mem=60gb -l walltime=25:00:00');
insert into qiita.processing_job_resource_allocation (name, description, type, allocation) values ('Validate', 'single-core-56gb', 'RESOURCE_PARAMS_COMMAND', '-q qiita -l nodes=1:ppn=1 -l mem=60gb -l walltime=25:00:00');
insert into qiita.processing_job_resource_allocation (name, description, type, allocation) values ('Trimming', 'single-core-120gb', 'RESOURCE_PARAMS_COMMAND', '-q qiita -l nodes=1:ppn=1 -l mem=120gb -l walltime=80:00:00');
insert into qiita.processing_job_resource_allocation (name, description, type, allocation) values ('Split libraries FASTQ', 'single-core-120gb', 'RESOURCE_PARAMS_COMMAND', '-q qiita -l nodes=1:ppn=1 -l mem=120gb -l walltime=80:00:00');
insert into qiita.processing_job_resource_allocation (name, description, type, allocation) values ('Deblur', 'multi-core-low', 'RESOURCE_PARAMS_COMMAND', '-q qiita -l nodes=1:ppn=5 -l mem=96gb -l walltime=130:00:00');
insert into qiita.processing_job_resource_allocation (name, description, type, allocation) values ('Shogun', 'multi-core-low', 'RESOURCE_PARAMS_COMMAND', '-q qiita -l nodes=1:ppn=5 -l mem=96gb -l walltime=130:00:00');
insert into qiita.processing_job_resource_allocation (name, description, type, allocation) values ('Pick closed-reference OTUs', 'multi-core-high', 'RESOURCE_PARAMS_COMMAND', '-q qiita -l nodes=1:ppn=5 -l mem=120gb -l walltime=130:00:00');
insert into qiita.processing_job_resource_allocation (name, description, type, allocation) values ('Pick closed-reference OTUs', 'single-core-24gb', 'RELEASE_VALIDATORS_RESOURCE_PARAM', '-q qiita -l nodes=1:ppn=1 -l mem=24gb -l walltime=50:00:00');
insert into qiita.processing_job_resource_allocation (name, description, type, allocation) values ('Trimming', 'single-core-24gb', 'RELEASE_VALIDATORS_RESOURCE_PARAM', '-q qiita -l nodes=1:ppn=1 -l mem=24gb -l walltime=50:00:00');
insert into qiita.processing_job_resource_allocation (name, description, type, allocation) values ('Filter samples by metadata', 'single-core-24gb', 'RELEASE_VALIDATORS_RESOURCE_PARAM', '-q qiita -l nodes=1:ppn=1 -l mem=24gb -l walltime=50:00:00');
insert into qiita.processing_job_resource_allocation (name, description, type, allocation) values ('Rarefy features', 'single-core-24gb', 'RELEASE_VALIDATORS_RESOURCE_PARAM', '-q qiita -l nodes=1:ppn=1 -l mem=24gb -l walltime=50:00:00');
insert into qiita.processing_job_resource_allocation (name, description, type, allocation) values ('BIOM', 'single-core-16gb', 'COMPLETE_JOBS_RESOURCE_PARAM', '-q qiita -l nodes=1:ppn=1 -l mem=16gb -l walltime=10:00:00');
insert into qiita.processing_job_resource_allocation (name, description, type, allocation) values ('alpha_vector', 'single-core-16gb', 'COMPLETE_JOBS_RESOURCE_PARAM', '-q qiita -l nodes=1:ppn=1 -l mem=16gb -l walltime=10:00:00');
insert into qiita.processing_job_resource_allocation (name, description, type, allocation) values ('distance_matrix', 'single-core-16gb', 'COMPLETE_JOBS_RESOURCE_PARAM', '-q qiita -l nodes=1:ppn=1 -l mem=16gb -l walltime=10:00:00');
insert into qiita.processing_job_resource_allocation (name, description, type, allocation) values ('Demultiplexed', 'single-core-16gb', 'COMPLETE_JOBS_RESOURCE_PARAM', '-q qiita -l nodes=1:ppn=1 -l mem=16gb -l walltime=10:00:00');
insert into qiita.processing_job_resource_allocation (name, description, type, allocation) values ('ordination_results', 'single-core-16gb', 'COMPLETE_JOBS_RESOURCE_PARAM', '-q qiita -l nodes=1:ppn=1 -l mem=16gb -l walltime=10:00:00');
insert into qiita.processing_job_resource_allocation (name, description, type, allocation) values ('q2_visualization', 'single-core-16gb', 'COMPLETE_JOBS_RESOURCE_PARAM', '-q qiita -l nodes=1:ppn=1 -l mem=16gb -l walltime=10:00:00');

-- January 11, 2019
-- add general configuration info to store attribute/value pairs that are
-- intended to be mutable during Qiita's operation.
-- alter table settings add column trq_owner varchar;
-- alter table settings add column trq_poll_val int;
-- alter table settings add column trq_dependency_q_cnt int;
