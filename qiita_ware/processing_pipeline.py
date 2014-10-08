# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from qiita_ware.wrapper import ParallelWrapper


def _get_preprocess_illumina_cmd(raw_data, params):
    """Generates the split_libraries_fastq.py command to pre-process the
    illumina raw data

    Parameters
    ----------
    raw_data : RawData
        The raw data object to pre-process
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
    from tempfile import mkstemp, mkdtemp
    from os import close

    from qiita_db.metadata_template import PrepTemplate
    from qiita_db.parameters import PreprocessedIlluminaParams

    # Get the filepaths from the raw data object
    seqs_fps = []
    barcode_fps = []
    for fp, fp_type in raw_data.get_filepaths():
        if fp_type == "raw_sequences":
            seqs_fps.append(fp)
        elif fp_type == "raw_barcodes":
            barcode_fps.append(fp)
        else:
            raise NotImplementedError("Raw data file type not supported %s"
                                      % fp_type)

    if len(seqs_fps) == 0:
        raise ValueError("Sequence file not found on raw data %s"
                         % raw_data.id)

    if len(barcode_fps) != len(seqs_fps):
        raise ValueError("The number of barcode files and the number of "
                         "sequence files should match: %d != %d"
                         % len(barcode_fps), len(seqs_fps))

    # Instantiate the prep template
    prep_template = PrepTemplate(raw_data.id)

    # The prep template should be written to a temporary file
    fd, prep_fp = mkstemp(prefix="qiita_prep_%s" % prep_template.id,
                          suffix='.txt')
    close(fd)
    prep_template.to_file(prep_fp)

    # Create a temporary directory to store the split libraries output
    output_dir = mkdtemp(prefix='slq_out')

    # Add any other parameter needed to split libraries fastq
    params_str = params.to_str()

    # Create the split_libraries_fastq.py command
    cmd = ("split_libraries_fastq.py --store_demultiplexed_fastq -i %s -b %s "
           "-m %s -o %s %s"
           % (','.join(seqs_fps), ','.join(barcode_fps), prep_fp, output_dir,
              params_str))
    return (cmd, output_dir)


def _clean_up(dirs):
    """Removes the directories listed in dirs

    Parameters
    ----------
    dirs : list of str
        Path to the directories to remove
    """
    from shutil import rmtree
    from os.path import exists

    for dp in dirs:
        if exists(dp):
            rmtree(dp)


def _insert_preprocessed_data(study, params, raw_data, prep_out_dir):
    """Inserts the preprocessed data to the database

    Parameters
    ----------
    study : Study
        The study to preprocess
    params : BaseParameters
        The parameters to use for preprocessing
    raw_data : RawData
        The raw data to use for the preprocessing
    prep_out_dir : str
        Path to the preprocessed command output directory

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

    path_builder = partial(join, prep_out_dir)
    fasta_fp = path_builder('seqs.fna')
    fastq_fp = path_builder('seqs.fastq')
    demux_fp = path_builder('seqs.demux')

    # Check that all the files exist
    if not (exists(fasta_fp) and exists(fastq_fp) and exists(demux_fp)):
        raise ValueError("The output directory %s does not contain all the "
                         "expected files." % prep_out_dir)

    filepaths = [(fasta_fp, "preprocessed_fasta"),
                 (fastq_fp, "preprocessed_fastq"),
                 (demux_fp, "preprocessed_demux")]

    PreprocessedData.create(study, params._table, params.id(), filepaths,
                            raw_data)


class StudyPreprocesser(ParallelWrapper):
    def _construct_job_graph(self, study, raw_data, params):
        """Constructs the workflow graph to preprocess a study

        The steps performed to preprocess a study are:
        1) Execute split libraries
        2) Add the new preprocessed data to the DB

        Parameters
        ----------
        study : Study
            The study to preprocess
        raw_data : RawData
            The raw data to use for the preprocessing
        params : BaseParameters
            The parameters to use for preprocessing
        """
        # STEP 1: Preprocess the study
        preprocess_node = "PREPROCESS"

        # Check the raw data filepath to know which command generator we
        # should use
        filetype = raw_data.filetype
        if filetype == "Illumina":
            cmd_generator = _get_preprocess_illumina_cmd
        else:
            raise NotImplementedError(
                "Raw data %s cannot be preprocessed, filetype %s not supported"
                % (raw_data.id, filetype))

        # Generate the command
        cmd, output_dir = cmd_generator(raw_data, params)
        self._job_graph.add_node(preprocess_node, job=(cmd,),
                                 requires_deps=False)

        # STEP 2: Add preprocessed data to DB
        insert_preprocessed_node = "INSERT_PREPROCESSED"
        self._job_graph.add_node(insert_preprocessed_node,
                                 job=(_insert_preprocessed_data, ),
                                 requires_deps=False)
        self._job_graph.add_edge(preprocess_node, insert_preprocessed_node)

        # Clean up the environment
        clean_up_node = "CLEAN_UP"
        self._job_graph.add_node(clean_up_node,
                                 job=(_clean_up, [output_dir]),
                                 requires_deps=False)
        self._job_graph.add_edge(insert_processed_node, clean_up_node)
