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

from qiita_db.artifact import Artifact
from qiita_db.logger import LogEntry
from qiita_db.processing_job import _system_call as system_call
from qiita_core.qiita_settings import qiita_config
from qiita_ware.ebi import EBISubmission
from qiita_ware.exceptions import ComputeError, EBISubmissionError


def submit_EBI(artifact_id, action, send, test=False):
    """Submit an artifact to EBI

    Parameters
    ----------
    artifact_id : int
        The artifact id
    action : %s
        The action to perform with this data
    send : bool
        True to actually send the files
    test : bool
        If True some restrictions will be ignored, only used in parse_EBI_reply
    """
    # step 1: init and validate
    ebi_submission = EBISubmission(artifact_id, action)

    # step 2: generate demux fastq files
    try:
        ebi_submission.generate_demultiplexed_fastq()
    except Exception:
        error_msg = format_exc()
        if isdir(ebi_submission.full_ebi_dir):
            rmtree(ebi_submission.full_ebi_dir)
        LogEntry.create('Runtime', error_msg,
                        info={'ebi_submission': artifact_id})
        raise

    # step 3: generate and write xml files
    ebi_submission.generate_xml_files()

    if send:
        # step 4: sending sequences
        if action != 'MODIFY':
            old_ascp_pass = environ.get('ASPERA_SCP_PASS', '')
            if old_ascp_pass == '':
                environ['ASPERA_SCP_PASS'] = qiita_config.ebi_seq_xfer_pass

            LogEntry.create('Runtime',
                            ("Submitting sequences for pre_processed_id: "
                             "%d" % artifact_id))
            for cmd in ebi_submission.generate_send_sequences_cmd():
                stdout, stderr, rv = system_call(cmd)
                if rv != 0:
                    error_msg = ("ASCP Error:\nStd output:%s\nStd error:%s" % (
                        stdout, stderr))
                    raise ComputeError(error_msg)
                open(ebi_submission.ascp_reply, 'a').write(
                    'stdout:\n%s\n\nstderr: %s' % (stdout, stderr))

            ascp_passwd = environ['ASPERA_SCP_PASS']
            environ['ASPERA_SCP_PASS'] = old_ascp_pass
            LogEntry.create('Runtime',
                            ('Submission of sequences of pre_processed_id: '
                             '%d completed successfully' % artifact_id))

        # step 5: sending xml and parsing answer
        xmls_cmds = ebi_submission.generate_curl_command(
            ebi_seq_xfer_pass=ascp_passwd)
        LogEntry.create('Runtime',
                        ("Submitting XMLs for pre_processed_id: "
                         "%d" % artifact_id))
        xml_content, stderr, rv = system_call(xmls_cmds)
        if rv != 0:
            error_msg = ("Error:\nStd output:%s\nStd error:%s" % (
                xml_content, stderr))
            raise ComputeError(error_msg)
        else:
            LogEntry.create('Runtime',
                            ('Submission of sequences of pre_processed_id: '
                             '%d completed successfully' % artifact_id))
        open(ebi_submission.curl_reply, 'w').write(
            'stdout:\n%s\n\nstderr: %s' % (xml_content, stderr))

        try:
            st_acc, sa_acc, bio_acc, ex_acc, run_acc = \
                ebi_submission.parse_EBI_reply(xml_content, test=test)
        except EBISubmissionError as e:
            error = str(e)
            le = LogEntry.create(
                'Fatal', "Command: %s\nError: %s\n" % (xml_content, error),
                info={'ebi_submission': artifact_id})
            raise ComputeError(
                "EBI Submission failed! Log id: %d\n%s" % (le.id, error))

        if action == 'ADD':
            if st_acc:
                ebi_submission.study.ebi_study_accession = st_acc
            if sa_acc:
                ebi_submission.sample_template.ebi_sample_accessions = sa_acc
            if bio_acc:
                ebi_submission.sample_template.biosample_accessions = bio_acc
            if ex_acc:
                ebi_submission.prep_template.ebi_experiment_accessions = ex_acc
            ebi_submission.artifact.ebi_run_accessions = run_acc
    else:
        st_acc, sa_acc, bio_acc, ex_acc, run_acc = None, None, None, None, None

    return st_acc, sa_acc, bio_acc, ex_acc, run_acc


def submit_VAMPS(artifact_id):
    """Submit artifact to VAMPS

    Parameters
    ----------
    artifact_id : int
        The artifact id

    Raises
    ------
    ComputeError
        - If the artifact cannot be submitted to VAMPS
        - If the artifact is associated with more than one prep template
    """
    artifact = Artifact(artifact_id)
    if not artifact.can_be_submitted_to_vamps:
        raise ComputeError("Artifact %d cannot be submitted to VAMPS"
                           % artifact_id)
    study = artifact.study
    sample_template = study.sample_template
    prep_templates = artifact.prep_templates
    if len(prep_templates) > 1:
        raise ComputeError(
            "Multiple prep templates associated with the artifact: %s"
            % artifact_id)
    prep_template = prep_templates[0]

    # Also need to check that is not submitting (see item in #1523)
    if artifact.is_submitted_to_vamps:
        raise ValueError("Cannot resubmit artifact %s to VAMPS!" % artifact_id)

    # Generating a tgz
    targz_folder = mkdtemp(prefix=qiita_config.working_dir)
    targz_fp = join(targz_folder, '%d_%d_%d.tgz' % (study.id,
                                                    prep_template.id,
                                                    artifact_id))
    targz = taropen(targz_fp, mode='w:gz')

    # adding sample/prep
    samp_fp = join(targz_folder, 'sample_metadata.txt')
    sample_template.to_file(samp_fp)
    targz.add(samp_fp, arcname='sample_metadata.txt')
    prep_fp = join(targz_folder, 'prep_metadata.txt')
    prep_template.to_file(prep_fp)
    targz.add(prep_fp, arcname='prep_metadata.txt')

    # adding preprocessed data
    for _, fp, fp_type in artifact.filepaths:
        if fp_type == 'preprocessed_fasta':
            targz.add(fp, arcname='preprocessed_fasta.fna')

    targz.close()

    # submitting
    cmd = ("curl -F user=%s -F pass='%s' -F uploadFile=@%s -F "
           "press=UploadFile %s" % (qiita_config.vamps_user,
                                    qiita_config.vamps_pass,
                                    targz_fp,
                                    qiita_config.vamps_url))
    obs, stderr, rv = system_call(cmd)
    if rv != 0:
        error_msg = ("Error:\nStd output:%s\nStd error:%s" % (obs, stderr))
        raise ComputeError(error_msg)

    exp = ("<html>\n<head>\n<title>Process Uploaded File</title>\n</head>\n"
           "<body>\n</body>\n</html>")

    if obs != exp:
        return False
    else:
        artifact.is_submitted_to_vamps = True
        return True
