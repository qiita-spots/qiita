# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from os.path import join, isdir
from shutil import rmtree
from tarfile import open as taropen
from tempfile import mkdtemp

from moi.job import system_call
from qiita_db.study import Study
from qiita_db.data import PreprocessedData
from qiita_db.metadata_template import PrepTemplate, SampleTemplate
from qiita_db.logger import LogEntry
from qiita_core.qiita_settings import qiita_config
from qiita_ware.ebi import EBISubmission
from qiita_ware.exceptions import ComputeError
from traceback import format_exc


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
    # step 1: init and validate
    ebi_submission = EBISubmission(preprocessed_data_id, action)

    # step 2: generate demux fastq files
    ebi_submission.preprocessed_data.update_insdc_status('demuxing samples')
    try:
        ebi_submission.generate_demultiplexed_fastq()
    except:
        error_msg = format_exc()
        if isdir(ebi_submission.ebi_dir):
            rmtree(ebi_submission.ebi_dir)
        ebi_submission.preprocessed_data.update_insdc_status(
            'failed: %s' % error_msg)
        LogEntry.create('Runtime', error_msg,
                        info={'ebi_submission': preprocessed_data_id})
        raise

    # step 3: generate and write xml files
    ebi_submission.write_xml_file(ebi_submission.generate_study_xml(),
                                  ebi_submission.study_xml_fp)
    ebi_submission.write_xml_file(ebi_submission.generate_sample_xml(),
                                  ebi_submission.sample_xml_fp)
    ebi_submission.write_xml_file(ebi_submission.generate_experiment_xml(),
                                  ebi_submission.experiment_xml_fp)
    ebi_submission.write_xml_file(ebi_submission.generate_run_xml(),
                                  ebi_submission.run_xml_fp)
    ebi_submission.write_xml_file(ebi_submission.generate_submission_xml(),
                                  ebi_submission.submission_xml_fp)
    if send:
        # step 4: sending sequences
        ebi_submission.send_sequences()

        # step 5: sending xml and retrieving answer
        study_accession, submission_accession = ebi_submission.send_xml()

        if study_accession is None or submission_accession is None:
            ebi_submission.preprocessed_data.update_insdc_status('failed')

            raise ComputeError("EBI Submission failed!")
        else:
            ebi_submission.preprocessed_data.update_insdc_status(
                'success', study_accession, submission_accession)
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
