# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------


def process_study(raw_data):
    """
    Parameters
    ----------
    raw_data : RawData
        The raw data object to process

    Notes
    -----
    TODO: it only performs closed reference OTU picking against gg 13 8
    """
    # Step 1: split libraries (demultiplexing + quality filtering)
    # We get the filepaths from the raw data object
    cmd = "split_libraries_fastq.py -i %s -b %s -m %s -o %s %s"
    # Step 2: otu picking
    cmd = "pick_closed_reference_otus.py -i %s -r %s -o %s -t %s"
