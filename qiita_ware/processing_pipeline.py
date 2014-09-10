# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from tempfile import mkstemp, mkdtemp
from os import close

from qiita_db.metadata_template import PrepTemplate


def _preprocess_study(study, raw_data):
    """
    Parameters
    ----------
    study : Study
        The study object where the data belongs to
    raw_data : RawData
        The raw data object to process
    """
    # Step 1: split libraries (demultiplexing + quality filtering)
    # We get the filepaths from the raw data object
    seqs_fps = []
    barcode_fps = []
    for fp, fp_type in raw_data.get_filepaths():
        if fp_type == "raw_sequences":
            seqs_fps.append(fp)
        elif fp_type == "raw_barcodes":
            barcode_fps.append(fp)
        else:
            raise ValueError("Raw data file type not supported %s" % fp_type)

    # We need to get the prep template in order to run split libraries
    prep_template = PrepTemplate(raw_data.id)

    # We have to write it to a temporary file, since QIIME needs a filepath
    fd, prep_fp = mkstemp(prefix="qiita_prep_%s" % prep_template.id,
                          suffix='.txt')
    close(fd)
    prep_template.to_file(prep_fp)

    # Create a temporary directory to store the split libraries output
    output_fp = mkdtemp(prefix='slq_out')

    # Add any other parameter needed to split libraries fastq
    params = ""

    # Build the command to run split libraries
    cmd = ("split_libraries_fastq.py -i %s -b %s -m %s -o %s %s"
           % (seqs_fps, barcode_fps, prep_fp, output_dir, params))

    # Run the commands


def process_study(study, raw_data):
    """
    Parameters
    ----------
    study : Study
        The study object where the data belongs to
    raw_data : RawData
        The raw data object to process

    Notes
    -----
    TODO: it only performs closed reference OTU picking against gg 13 8
    """
    # Step 1: split libraries (demultiplexing + quality filtering)
    _preprocess_study(study, raw_data)

    # Step 2: otu picking
    cmd = "pick_closed_reference_otus.py -i %s -r %s -o %s -t %s"
