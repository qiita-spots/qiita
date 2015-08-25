# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from os.path import join, isdir
from os import makedirs, remove
from functools import partial
from tempfile import mkdtemp
from gzip import open as gzopen
from tarfile import open as taropen
from moi.job import system_call

from qiita_db.study import Study
from qiita_db.data import PreprocessedData
from qiita_db.metadata_template import PrepTemplate, SampleTemplate
from qiita_core.qiita_settings import qiita_config

from qiita_ware.ebi import EBISubmission
from qiita_ware.demux import to_per_sample_ascii
from qiita_ware.exceptions import ComputeError
from qiita_ware.util import open_file


def submit_EBI(preprocessed_data_id, action, send, fastq_dir_fp=None):
    """Submit a preprocessed data to EBI

    Parameters
    ----------
    preprocessed_data_id : int
        The preprocesssed data id
    action : %s
        The action to perform with this data
    send : bool
        True to actually send the files
    fastq_dir_fp : str, optional
        The fastq filepath

    Notes
    -----
    If fastq_dir_fp is passed, it must not contain any empty files, or
    gzipped empty files
    """

    preprocessed_data = PreprocessedData(preprocessed_data_id)
    preprocessed_data_id_str = str(preprocessed_data_id)
    study = Study(preprocessed_data.study)
    sample_template = SampleTemplate(study.sample_template)
    prep_template = PrepTemplate(preprocessed_data.prep_template)

    investigation_type = None
    new_investigation_type = None

    if send:
        # If we intend actually to send the files, then change the status in
        # the database
        preprocessed_data.update_insdc_status('submitting')

    if fastq_dir_fp is not None:
        # If the user specifies a FASTQ directory, use it

        # Set demux_samples to None so that MetadataTemplate.to_file will put
        # all samples in the template files
        demux_samples = None
    else:
        # If the user does not specify a FASTQ directory, create one and
        # re-serialize the per-sample FASTQs from the demux file
        fastq_dir_fp = mkdtemp(prefix=qiita_config.working_dir)
        demux = [path for _, path, ftype in preprocessed_data.get_filepaths()
                 if ftype == 'preprocessed_demux'][0]

        # Keep track of which files were actually in the demux file so that we
        # can write those rows to the prep and samples templates
        demux_samples = set()

        with open_file(demux) as demux_fh:
            for samp, iterator in to_per_sample_ascii(demux_fh,
                                                      list(sample_template)):
                demux_samples.add(samp)
                sample_fp = join(fastq_dir_fp, "%s.fastq.gz" % samp)
                wrote_sequences = False
                with gzopen(sample_fp, 'w') as fh:
                    for record in iterator:
                        fh.write(record)
                        wrote_sequences = True

                if not wrote_sequences:
                    remove(sample_fp)

    output_dir = fastq_dir_fp + '_submission'

    samp_fp = join(fastq_dir_fp, 'sample_metadata.txt')
    prep_fp = join(fastq_dir_fp, 'prep_metadata.txt')

    sample_template.to_file(samp_fp, demux_samples)
    prep_template.to_file(prep_fp, demux_samples)

    # Get specific output directory and set filepaths
    get_output_fp = partial(join, output_dir)
    study_fp = get_output_fp('study.xml')
    sample_fp = get_output_fp('sample.xml')
    experiment_fp = get_output_fp('experiment.xml')
    run_fp = get_output_fp('run.xml')
    submission_fp = get_output_fp('submission.xml')

    if not isdir(output_dir):
        makedirs(output_dir)
    else:
        raise IOError('The output folder already exists: %s' %
                      output_dir)

    with open(samp_fp, 'U') as st, open(prep_fp, 'U') as pt:
        submission = EBISubmission.from_templates_and_per_sample_fastqs(
            preprocessed_data_id_str, study.title,
            study.info['study_abstract'], investigation_type, st, pt,
            fastq_dir_fp, new_investigation_type=new_investigation_type,
            pmids=study.pmids)

    submission.write_all_xml_files(study_fp, sample_fp, experiment_fp, run_fp,
                                   submission_fp, action)

    if send:
        submission.send_sequences()
        study_accession, submission_accession = submission.send_xml()

        if study_accession is None or submission_accession is None:
            preprocessed_data.update_insdc_status('failed')

            raise ComputeError("EBI Submission failed!")
        else:
            preprocessed_data.update_insdc_status('success', study_accession,
                                                  submission_accession)
    else:
        study_accession, submission_accession = None, None

    return study_accession, submission_accession


def submit_VAMPS(preprocessed_data_id):
    """Submit preprocessed data to VAMPS

    Parameters
    ----------
    preprocessed_data_id : int
        The preprocesssed data id
    """
    preprocessed_data = PreprocessedData(preprocessed_data_id)
    study = Study(preprocessed_data.study)
    sample_template = SampleTemplate(study.sample_template)
    prep_template = PrepTemplate(preprocessed_data.prep_template)

    status = preprocessed_data.submitted_to_vamps_status()
    if status in ('submitting', 'success'):
        raise ValueError("Cannot resubmit! Current status is: %s" % status)

        preprocessed_data.update_vamps_status('submitting')

    # Generating a tgz
    targz_folder = mkdtemp(prefix=qiita_config.working_dir)
    targz_fp = join(targz_folder, '%d_%d_%d.tgz' % (study.id,
                                                    prep_template.id,
                                                    preprocessed_data.id))
    targz = taropen(targz_fp, mode='w:gz')

    # adding sample/prep
    samp_fp = join(targz_folder, 'sample_metadata.txt')
    sample_template.to_file(samp_fp)
    targz.add(samp_fp, arcname='sample_metadata.txt')
    prep_fp = join(targz_folder, 'prep_metadata.txt')
    prep_template.to_file(prep_fp)
    targz.add(prep_fp, arcname='prep_metadata.txt')

    # adding preprocessed data
    for _, fp, fp_type in preprocessed_data.get_filepaths():
        if fp_type == 'preprocessed_fasta':
            targz.add(fp, arcname='preprocessed_fasta.fna')

    targz.close()

    # submitting
    cmd = ("curl -F user=%s -F pass='%s' -F uploadFile=@%s -F "
           "press=UploadFile %s" % (qiita_config.vamps_user,
                                    qiita_config.vamps_pass,
                                    targz_fp,
                                    qiita_config.vamps_url))
    obs, _, _ = system_call(cmd)

    exp = ("<html>\n<head>\n<title>Process Uploaded File</title>\n</head>\n"
           "<body>\n</body>\n</html>")

    if obs != exp:
        preprocessed_data.update_vamps_status('failure')
        return False
    else:
        preprocessed_data.update_vamps_status('success')
        return True
