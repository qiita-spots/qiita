# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from sys import stderr

from qiita_ware.wrapper import ParallelWrapper

from qiita_db.logger import LogEntry
from qiita_db.data import RawData


def _get_qiime_minimal_mapping(prep_template, out_dir):
    """Generates a minimal QIIME-compliant mapping file for split libraries

    The columns of the generated file are, in order: SampleID, BarcodeSequence,
    LinkerPrimerSequence, Description. All values are taken from the prep
    template except for Description, which always receive the value "Qiita MMF"

    Parameters
    ----------
    prep_template : PrepTemplate
        The prep template from which we need to generate the minimal mapping
    out_dir : str
        Path to the output directory

    Returns
    -------
    list of str
        The paths to the qiime minimal mapping files
    """
    from functools import partial
    from os.path import join
    import pandas as pd
    from qiita_ware.util import template_to_dict

    # Get the data in a pandas DataFrame, so it is easier to manage
    pt = pd.DataFrame.from_dict(template_to_dict(prep_template),
                                orient='index')
    # We now need to rename some columns to be QIIME compliant.
    # Hopefully, this conversion won't be needed if QIIME relaxes its
    # constraints
    pt.rename(columns={'barcodesequence': 'BarcodeSequence',
                       'linkerprimersequence': 'LinkerPrimerSequence'},
              inplace=True)
    pt['Description'] = pd.Series(['Qiita MMF'] * len(pt.index),
                                  index=pt.index)

    # We ensure the order of the columns as QIIME is expecting
    cols = ['BarcodeSequence', 'LinkerPrimerSequence', 'Description']

    # If the study has more than 1 lane, we should generate a qiita MMF for
    # each of the lanes. We know how to split the prep template based on
    # the run_prefix column
    output_fps = []
    path_builder = partial(join, out_dir)
    for prefix, df in pt.groupby('run_prefix'):
        df = df[cols]
        out_fp = path_builder("%s_MMF.txt" % prefix)
        output_fps.append(out_fp)
        df.to_csv(out_fp, index_label="#SampleID", sep='\t')

    return output_fps


def _get_preprocess_fastq_cmd(raw_data, prep_template, params):
    """Generates the split_libraries_fastq.py command for the raw-data

    Parameters
    ----------
    raw_data : RawData
        The raw data object to pre-process
    prep_template : PrepTemplate
        The prep template to pre-process
    params : PreprocessedIlluminaParams
        The parameters to use for the preprocessing

    Returns
    -------
    tuple (str, str)
        A 2-tuple of strings. The first string is the command to be executed.
        The second string is the path to the command's output directory

    Raises
    ------
    NotImplementedError
        If any of the raw data input filepath type is not supported
    ValueError
        If the number of raw sequences an raw barcode files are not the same
        If the raw data object does not have any sequence file associated
    """
    from tempfile import mkdtemp

    from qiita_core.qiita_settings import qiita_config

    # Get the filepaths from the raw data object
    forward_seqs = []
    reverse_seqs = []
    barcode_fps = []
    for fpid, fp, fp_type in raw_data.get_filepaths():
        if fp_type == "raw_forward_seqs":
            forward_seqs.append(fp)
        elif fp_type == "raw_reverse_seqs":
            reverse_seqs.append(fp)
        elif fp_type == "raw_barcodes":
            barcode_fps.append(fp)
        else:
            raise NotImplementedError("Raw data file type not supported %s"
                                      % fp_type)

    if len(forward_seqs) == 0:
        raise ValueError("Forward reads file not found on raw data %s"
                         % raw_data.id)

    if len(barcode_fps) != len(forward_seqs):
        raise ValueError("The number of barcode files and the number of "
                         "sequence files should match: %d != %d"
                         % (len(barcode_fps), len(forward_seqs)))

    # The minimal QIIME mapping files should be written to a directory,
    # so QIIME can consume them
    prep_dir = mkdtemp(dir=qiita_config.working_dir,
                       prefix='MMF_%s' % prep_template.id)

    # Get the Minimal Mapping Files
    mapping_fps = _get_qiime_minimal_mapping(prep_template, prep_dir)

    # Create a temporary directory to store the split libraries output
    output_dir = mkdtemp(dir=qiita_config.working_dir, prefix='slq_out')

    # Add any other parameter needed to split libraries fastq
    params_str = params.to_str()

    # We need to sort the filepaths to make sure that each lane's file is in
    # the same order, so they match when passed to split_libraries_fastq.py
    # All files should be prefixed with run_prefix, so the ordering is
    # ensured to be correct
    forward_seqs = sorted(forward_seqs)
    reverse_seqs = sorted(reverse_seqs)
    barcode_fps = sorted(barcode_fps)
    mapping_fps = sorted(mapping_fps)

    # Create the split_libraries_fastq.py command
    cmd = str("split_libraries_fastq.py --store_demultiplexed_fastq -i %s -b "
              "%s -m %s -o %s %s"
              % (','.join(forward_seqs), ','.join(barcode_fps),
                 ','.join(mapping_fps), output_dir, params_str))
    return (cmd, output_dir)


def _generate_demux_file(sl_out):
    """Creates the HDF5 demultiplexed file

    Parameters
    ----------
    sl_out : str
        Path to the output directory of split libraries

    Raises
    ------
    ValueError
        If the split libraries output does not contain the demultiplexed fastq
        file
    """
    from os.path import join, exists
    from h5py import File
    from qiita_ware.demux import to_hdf5

    fastq_fp = join(sl_out, 'seqs.fastq')
    if not exists(fastq_fp):
        raise ValueError("The split libraries output directory does not "
                         "contain the demultiplexed fastq file")

    demux_fp = join(sl_out, 'seqs.demux')
    with File(demux_fp, "w") as f:
        to_hdf5(fastq_fp, f)


def _insert_preprocessed_data_fastq(study, params, prep_template, slq_out):
    """Inserts the preprocessed data to the database

    Parameters
    ----------
    study : Study
        The study to preprocess
    params : BaseParameters
        The parameters to use for preprocessing
    prep_template : PrepTemplate
        The prep template to use for the preprocessing
    slq_out : str
        Path to the split_libraries_fastq.py output directory

    Raises
    ------
    ValueError
        If the preprocessed output directory does not contain all the expected
        files
    """
    from os.path import exists, join
    from functools import partial
    from qiita_db.data import PreprocessedData

    # The filepaths that we are interested in are:
    #   1) seqs.fna -> demultiplexed fasta file
    #   2) seqs.fastq -> demultiplexed fastq file
    #   3) seqs.demux -> demultiplexed HDF5 file

    path_builder = partial(join, slq_out)
    fasta_fp = path_builder('seqs.fna')
    fastq_fp = path_builder('seqs.fastq')
    demux_fp = path_builder('seqs.demux')
    log_fp = path_builder('split_library_log.txt')

    # Check that all the files exist
    if not (exists(fasta_fp) and exists(fastq_fp) and exists(demux_fp) and
            exists(log_fp)):
        raise ValueError("The output directory %s does not contain all the "
                         "expected files." % slq_out)

    filepaths = [(fasta_fp, "preprocessed_fasta"),
                 (fastq_fp, "preprocessed_fastq"),
                 (demux_fp, "preprocessed_demux"),
                 (log_fp, "log")]

    PreprocessedData.create(study, params._table, params.id, filepaths,
                            prep_template)

    # Change the prep_template status to success
    prep_template.preprocessing_status = 'success'


class StudyPreprocessor(ParallelWrapper):
    def _construct_job_graph(self, study, prep_template, params):
        """Constructs the workflow graph to preprocess a study

        The steps performed to preprocess a study are:
        1) Execute split libraries
        2) Add the new preprocessed data to the DB

        Parameters
        ----------
        study : Study
            The study to preprocess
        prep_template : PrepTemplate
            The prep template to use for the preprocessing
        params : BaseParameters
            The parameters to use for preprocessing
        """

        self.prep_template = prep_template
        self._logger = stderr
        raw_data = RawData(prep_template.raw_data)
        # Change the prep_template preprocessing_status t
        self.prep_template.preprocessing_status = 'preprocessing'

        # STEP 1: Preprocess the study
        preprocess_node = "PREPROCESS"

        # Check the raw data filetype to know which command generator we
        # should use
        filetype = raw_data.filetype
        if filetype == "FASTQ":
            cmd_generator = _get_preprocess_fastq_cmd
            insert_preprocessed_data = _insert_preprocessed_data_fastq
        else:
            raise NotImplementedError(
                "Raw data %s cannot be preprocessed, filetype %s not supported"
                % (raw_data.id, filetype))

        # Generate the command
        cmd, output_dir = cmd_generator(raw_data, self.prep_template, params)
        self._job_graph.add_node(preprocess_node, job=(cmd,),
                                 requires_deps=False)

        # This step is currently only for data types in which we need to store,
        # demultiplexed sequences. Since it is the only supported data type at
        # this point, it is ok the leave it here. However, as new data types
        # become available, we will need to think a better way of doing this.
        demux_node = "GEN_DEMUX_FILE"
        self._job_graph.add_node(demux_node,
                                 job=(_generate_demux_file, output_dir),
                                 requires_deps=False)
        self._job_graph.add_edge(preprocess_node, demux_node)

        # STEP 2: Add preprocessed data to DB
        insert_preprocessed_node = "INSERT_PREPROCESSED"
        self._job_graph.add_node(insert_preprocessed_node,
                                 job=(insert_preprocessed_data, study, params,
                                      self.prep_template, output_dir),
                                 requires_deps=False)
        self._job_graph.add_edge(demux_node, insert_preprocessed_node)

        self._dirpaths_to_remove.append(output_dir)

    def _failure_callback(self, msg=None):
        """Callback to execute in case that any of the job nodes failed

        Need to change the prep_template preprocessing status to 'failed'
        """
        self.prep_template.preprocessing_status = 'failed: %s' % msg
        LogEntry.create('Fatal', msg,
                        info={'prep_template': self.prep_template.id})
