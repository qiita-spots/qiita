# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

# TODO: change to import from QIITA once is merged
from qiime.parallel.wrapper import ParallelWrapper


def _get_preprocess_illumina_cmd(raw_data):
    """Generates the split_libraries_fastq.py command to pre-process the
    illumina raw data

    Parameters
    ----------
    raw_data : RawData
        The raw data object to pre-process

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
    params = ""

    # Create the split_libraries_fastq.py command
    cmd = ("split_libraries_fastq.py --store_demultiplexed_fastq -i %s -b %s "
           "-m %s -o %s %s"
           % (seqs_fps, barcode_fps, prep_fp, output_dir, params))
    return (cmd, output_dir)


def _get_pick_closed_reference_cmd(preprocessed_data, reference):
    """Generates the pcik_closed_reference.py command to process the
    pre-processed data

    Parameters
    ----------
    preprocessed_data : PreprocessedData
        The pre-processed data object to process
    reference : Reference
        The reference database to use to process thee data

    Returns
    -------
    tuple (str, str)
        A 2-tuple of strings. The first string is the command to be executed.
        The second string is the path to the command's output directory
    """
    from tempfile import mkdtemp

    # Create a temporary directory to store the pick otus output
    output_dir = mkdtemp(prefix='closed_otus_out')

    cmd = ("pick_closed_reference_otus.py -i %s -r %s -t %s -o %s"
           % (seqs_fp, reference.sequence_fp, reference.taxonomy_fp,
              output_dir))

    return (cmd, output_dir)


def _clean_up(dirs):
    """"""
    from shutil import rmtree
    from os.path import exists

    for dp in dirs:
        if exists(dp):
            rmtree(dp)


def _insert_preprocessed_data():
    """"""
    from qiita_db.data import PreprocessedData

    PreprocessedData.create(study, preprocessed_params_table,
                            preprocessed_params_id, filepaths, raw_data)


def _insert_processed_data():
    """"""
    from qiita_db.data import ProcessedData

    ProcessedData(processed_params_table, processed_params_id, filepaths,
                  preprocessed_data)


class StudyProcesser(ParallelWrapper):
    def _construct_job_graph(self, study, raw_data):
        """Constructs the workflow graph to process a study

        The steps performed to process a study are:
        1) Preprocess the study with split_libraries_fastq.py
        2) Add the new preprocesed data to the DB
        3) Process the preprocessed data by doing closed reference OTU picking
        against GreenGenes, using SortMeRNA
        4) Add the new processed data to the DB

        Parameters
        ----------
        study : Study
            The study to process
        raw_data: RawData
            The raw data to use to process the study

        Raises
        ------
        NotImplementedError
            If any file type in the raw data object is not supported
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
        cmd, output_dir = cmd_generator(raw_data)
        self._job_graph.add_node(preprocess_node, job=(cmd,),
                                 requires_deps=False)

        # STEP 2: Add preprocessed data to DB
        insert_preprocessed_node = "INSERT_PREPROCESSED"
        self._job_graph.add_node(insert_preprocessed_node,
                                 job=(_insert_preprocessed_data, ),
                                 requires_deps=False)
        self._job_graph.add_edge(preprocess_node, insert_preprocessed_node)

        # STEP 3: pick closed-ref otu picking
        processed_node = "PROCESS"
        # TODO: Now hard-coded to GG 13 8 (id = 1) - issue #
        reference = Reference(1)
        cmd, otus_out = _get_pick_closed_reference_cmd(output_dir, reference)
        self._job_graph.add_node(processed_node, job=(cmd,),
                                 requires_deps=False)
        self._job_graph.add_edge(insert_preprocessed_node, processed_node)

        # STEP 4: Add processed data to DB
        insert_processed_node = "INSERT_PROCESSED"
        self._job_graph.add_node(insert_processed_node,
                                 job=(_insert_processed_data, ),
                                 requires_deps=False)
        self._job_graph.add_edge(process_node, insert_processed_node)

        # Clean up the environment
        clean_up_node = "CLEAN_UP"
        self._job_graph.add_node(clean_up_node,
                                 job=(_clean_up, [output_dir, otus_out]),
                                 requires_deps=False)
        self._job_graph.add_edge(insert_processed_node, clean_up_node)
