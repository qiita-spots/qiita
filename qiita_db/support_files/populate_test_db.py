from functools import partial
from os.path import join
from shutil import copyfile

from qiita_db.user import User
from qiita_db.study import StudyPerson, Study
from qiita_db.util import get_mountpoint
from qiita_db.metadata_template.util import load_template_to_dataframe
from qiita_db.metadata_template.prep_template import PrepTemplate
from qiita_db.metadata_template.sample_template import SampleTemplate
from qiita_db.artifact import Artifact
from qiita_db.software import Parameters, Command
from qiita_db.processing_job import ProcessingJob
from qiita_db.analysis import Analysis

#
# Creating users
#

user_test = User.create('test@foo.bar', 'password', {
    'name': 'Dude',
    'affiliation': 'Nowhere University',
    'address': '123 fake st, Apt 0, Faketown, CO 80302',
    'phone': '111-222-3344'})
user_test.level = 'user'
user_share = User.create('shared@foo.bar', 'password', {
    'name': 'Shared',
    'affiliation': 'Nowhere University',
    'address': '123 fake st, Apt 0, Faketown, CO 80302',
    'phone': '111-222-3344'})
user_share.level = 'superuser'
user = User.create('admin@foo.bar', 'password', {
    'name': 'Admin',
    'affiliation': 'Owner University',
    'address': '312 noname st, Apt K, Nonexistantown, CO 80302',
    'phone': '222-444-6789'})
user.level = 'admin'
user = User.create('demo@microbio.me', 'password', {
    'name': 'Demo',
    'affiliation': 'Qitta Dev',
    'address': '1345 Colorado Avenue',
    'phone': '303-492-1984'})
user.level = 'user'

#
# Creating study person entries
#

StudyPerson.create('LabDude', 'lab_dude@foo.bar', 'knight lab',
                   '123 lab street', '121-222-3333')
StudyPerson.create('empDude', 'emp_dude@foo.bar', 'broad', None,
                   '444-222-3333')
StudyPerson.create('PIDude', 'PI_dude@foo.bar', 'Wash U', '123 PI street')

#
# Adding a new study
#

info = {
    'emp_person_id': 2,
    'first_contact': '2014-05-19 16:10',
    'timeseries_type_id': 1,
    'lab_person_id': 1,
    'metadata_complete': True,
    'mixs_compliant': True,
    'most_recent_contact': '2014-05-19 16:11',
    'number_samples_collected': 27,
    'number_samples_promised': 27,
    'principal_investigator_id': 3,
    'reprocess': False,
    'spatial_series': False,
    'study_alias': 'Cannabis Soils',
    'study_description': 'Analysis of the Cannabis Plant Microbiome',
    'study_abstract': (
        'This is a preliminary study to examine the microbiota associated '
        'with the Cannabis plant. Soils samples from the bulk soil, soil '
        'associated with the roots, and the rhizosphere were extracted and '
        'the DNA sequenced. Roots from three independent plants of different '
        'strains were examined. These roots were obtained November 11, 2011 '
        'from plants that had been harvested in the summer. Future studies '
        'will attempt to analyze the soils and rhizospheres from the same '
        'location at different time points in the plant lifecycle.')}
# [1] is the efo_id
study = Study.create(user_test,
                     'Identification of the Microbiomes for Cannabis Soils',
                     [1],
                     info)
study_id = study.id
study.ebi_study_accession = 'EBI123456-BB'
study.ebi_submission_status = 'submitted'
study.environmental_packages = ['soil', 'plant-associated']
study.share(user_share)
study.publications = [['10.100/123456', '123456'],
                      ['10.100/7891011', '7891011']]

#
# Adding sample and preparation information to our study
#

fp_source = partial(join, get_mountpoint("uploads")[0][1], str(study.id))

sample_info = fp_source('sample_information.txt')
SampleTemplate.create(load_template_to_dataframe(sample_info), study)

preparation_info = fp_source('preparation_information.txt')
# 2 is the data_type_id => 18S
pt = PrepTemplate.create(load_template_to_dataframe(preparation_info),
                         study, 2, 'Metagenomics')
ebi_experiment_values = {
    '1.SKB8.640193': 'ERX0000000', '1.SKD8.640184': 'ERX0000001',
    '1.SKB7.640196': 'ERX0000002', '1.SKM9.640192': 'ERX0000003',
    '1.SKM4.640180': 'ERX0000004', '1.SKM5.640177': 'ERX0000005',
    '1.SKB5.640181': 'ERX0000006', '1.SKD6.640190': 'ERX0000007',
    '1.SKB2.640194': 'ERX0000008', '1.SKD2.640178': 'ERX0000009',
    '1.SKM7.640188': 'ERX0000010', '1.SKB1.640202': 'ERX0000011',
    '1.SKD1.640179': 'ERX0000012', '1.SKD3.640198': 'ERX0000013',
    '1.SKM8.640201': 'ERX0000014', '1.SKM2.640199': 'ERX0000015',
    '1.SKB9.640200': 'ERX0000016', '1.SKD5.640186': 'ERX0000017',
    '1.SKM3.640197': 'ERX0000018', '1.SKD9.640182': 'ERX0000019',
    '1.SKB4.640189': 'ERX0000020', '1.SKD7.640191': 'ERX0000021',
    '1.SKM6.640187': 'ERX0000022', '1.SKD4.640185': 'ERX0000023',
    '1.SKB3.640195': 'ERX0000024', '1.SKB6.640176': 'ERX0000025',
    '1.SKM1.640183': 'ERX0000026'}
pt.ebi_experiment_accession = ebi_experiment_values

#
# Adding artifacts
#

# 1 (Raw fastq) ---> 2 (demultiplexed) ---> 4 (otu table, ref 1)
#                                       \-> 5 (otu table, ref 1)
#                                       \-> 6 (otu table, ref 2)
#                \-> 3 (demultiplexed)

fp = fp_source('raw_data.fastq')
fp_bk = fp_source('raw_data.bk.fastq')
copyfile(fp, fp_bk)
# 1 -> raw_forward_seqs
raw_data = Artifact.create([(fp_bk, 1)], 'FASTQ', 'Raw data 1',
                           prep_template=pt)
raw_data.visibility = 'private'

processing_parameters_vals = {
    "max_bad_run_length": 3,
    "min_per_read_length_fraction": 0.75,
    "sequence_max_n": 0,
    "rev_comp_barcode": False,
    "rev_comp_mapping_barcodes": False,
    "rev_comp": False,
    "phred_quality_threshold": 3,
    "barcode_type": "golay_12",
    "max_barcode_errors": 1.5,
    "input_data": raw_data.id}
fp = fp_source('demux.fna')
fp_bk = fp_source('demux.bk.fna')
copyfile(fp, fp_bk)
params = Parameters.load(Command(1), values_dict=processing_parameters_vals)
pj = ProcessingJob.create(user_test, params)
# 4 -> preprocessed_fasta
demux = Artifact.create([(fp_bk, 4)], 'Demultiplexed', 'Demultiplexed 1',
                        parents=[raw_data], processing_parameters=params,
                        can_be_submitted_to_ebi=True,
                        can_be_submitted_to_vamps=True)
demux.visibility = 'private'

ebi_run_values = {
    '1.SKB1.640202': 'ERR0000001', '1.SKB2.640194': 'ERR0000002',
    '1.SKB3.640195': 'ERR0000003', '1.SKB4.640189': 'ERR0000004',
    '1.SKB5.640181': 'ERR0000005', '1.SKB6.640176': 'ERR0000006',
    '1.SKB7.640196': 'ERR0000007', '1.SKB8.640193': 'ERR0000008',
    '1.SKB9.640200': 'ERR0000009', '1.SKD1.640179': 'ERR0000010',
    '1.SKD2.640178': 'ERR0000011', '1.SKD3.640198': 'ERR0000012',
    '1.SKD4.640185': 'ERR0000013', '1.SKD5.640186': 'ERR0000014',
    '1.SKD6.640190': 'ERR0000015', '1.SKD7.640191': 'ERR0000016',
    '1.SKD8.640184': 'ERR0000017', '1.SKD9.640182': 'ERR0000018',
    '1.SKM1.640183': 'ERR0000019', '1.SKM2.640199': 'ERR0000020',
    '1.SKM3.640197': 'ERR0000021', '1.SKM4.640180': 'ERR0000022',
    '1.SKM5.640177': 'ERR0000023', '1.SKM6.640187': 'ERR0000024',
    '1.SKM7.640188': 'ERR0000025', '1.SKM8.640201': 'ERR0000026',
    '1.SKM9.640192': 'ERR0000027'}
demux.ebi_run_accession = ebi_run_values

processing_parameters_vals = {
    "max_bad_run_length": 3,
    "min_per_read_length_fraction": 0.75,
    "sequence_max_n": 0,
    "rev_comp_barcode": False,
    "rev_comp_mapping_barcodes": True,
    "rev_comp": False,
    "phred_quality_threshold": 3,
    "barcode_type": "golay_12",
    "max_barcode_errors": 1.5,
    "input_data": raw_data.id}
fp = fp_source('demux.fna')
fp_bk = fp_source('demux.bk.fna')
copyfile(fp, fp_bk)
# 4 -> preprocessed_fasta
params = Parameters.load(Command(1), values_dict=processing_parameters_vals)
pj = ProcessingJob.create(user_test, params)
demux_tmp = Artifact.create([(fp_bk, 4)], 'Demultiplexed', 'Demultiplexed 1',
                            parents=[raw_data], processing_parameters=params,
                            can_be_submitted_to_ebi=True,
                            can_be_submitted_to_vamps=True)
demux_tmp.visibility = 'private'

processing_parameters_vals = {
    "reference": 1,
    "sortmerna_e_value": 1,
    "sortmerna_max_pos": 10000,
    "similarity": 0.97,
    "sortmerna_coverage": 0.97,
    "threads": 1,
    "input_data": demux.id}
fp = fp_source('biom_table.biom')
fp_bk = fp_source('biom_table.bk.biom')
copyfile(fp, fp_bk)
# 7 -> biom
params = Parameters.load(Command(3), values_dict=processing_parameters_vals)
pj = ProcessingJob.create(user_test, params)
biom1 = Artifact.create([(fp_bk, 7)], 'BIOM', 'BIOM', parents=[demux],
                        processing_parameters=params)
biom1.visibility = 'private'

processing_parameters_vals = {
    "reference": 1,
    "sortmerna_e_value": 1,
    "sortmerna_max_pos": 10000,
    "similarity": 0.97,
    "sortmerna_coverage": 0.97,
    "threads": 1,
    "input_data": demux.id}
fp = fp_source('biom_table.biom')
fp_bk = fp_source('biom_table.bk.biom')
copyfile(fp, fp_bk)
# 7 -> biom
params = Parameters.load(Command(3), values_dict=processing_parameters_vals)
pj = ProcessingJob.create(user_test, params)
biom2 = Artifact.create([(fp_bk, 7)], 'BIOM', 'BIOM', parents=[demux],
                        processing_parameters=params)
biom2.visibility = 'private'

processing_parameters_vals = {
    "reference": 2,
    "sortmerna_e_value": 1,
    "sortmerna_max_pos": 10000,
    "similarity": 0.97,
    "sortmerna_coverage": 0.97,
    "threads": 1,
    "input_data": demux.id}
fp = fp_source('biom_table.biom')
fp_bk = fp_source('biom_table.bk.biom')
copyfile(fp, fp_bk)
# 7 -> biom
params = Parameters.load(Command(3), values_dict=processing_parameters_vals)
pj = ProcessingJob.create(user_test, params)
biom3 = Artifact.create([(fp_bk, 7)], 'BIOM', 'BIOM', parents=[demux],
                        processing_parameters=params)
biom3.visibility = 'private'

#
# Adding analyses
#

analysis = Analysis.create(user_test, 'SomeAnalysis', 'A test analysis')
to_add = ['%d.%s' % (study_id, s) for s in [
    '1.SKB8.640193', '1.SKD8.640184', '1.SKB7.640196', '1.SKM9.640192',
    '1.SKM4.640180']]
analysis.add_samples({biom1.id: to_add, biom2.id: to_add, biom3.id: to_add})
analysis.pmid = '121112'
analysis.share(user_share)

analysis = Analysis.create(user_test, 'SomeSecondAnalysis',
                           'Another test analysis')
to_add = ['%d.%s' % (study_id, s) for s in [
    '1.SKB8.640193', '1.SKD8.640184', '1.SKB7.640196', '1.SKM3.640197']]
analysis.add_samples({biom1.id: to_add, biom2.id: to_add, biom3.id: to_add})
analysis.pmid = '22221112'
