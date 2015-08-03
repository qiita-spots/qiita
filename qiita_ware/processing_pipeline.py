# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from sys import stderr
from tempfile import mkdtemp, mkstemp
from os import close, rmdir

from moi.job import system_call

from qiita_core.qiita_settings import qiita_config
from qiita_ware.wrapper import ParallelWrapper
from qiita_db.logger import LogEntry
from qiita_db.data import RawData
from qiita_db.metadata_template import TARGET_GENE_DATA_TYPES
from qiita_db.reference import Reference


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
    from collections import defaultdict
    from os.path import join
    import pandas as pd

    # The prep templates has a QIIME mapping file, get it
    qiime_map = pd.read_csv(prep_template.qiime_map_fp, sep='\t',
                            keep_default_na=False, na_values=['unknown'],
                            index_col=False,
                            converters=defaultdict(lambda: str))
    qiime_map.set_index('#SampleID', inplace=True, drop=True)

    # We use our own description to avoid potential processing problems
    qiime_map['Description'] = pd.Series(['Qiita MMF'] * len(qiime_map.index),
                                         index=qiime_map.index)

    # We ensure the order of the columns as QIIME is expecting
    if 'ReverseLinkerPrimer' in qiime_map:
        cols = ['BarcodeSequence', 'LinkerPrimerSequence',
                'ReverseLinkerPrimer', 'Description']
    else:
        cols = ['BarcodeSequence', 'LinkerPrimerSequence', 'Description']

    path_builder = partial(join, out_dir)
    if 'run_prefix' in qiime_map:
        # The study potentially has more than 1 lane, so we should generate a
        # qiime MMF for each of the lanes. We know how to split the prep
        # template based on the run_prefix column
        output_fps = []
        for prefix, df in qiime_map.groupby('run_prefix'):
            df = df[cols]
            out_fp = path_builder("%s_MMF.txt" % prefix)
            output_fps.append(out_fp)
            df.to_csv(out_fp, index_label="#SampleID", sep='\t')
    else:
        # The study only has one lane, just write the MMF
        df = qiime_map[cols]
        out_fp = path_builder("prep_%d_MMF.txt" % prep_template.id)
        output_fps = [out_fp]
        df.to_csv(out_fp, index_label="#SampleID", sep='\t')

    return output_fps


def _get_sample_names_by_run_prefix(prep_template):
    """Generates a dictionary of run_prefix and sample names

    Parameters
    ----------
    prep_template : PrepTemplate
        The prep template from which we need to generate the minimal mapping
        file

    Returns
    -------
    dict
        Dict mapping run_prefix to path of the minimal qiime mapping file

    Raises
    ------
    ValueError
        If there is more than 1 sample per run_prefix
    """
    from qiita_db.metadata_template import load_template_to_dataframe

    qiime_map = load_template_to_dataframe(prep_template.qiime_map_fp,
                                           index='#SampleID')

    samples = {}
    errors = []
    for prefix, df in qiime_map.groupby('run_prefix'):
        len_df = len(df)
        if len_df != 1:
            errors.append('%s has %d samples (%s)' % (prefix, len_df,
                                                      ', '.join(df.index)))
        else:
            samples[prefix] = df.index.values[0]

    if errors:
        raise ValueError("You have run_prefix values with multiple "
                         "samples: %s" % ' -- '.join(errors))

    return samples


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
        If the raw data object does not have any sequence file associated
        If the raw data filetype is not per_sample_FASTQ and the number of raw
        forward sequences and raw barcode files are not the same
        If the raw data filetype is per_sample_FASTQ and it has barcode files
        If the raw data filetype is per_sample_FASTQ and the run_prefix values
        don't match the file names without extensions and without the raw data
        id prefix
    """
    from tempfile import mkdtemp
    from os.path import basename

    from qiita_core.qiita_settings import qiita_config

    filetype = raw_data.filetype

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

    # We need to sort the filepaths to make sure that each lane's file is in
    # the same order, so they match when passed to split_libraries_fastq.py
    # All files should be prefixed with run_prefix, so the ordering is
    # ensured to be correct
    forward_seqs = sorted(forward_seqs)
    reverse_seqs = sorted(reverse_seqs)
    barcode_fps = sorted(barcode_fps)

    # Create a temporary directory to store the split libraries output
    output_dir = mkdtemp(
        dir=qiita_config.working_dir,
        prefix='slq_out_%d_%d_' % (prep_template.id, raw_data.id))

    # Add any other parameter needed to split libraries fastq
    params_str = params.to_str()

    if len(forward_seqs) == 0:
        raise ValueError("Forward reads file not found in raw data %s"
                         % raw_data.id)

    if filetype == "per_sample_FASTQ":
        if barcode_fps:
            raise ValueError("per_sample_FASTQ can not have barcodes: %s"
                             % (', '.join([basename(b) for b in barcode_fps])))

        sn_by_rp = _get_sample_names_by_run_prefix(prep_template)
        samples = []
        for f in forward_seqs:
            # getting just the main filename
            f = basename(f).split('_', 1)[1]
            # removing extentions: fastq or fastq.gz
            if 'fastq' in f.lower().rsplit('.', 2):
                f = f[:f.lower().rindex('.fastq')]
            # this try/except block is simply to retrieve all possible errors
            # and display them in the next if block
            try:
                samples.append(sn_by_rp[f])
                del sn_by_rp[f]
            except KeyError:
                pass

        if sn_by_rp:
            raise ValueError(
                'Some run_prefix values do not match your sample names: %s'
                % ', '.join(sn_by_rp.keys()))

        cmd = str("split_libraries_fastq.py --store_demultiplexed_fastq -i %s "
                  "--sample_ids %s -o %s %s" % (','.join(forward_seqs),
                                                ','.join(samples), output_dir,
                                                params_str))
    else:
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
        mapping_fps = sorted(mapping_fps)

        # Create the split_libraries_fastq.py command
        cmd = str("split_libraries_fastq.py --store_demultiplexed_fastq -i %s "
                  "-b %s -m %s -o %s %s"
                  % (','.join(forward_seqs), ','.join(barcode_fps),
                     ','.join(mapping_fps), output_dir, params_str))

    return (cmd, output_dir)


def _get_preprocess_fasta_cmd(raw_data, prep_template, params):
    """Generates the split_libraries.py command for the raw-data

    Parameters
    ----------
    raw_data : RawData
        The raw data object to pre-process
    prep_template : PrepTemplate
        The prep template to pre-process
    params : Preprocessed454Params
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
        If the raw data object does not have any sequence file associated
    """
    from tempfile import mkdtemp
    from os.path import basename, splitext, join
    from qiita_core.qiita_settings import qiita_config

    # Get the filepaths from the raw data object
    sffs = []
    seqs = []
    quals = []
    for fpid, fp, fp_type in raw_data.get_filepaths():
        if fp_type == "raw_sff":
            sffs.append(fp)
        elif fp_type == "raw_fasta":
            seqs.append(fp)
        elif fp_type == "raw_qual":
            quals.append(fp)
        else:
            raise NotImplementedError("Raw data file type not supported %s"
                                      % fp_type)

    # Create a temporary directory to store the split libraries output
    output_dir = mkdtemp(dir=qiita_config.working_dir, prefix='sl_out')

    prepreprocess_cmd = ''
    if seqs and sffs:
        raise ValueError("Cannot have SFF and raw fasta, on %s"
                         % raw_data.id)
    elif quals and not seqs:
        raise ValueError("Cannot have just qual, on %s"
                         % raw_data.id)
    elif seqs and not quals:
        raise ValueError("It is not currently possible to process "
                         "fasta file(s) without qual file(s). This will "
                         "be supported in the future. You can track progress "
                         "on this by following: "
                         "https://github.com/biocore/qiita/issues/953")
    elif seqs:
        seqs = sorted(seqs)
        quals = sorted(quals)

    else:
        prepreprocess_cmds = []
        for sff in sffs:
            base = splitext(basename(sff))[0]
            if sff.endswith('.gz'):
                base = splitext(base)[0]

            sff_cmd = "process_sff.py -i %s -o %s" % (sff, output_dir)
            prepreprocess_cmds.append(sff_cmd)
            seqs.append(join(output_dir, '%s.fna' % base))
            quals.append(join(output_dir, '%s.qual' % base))
        prepreprocess_cmd = '; '.join(prepreprocess_cmds)

    # The minimal QIIME mapping files should be written to a directory,
    # so QIIME can consume them
    prep_dir = mkdtemp(dir=qiita_config.working_dir,
                       prefix='MMF_%s' % prep_template.id)

    # Get the Minimal Mapping Files
    mapping_fps = sorted(_get_qiime_minimal_mapping(prep_template, prep_dir))

    # Add any other parameter needed to split libraries
    params_str = params.to_str()

    # Create the split_libraries_fastq.py command
    # len(mapping_fps) will be == 1 when there is no run_prefix or it has
    # the same value in all the rows
    if len(mapping_fps) == 1:
        qual_str = "-q %s -d" % ','.join(quals) if quals else ""
        cmd = ' '.join(["split_libraries.py",
                        "-f %s" % ','.join(seqs),
                        "-m %s" % mapping_fps[0],
                        qual_str,
                        "-o %s" % output_dir,
                        params_str])
    else:
        len_seqs = len(seqs)
        len_mapping_fps = len(mapping_fps)

        if len_mapping_fps > len_seqs:
            mapping_fps = [basename(m) for m in mapping_fps]
            sffs = [basename(s) for s in sffs]
            raise ValueError(
                'The prep template defines: "%s" but you only have "%s" as '
                'sequence files' % (', '.join(mapping_fps), ', '.join(sffs)))

        if len_seqs != len_mapping_fps:
            # -8 is to remove the _MMF.txt
            prefixes = {m: {'prefix': basename(m)[:-8], 'seqs': [],
                            'quals': []} for m in mapping_fps}
            counter = 0
            for p in prefixes.values():
                for i, s in enumerate(seqs):
                    # the files are prefixed with raw_data_id
                    if basename(s).split('_', 1)[1].startswith(p['prefix']):
                        p['seqs'].append(s)
                        if quals:
                            p['quals'].append(quals[i])
                        counter = counter + 1

            if counter != len_seqs:
                raise ValueError(
                    'The run prefixes in your prep template '
                    '"%s" do not match your file names "%s"' %
                    (', '.join(mapping_fps), ', '.join(sffs)))

            mapping_fps = prefixes.keys()
            seqs = [','.join(p['seqs']) for p in prefixes.values()]
            if quals:
                quals = [','.join(p['quals']) for p in prefixes.values()]

        cmd, output_folders, n = [], [], 1
        for i, (seq, mapping) in enumerate(zip(seqs, mapping_fps)):
            qual_str = "-q %s -d" % quals[i] if quals else ""
            split_dir = join(output_dir, basename(mapping))
            output_folders.append(split_dir)

            cmd.append(' '.join(["split_libraries.py",
                                 "-f %s" % seq,
                                 "-m %s" % mapping,
                                 qual_str,
                                 "-o %s" % split_dir,
                                 "-n %d" % n,
                                 params_str]))
            # Number comes from (100K larger than amplicon):
            # http://454.com/products/gs-FLX-system/index.asp
            n = (i + 1) * 800000

        # files to cat from multiple split libraries
        to_cat = ['split_library_log.txt', 'seqs.fna']
        if quals:
            to_cat.append('seqs_filtered.qual')
        for tc in to_cat:
            files = [join(x, tc) for x in output_folders]
            cmd.append("cat %s > %s" % (' '.join(files),
                                        join(output_dir, tc)))

        cmd = '; '.join(cmd)

    if quals:
        fq_cmd = ' '.join(["convert_fastaqual_fastq.py",
                           "-f %s/seqs.fna" % output_dir,
                           "-q %s/seqs_filtered.qual" % output_dir,
                           "-o %s" % output_dir,
                           "-F"])

        if prepreprocess_cmd:
            cmd = '; '.join([prepreprocess_cmd, cmd, fq_cmd])
        else:
            cmd = '; '.join([cmd, fq_cmd])
    return (cmd, output_dir)


def generate_demux_file(sl_out, **kwargs):
    """Creates the HDF5 demultiplexed file

    Parameters
    ----------
    sl_out : str
        Path to the output directory of split libraries
    kwargs: ignored
        Necessary to include to support execution via moi.

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
                         "contain the demultiplexed fastq file.")

    demux_fp = join(sl_out, 'seqs.demux')
    with File(demux_fp, "w") as f:
        to_hdf5(fastq_fp, f)

    return demux_fp


def _insert_preprocessed_data(study, params, prep_template, slq_out,
                              **kwargs):
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
    kwargs: ignored
        Necessary to include to support execution via moi.

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
    if not (exists(fasta_fp) and exists(demux_fp) and exists(log_fp)):
        raise ValueError("The output directory %s does not contain all the "
                         "expected files." % slq_out)

    filepaths = [(fasta_fp, "preprocessed_fasta"),
                 (demux_fp, "preprocessed_demux"),
                 (log_fp, "log")]

    if exists(fastq_fp):
        filepaths.append((fastq_fp, "preprocessed_fastq"))

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
        if filetype in ("FASTQ", "per_sample_FASTQ"):
            cmd_generator = _get_preprocess_fastq_cmd
            insert_preprocessed_data = _insert_preprocessed_data
        elif filetype in ('FASTA', 'SFF'):
            cmd_generator = _get_preprocess_fasta_cmd
            insert_preprocessed_data = _insert_preprocessed_data
        else:
            raise NotImplementedError(
                "Raw data %s cannot be preprocessed, filetype %s not supported"
                % (raw_data.id, filetype))

        # Generate the command
        cmd, output_dir = cmd_generator(raw_data, self.prep_template, params)
        self._job_graph.add_node(preprocess_node, func=system_call,
                                 args=(cmd,),
                                 job_name="Construct preprocess command",
                                 requires_deps=False)

        # This step is currently only for data types in which we need to store,
        # demultiplexed sequences. Since it is the only supported data type at
        # this point, it is ok the leave it here. However, as new data types
        # become available, we will need to think a better way of doing this.
        demux_node = "GEN_DEMUX_FILE"
        self._job_graph.add_node(demux_node,
                                 func=generate_demux_file,
                                 args=(output_dir,),
                                 job_name="Generated demux file",
                                 requires_deps=False)
        self._job_graph.add_edge(preprocess_node, demux_node)

        # STEP 2: Add preprocessed data to DB
        insert_preprocessed_node = "INSERT_PREPROCESSED"
        self._job_graph.add_node(insert_preprocessed_node,
                                 func=insert_preprocessed_data,
                                 args=(study, params, self.prep_template,
                                       output_dir),
                                 job_name="Store preprocessed data",
                                 requires_deps=False)
        self._job_graph.add_edge(demux_node, insert_preprocessed_node)

        self._dirpaths_to_remove.append(output_dir)

    def _failure_callback(self, msg=None):
        """Callback to execute in case that any of the job nodes failed

        Need to change the prep_template preprocessing status to 'failed'
        """
        self.prep_template.preprocessing_status = 'failed:\n %s' % msg
        LogEntry.create('Fatal', msg,
                        info={'prep_template': self.prep_template.id})


# <======== StudyProcessor helper functions ===========>


def _get_process_target_gene_cmd(preprocessed_data, params):
    """Generates the pick_closed_reference_otus.py command

    Parameters
    ----------
    preprocessed_data : PreprocessedData
        The preprocessed_data to process
    params : ProcessedSortmernaParams
        The parameters to use for the processing

    Returns
    -------
    tuple (str, str)
        A 2-tuple of strings. The first string is the command to be executed.
        The second string is the path to the command's output directory

    Raises
    ------
    ValueError
        If no sequence file is found on the preprocessed data
    """
    # Get the filepaths from the preprocessed data object
    seqs_fp = None
    for fpid, fp, fp_type in preprocessed_data.get_filepaths():
        if fp_type == "preprocessed_fasta":
            seqs_fp = fp
            break

    if not seqs_fp:
        raise ValueError("No sequence file found on the preprocessed data %s"
                         % preprocessed_data.id)

    # Create a temporary directory to store the pick otus results
    output_dir = mkdtemp(dir=qiita_config.working_dir,
                         prefix='pick_otus_otu_%s_' % preprocessed_data.id)
    # mkdtemp creates the directory, so we remove it here so the script
    # can safely run
    rmdir(output_dir)

    # We need to generate a parameters file with the parameters for
    # pick_otus.py
    fd, param_fp = mkstemp(dir=qiita_config.working_dir,
                           prefix='params_%s_' % preprocessed_data.id,
                           suffix='.txt')
    close(fd)

    with open(param_fp, 'w') as f:
        params.to_file(f)

    ref = Reference(params.reference)

    reference_fp = ref.sequence_fp
    taxonomy_fp = ref.taxonomy_fp
    if taxonomy_fp:
        params_str = "-t %s" % taxonomy_fp
    else:
        params_str = ""

    # Create the split_libraries_fastq.py command
    cmd = str("pick_closed_reference_otus.py -i %s -r %s -o %s -p %s %s"
              % (seqs_fp, reference_fp, output_dir, param_fp, params_str))

    return (cmd, output_dir)


def _insert_processed_data_target_gene(preprocessed_data, params,
                                       pick_otus_out, **kwargs):
    """Inserts the preprocessed data to the database

    Parameters
    ----------
    preprocessed_data : PreprocessedData
        The preprocessed_data to process
    params : ProcessedSortmernaParams
        The parameters to use for the processing
    pick_otus_out : str
        Path to the pick_closed_reference_otus.py output directory
    kwargs: ignored
        Necessary to include to support execution via moi.

    Raises
    ------
    ValueError
        If the processed output directory does not contain all the expected
        files
    """
    from os.path import exists, join, isdir
    from glob import glob
    from functools import partial
    from qiita_db.data import ProcessedData

    # The filepaths that we are interested in are:
    #   1) otu_table.biom -> the output OTU table
    #   2) sortmerna_picked_otus -> intermediate output of pick_otus.py
    #   3) log_20141217091339.log -> log file

    path_builder = partial(join, pick_otus_out)
    biom_fp = path_builder('otu_table.biom')
    otus_dp = path_builder('sortmerna_picked_otus')
    log_fp = glob(path_builder('log_*.txt'))[0]

    # Check that all the files exist
    if not (exists(biom_fp) and isdir(otus_dp) and exists(log_fp)):
        raise ValueError("The output directory %s does not contain all the "
                         "expected files." % pick_otus_out)

    filepaths = [(biom_fp, "biom"),
                 (otus_dp, "directory"),
                 (log_fp, "log")]

    ProcessedData.create(params._table, params.id, filepaths,
                         preprocessed_data=preprocessed_data)

    # Change the preprocessed_data status to processed
    preprocessed_data.processing_status = 'processed'


class StudyProcessor(ParallelWrapper):
    def _construct_job_graph(self, preprocessed_data, params):
        """Constructs the workflow graph to process a study

        The steps performed to process a study are:
        1) Execute pick_closed_reference_otus.py
        2) Add the new processed data to the DB

        Parameters
        ----------
        preprocessed_data : PreprocessedData
            The preprocessed data to process
        params : BaseParameters
            The parameters to use for processing
        """
        self._logger = stderr
        self.preprocessed_data = preprocessed_data
        self.preprocessed_data.processing_status = "processing"

        if preprocessed_data.data_type() in TARGET_GENE_DATA_TYPES:
            cmd_generator = _get_process_target_gene_cmd
            insert_processed_data = _insert_processed_data_target_gene
        else:
            raise NotImplementedError(
                "Preprocessed data %s cannot be processed, data type %s "
                "not supported"
                % (preprocessed_data.id, preprocessed_data.data_type()))

        # Step 1: Process the study
        process_node = "PROCESS"
        cmd, output_dir = cmd_generator(preprocessed_data, params)
        self._job_graph.add_node(process_node,
                                 func=system_call,
                                 args=(cmd,),
                                 job_name="Process command",
                                 requires_deps=False)

        # Step 2: Add processed data to DB
        insert_processed_node = "INSERT_PROCESSED"
        self._job_graph.add_node(insert_processed_node,
                                 func=insert_processed_data,
                                 args=(self.preprocessed_data, params,
                                       output_dir),
                                 job_name="Store processed data",
                                 requires_deps=False)
        self._job_graph.add_edge(process_node, insert_processed_node)

        self._dirpaths_to_remove.append(output_dir)

    def _failure_callback(self, msg=None):
        """Callback to execute in case that any of the job nodes failed

        Need to change the preprocessed data process status to 'failed'
        """
        self.preprocessed_data.processing_status = 'failed: %s' % msg
        LogEntry.create('Fatal', msg,
                        info={'preprocessed_data': self.preprocessed_data.id})
