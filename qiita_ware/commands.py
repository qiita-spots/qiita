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
from os import environ
from traceback import format_exc
from subprocess import call
from shlex import split as shsplit

from moi.job import system_call
from qiita_db.study import Study
from qiita_db.data import PreprocessedData
from qiita_db.metadata_template import PrepTemplate, SampleTemplate
from qiita_db.logger import LogEntry
from qiita_core.qiita_settings import qiita_config
from qiita_ware.ebi import EBISubmission
from qiita_ware.exceptions import ComputeError, EBISubmissionError


def submit_EBI(preprocessed_data_id, action, send):
    """Submit a preprocessed data to EBI

    Parameters
    ----------
    preprocessed_data_id : int
        The preprocesssed data id
    action : %s
        The action to perform with this data
    send : bool
        True to actually send the files
    """
    # step 1: init and validate
    ebi_submission = EBISubmission(preprocessed_data_id, action)

    # step 2: generate demux fastq files
    ebi_submission.study.ebi_submission_status = 'submitting'
    try:
        ebi_submission.generate_demultiplexed_fastq()
    except:
        error_msg = format_exc()
        if isdir(ebi_submission.full_ebi_dir):
            rmtree(ebi_submission.full_ebi_dir)
        ebi_submission.study.ebi_submission_status = 'failed: %s' % error_msg
        LogEntry.create('Runtime', error_msg,
                        info={'ebi_submission': preprocessed_data_id})
        raise

    # step 3: generate and write xml files
    ebi_submission.generate_xml_files()

    if send:
        # step 4: sending sequences
        old_ascp_pass = environ.get('ASPERA_SCP_PASS', '')
        environ['ASPERA_SCP_PASS'] = qiita_config.ebi_seq_xfer_pass

        LogEntry.create('Runtime',
                        ("Submitting sequences for pre_processed_id: "
                         "%d" % preprocessed_data_id))
        for cmd in ebi_submission.generate_send_sequences_cmd():
            cmd_pieces = shsplit(cmd)
            try:
                call(cmd_pieces, stdout=open(ebi_submission.ascp_reply, 'a'))
            except:
                with open(ebi_submission.ascp_reply, 'r') as f:
                    content = f.read()
                ebi_submission.study.ebi_submission_status = (
                    "failed: ASCP - %s" % content)
                LogEntry.create('Fatal', content,
                                info={
                                    'ebi_submission': preprocessed_data_id,
                                    'fail': cmd})
        LogEntry.create('Runtime',
                        ('Submission of sequences of pre_processed_id: '
                         '%d completed successfully' %
                         preprocessed_data_id))
        environ['ASPERA_SCP_PASS'] = old_ascp_pass

        # step 5: sending xml and parsing answer
        xmls_cmds = shsplit(ebi_submission.generate_curl_command())
        LogEntry.create('Runtime',
                        ("Submitting XMLs for pre_processed_id: "
                         "%d" % preprocessed_data_id))
        try:
            call(xmls_cmds, stdout=open(ebi_submission.curl_reply, 'w'))
            with open(ebi_submission.curl_reply, 'r') as f:
                xml_content = f.read()
        except:
            with open(ebi_submission.curl_reply, 'r') as f:
                xml_content = f.read()
            LogEntry.create('Fatal', xml_content,
                            info={'ebi_submission': preprocessed_data_id})
        else:
            LogEntry.create('Runtime',
                            ('Submission of sequences of pre_processed_id: '
                             '%d completed successfully' %
                             preprocessed_data_id))

        try:
            st_acc, sa_acc, bio_acc, ex_acc, run_acc = \
                ebi_submission.parse_EBI_reply(xml_content)
        except EBISubmissionError as e:
            le = LogEntry.create(
                'Fatal', "Command: %s\nError: %s\n" % (xml_content, str(e)),
                info={'ebi_submission': preprocessed_data_id})
            ebi_submission.study.ebi_submission_status = (
                "failed: XML submission, log id: %d" % le.id)
            raise ComputeError("EBI Submission failed! Log id: %d" % le.id)

        ebi_submission.study.ebi_submission_status = 'submitted'
        if st_acc:
            ebi_submission.study.ebi_study_accession = st_acc
        if sa_acc:
            ebi_submission.sample_template.ebi_sample_accessions = sa_acc
        if bio_acc:
            ebi_submission.sample_template.biosample_accessions = bio_acc
        if ex_acc:
            ebi_submission.prep_template.ebi_experiment_accessions = ex_acc
        ebi_submission.preprocessed_data.ebi_run_accessions = run_acc
    else:
        st_acc, sa_acc, bio_acc, ex_acc, run_acc = None, None, None, None, None

    return st_acc, sa_acc, bio_acc, ex_acc, run_acc


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
