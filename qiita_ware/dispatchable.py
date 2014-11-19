# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from os.path import join
from tempfile import mkdtemp
from gzip import open as gzopen
from traceback import format_exception_only
from sys import exc_info

from .processing_pipeline import StudyPreprocessor
from .analysis_pipeline import RunAnalysis
from qiita_core.qiita_settings import qiita_config
from qiita_ware.commands import submit_EBI_from_files
from qiita_ware.demux import to_per_sample_ascii
from qiita_ware.exceptions import ComputeError
from qiita_ware.util import open_file
from qiita_db.util import convert_to_id
from qiita_db.study import Study
from qiita_db.analysis import Analysis
from qiita_db.metadata_template import SampleTemplate, PrepTemplate
from qiita_db.data import RawData
from qiita_db.ontology import Ontology


def preprocessor(study_id, prep_template_id, param_id, param_constructor):
    """Dispatch for preprocessor work"""
    study = Study(study_id)
    prep_template = PrepTemplate(prep_template_id)
    params = param_constructor(param_id)

    sp = StudyPreprocessor()
    try:
        preprocess_out = sp(study, prep_template, params)
    except Exception as e:
        error_msg = ''.join(format_exception_only(e, exc_info()))
        prep_template.preprocessing_status = "failed: %s" % error_msg
        preprocess_out = None

    return preprocess_out


def submit_to_ebi(preprocessed_data_id, submission_type):
    """Submit a study to EBI"""
    from qiita_db.data import PreprocessedData

    preprocessed_data = PreprocessedData(preprocessed_data_id)
    pt = PrepTemplate(preprocessed_data.prep_template)
    st = SampleTemplate(preprocessed_data.study)

    investigation_type = None
    new_investigation_type = None

    state = preprocessed_data.submitted_to_insdc_status()
    if state in ('submitting', 'success'):
        raise ValueError("Cannot resubmit! Current state is: %s" % state)

    # we need to figure out whehter the investigation type is a known one
    # or if we have to submit a "new_investigation_type" to EBI
    current_type = pt.investigation_type
    if current_type not in Ontology(convert_to_id('ENA', 'ontology')).terms:
        investigation_type = 'Other'
        new_investigation_type = current_type
    else:
        investigation_type = current_type

    demux = [path for path, ftype in preprocessed_data.get_filepaths()
             if ftype == 'preprocessed_demux'][0]

    tmp_dir = mkdtemp(prefix=qiita_config.working_dir)
    output_dir = tmp_dir + '_submission'

    samp_fp = join(tmp_dir, 'sample_metadata.txt')
    prep_fp = join(tmp_dir, 'prep_metadata.txt')

    st.to_file(samp_fp)
    pt.to_file(prep_fp)

    with open_file(demux) as demux_fh:
        for samp, iterator in to_per_sample_ascii(demux_fh, list(st)):
            with gzopen(join(tmp_dir, "%s.fastq.gz" % samp), 'w') as fh:
                for record in iterator:
                    fh.write(record)

    preprocessed_data.update_insdc_status('submitting')
    study_acc, submission_acc = submit_EBI_from_files(preprocessed_data_id,
                                                      open(samp_fp),
                                                      open(prep_fp), tmp_dir,
                                                      output_dir,
                                                      investigation_type,
                                                      submission_type, True,
                                                      new_investigation_type)

    if study_acc is None or submission_acc is None:
        preprocessed_data.update_insdc_status('failed')

        # this will set the job status as failed
        raise ComputeError("EBI Submission failed!")
    else:
        preprocessed_data.update_insdc_status('success', study_acc,
                                              submission_acc)

    return study_acc, submission_acc


def run_analysis(analysis_id, commands, comm_opts=None,
                 rarefaction_depth=None, **kwargs):
    """Run a meta-analysis"""
    analysis = Analysis(analysis_id)
    ar = RunAnalysis(**kwargs)
    return ar(analysis, commands, comm_opts, rarefaction_depth)


def add_files_to_raw_data(raw_data_id, filepaths):
    """Add files to raw data

    Needs to be dispachable because it moves large files
    """
    rd = RawData(raw_data_id)
    rd.add_filepaths(filepaths)


def unlink_all_files(raw_data_id):
    """Removes all files from raw data

    Needs to be dispachable because it does I/O and a lot of DB calls
    """
    rd = RawData(raw_data_id)
    rd.clear_filepaths()
