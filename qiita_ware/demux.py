r"""HDF5 demultiplexed DDL

Attributes off of ./ for the full file:

    n         : int, the number of sequences
    max       : int, the max sequence length
    min       : int, the min sequence length
    mean      : float, the mean sequence length
    std       : float, the standard deviation of sequence length
    median    : float, the median sequence length
    hist      : np.array of int, 10 bin histogram of sequence lengths
    hist_edge : np.array of int, left edge of each bin

Each sample has its own group with the following structure:

    ./<sample_name>/sequence          : (N,) of str where N is the number of \
sequences in the sample
    ./<sample_name>/qual              : (N, M) of int where N is the number \
of sequences in the sample, and M is the max sequence length (file-wide)
    ./<sample_name>/barcode/corrected : (N,) of str where N is the number of \
sequences in the sample
    ./<sample_name>/barcode/original  : (N,) of str where N is the number of \
sequences in the sample
    ./<sample_name>/barcode/error     : (N,) of int where N is the number of
sequences in the sample

Each sample additionally has the following attributes described on the
sample group:

    n         : int, the number of sequences
    max       : int, the max sequence length
    min       : int, the min sequence length
    mean      : float, the mean sequence length
    std       : float, the standard deviation of sequence length
    median    : float, the median sequence length
    hist      : np.array of int, 10 bin histogram of sequence lengths
    hist_edge : np.array of int, left edge of each bin

"""
from __future__ import division

# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

import os
from functools import partial
from itertools import repeat
from collections import defaultdict, namedtuple
from re import search

import numpy as np
from future.utils import viewitems, viewvalues
from future.builtins import zip
from skbio.parse.sequences import load
from skbio.format.sequences import format_fastq_record

from .util import open_file


# track some basic stats about the samples
stat = namedtuple('stat', 'n max min mean median std hist hist_edge')

# centralized in case paths change
dset_paths = {'sequence': 'sequence',
              'barcode_original': 'barcode/original',
              'barcode_corrected': 'barcode/corrected',
              'barcode_error': 'barcode/error',
              'qual': 'qual'}


class _buffer(object):
    """Buffer baseclass that sits on top of an HDF5 dataset

    Notes
    -----
    The intent of the buffer is to minimize direct writes against HDF5 datasets
    and to instead perform bulk operations against the h5py API. The 'stdio'
    driver for h5py also enables system buffers, but in practice, there is
    still a large amount of overhead when writing small pieces of data
    incrementally to h5py datasets.
    """
    def __init__(self, dset, max_fill=10000):
        """Construct thy self

        Parameters
        ----------
        dset : h5py.Dataset
            The dataset to buffer
        max_fill : unsigned int
            The maximum fill for the buffer
        """
        self.dset = dset

        self._n = 0
        self._idx = 0
        self._max_fill = max_fill
        self._alloc()

    def __del__(self):
        """Flush when the buffer is deconstructed"""
        if self._n > 0:
            self.flush()

    def write(self, data):
        """Deposit into the buffer, write to dataset if necessary

        Parameters
        ----------
        data : scalar or np.array
            The data is dependent on the underlying buffer
        """
        self._write(data)
        self._n += 1

        if self.is_full():
            self.flush()

    def _write(self, data):
        raise NotImplementedError

    def _alloc(self):
        raise NotImplementedError

    def is_full(self):
        """Determine if the buffer is full"""
        return self._n >= self._max_fill

    def flush(self):
        """Flush the buffer to the dataset

        Notes
        -----
        Buffer is zero'd out following the flush
        """
        # write
        start, end = self._idx, self._idx + self._n
        self.dset[start:end] = self._buf[:self._n]

        # zero out
        self._idx += self._n
        self._n = 0
        self._buf[:] = 0


class buffer1d(_buffer):
    """A 1 dimensional buffer

    Notes
    -----
    This buffer is useful for str or int. Strings, such as nucleotide
    sequences, can leverage this buffer if the strings are stored as strings
    and not char.
    """
    def _write(self, data):
        self._buf[self._n] = data

    def _alloc(self):
        self._buf = np.zeros(self._max_fill, self.dset.dtype)


class buffer2d(_buffer):
    """A 2 dimensional buffer

    Notes
    -----
    This buffer is useful for storing vectors of int or float. Qual scores,
    such as those commonly associated with nucleotide sequence data, can
    leverage this buffer as the qual scores are commonly represented as vectors
    of int.
    """
    def _write(self, data):
        self._buf[self._n, :data.size] = data

    def _alloc(self):
        shape = (self._max_fill, self.dset.shape[1])
        self._buf = np.zeros(shape, dtype=self.dset.dtype)


def _has_qual(fp):
    """Check if it looks like we have qual"""
    iter_ = load(fp)
    rec = next(iter(iter_))
    return rec['Qual'] is not None


def _per_sample_lengths(fp):
    """Determine the lengths of all sequences per sample

    Parameters
    ----------
    fp : filepath
        The sequence file to walk over

    Returns
    -------
    dict
        {sample_id: [sequence_length]}
    """
    lengths = defaultdict(list)
    for record in load(fp):
        sample_id = record['SequenceID'].split(' ')[0].rsplit('_', 1)[0]
        lengths[sample_id].append(len(record['Sequence']))

    return lengths


def _summarize_lengths(lengths):
    """Summarize lengths per sample

    Parameters
    ----------
    lengths : dict
        {sample_id: [sequence_length]}

    Returns
    -------
    dict
        {sample_id: sample_stat}
    stat
        The full file stats
    """
    sample_stats = {}
    all_lengths = np.zeros(sum([len(v) for v in viewvalues(lengths)]), int)
    pos = 0

    for sid, lens in viewitems(lengths):
        lens = np.array(lens)
        hist, edge = np.histogram(lens)
        sample_stats[sid] = stat(n=lens.size, max=lens.max(), std=lens.std(),
                                 min=lens.min(), mean=lens.mean(),
                                 median=np.median(lens), hist=hist,
                                 hist_edge=edge)

        all_lengths[pos:pos+lens.size] = lens
        pos += lens.size

    hist, edge = np.histogram(all_lengths)
    full_stats = stat(n=all_lengths.size, max=all_lengths.max(),
                      min=all_lengths.min(), std=all_lengths.std(),
                      mean=all_lengths.mean(), median=np.median(all_lengths),
                      hist=hist, hist_edge=edge)

    return sample_stats, full_stats


def _set_attr_stats(h5grp, stats):
    """Store stats in h5grp attrs

    Parameters
    ----------
    h5grp : h5py.Group or h5py.File
        The group or file to update .attrs on
    stats : stat
        The stats to record
    """
    h5grp.attrs['n'] = stats.n
    h5grp.attrs['mean'] = stats.mean
    h5grp.attrs['max'] = stats.max
    h5grp.attrs['min'] = stats.min
    h5grp.attrs['median'] = stats.median
    h5grp.attrs['std'] = stats.std
    h5grp.attrs['hist'] = stats.hist
    h5grp.attrs['hist_edge'] = stats.hist_edge


def _construct_datasets(sample_stats, h5file, max_barcode_length=12):
    """Construct the datasets within the h5file

    Parameters
    ----------
    sample_stats : dict
        {sample_id: stat}
    h5file : h5py.File
        The file to store the demux data

    Returns
    -------
    dict
        {str : _buffer} where str is the dataset path and the `_buffer` is
        either `buffer1d` or `buffer2d`.
    """
    def create_dataset(path, dtype, rows, cols):
        if cols == 1:
            shape = (rows,)
            buftype = buffer1d
        else:
            shape = (rows, cols)
            buftype = buffer2d

        kwargs = {'chunks': True, 'compression': True, 'compression_opts': 1}
        dset = h5file.create_dataset(path, dtype=dtype, shape=shape, **kwargs)
        return buftype(dset)

    buffers = {}

    for sid, stats in viewitems(sample_stats):
        # determine group
        pjoin = partial(os.path.join, sid)

        # setup dataset sizes and types
        rows = stats.n
        cols = stats.max
        seq_dtype = '|S%d' % cols
        bc_dtype = '|S%d' % max_barcode_length

        # construct datasets
        path = pjoin(dset_paths['sequence'])
        buffers[path] = create_dataset(path, seq_dtype, rows, 1)
        path = pjoin(dset_paths['barcode_original'])
        buffers[path] = create_dataset(path, bc_dtype, rows, 1)
        path = pjoin(dset_paths['barcode_corrected'])
        buffers[path] = create_dataset(path, bc_dtype, rows, 1)
        path = pjoin(dset_paths['barcode_error'])
        buffers[path] = create_dataset(path, int, rows, 1)
        path = pjoin(dset_paths['qual'])
        buffers[path] = create_dataset(path, np.uint8, rows, cols)

        # set stats
        _set_attr_stats(h5file[sid], stats)

    return buffers


def to_hdf5(fp, h5file, max_barcode_length=12):
    """Represent demux data in an h5file

    Parameters
    ----------
    fp : filepath
        The filepath containing either FASTA or FASTQ data.
    h5file : h5py.File
        The file to write into.

    Notes
    -----
    A group, per sample, will be created and within that group, 5 datasets will
    be constructed that correspond to sequence, original_barcode,
    corrected_barcode, barcode_errors, and qual.

    The filepath is required as two passes over the file are essential.

    The expectation is that the filepath being operated on is the result of
    split_libraries.py or split_libraries_fastq.py from QIIME. This code makes
    assumptions about items in the comment line that are added by split
    libraries. Specifically, the code looks for a "new_bc", an "ori_bc" and a
    "bc_diffs" field, and additionally assumes the sample ID is encoded in the
    ID.
    """
    # walk over the file and collect summary stats
    sample_stats, full_stats = _summarize_lengths(_per_sample_lengths(fp))

    # construct the datasets, storing per sample stats and full file stats
    buffers = _construct_datasets(sample_stats, h5file)
    _set_attr_stats(h5file, full_stats)
    h5file.attrs['has-qual'] = _has_qual(fp)

    for rec in load(fp):
        result = search((r'^(?P<sample>.+?)_\d+? .*orig_bc=(?P<orig_bc>.+?) '
                         'new_bc=(?P<corr_bc>.+?) bc_diffs=(?P<bc_diffs>\d+)'),
                        rec['SequenceID'])

        if result is None:
            raise ValueError("%s doesn't appear to be split libraries "
                             "output!" % fp)

        sample = result.group('sample')
        bc_diffs = result.group('bc_diffs')
        corr_bc = result.group('corr_bc')
        orig_bc = result.group('orig_bc')

        sequence = rec['Sequence']
        qual = rec['Qual']

        pjoin = partial(os.path.join, sample)
        buffers[pjoin(dset_paths['sequence'])].write(sequence)
        buffers[pjoin(dset_paths['barcode_original'])].write(orig_bc)
        buffers[pjoin(dset_paths['barcode_corrected'])].write(corr_bc)
        buffers[pjoin(dset_paths['barcode_error'])].write(bc_diffs)

        if qual is not None:
            buffers[pjoin(dset_paths['qual'])].write(qual)


def format_fasta_record(seqid, seq, qual):
    """Format a fasta record

    Parameters
    ----------
    seqid : str
        The sequence ID
    seq : str
        The sequence
    qual : ignored
        This is ignored

    Returns
    -------
    str
        A formatted sequence record
    """
    return b'\n'.join([b'>' + seqid, seq, b''])


def to_ascii(demux, samples=None):
    """Consume a demuxed HDF5 file and yield sequence records

    Parameters
    ----------
    demux : h5py.File
        The demux file to operate on
    samples : list, optional
        Samples to pull out. If None, then all samples will be examined.
        Defaults to None.

    Returns
    -------
    generator
        A formatted fasta or fastq record. The format is determined based on
        the presence/absence of qual scores. If qual scores exist, then fastq
        is returned, otherwise fasta is returned.
    """
    if demux.attrs['has-qual']:
        formatter = format_fastq_record
    else:
        formatter = format_fasta_record

    id_fmt = ("%(sample)s_%(idx)d orig_bc=%(bc_ori)s new_bc=%(bc_cor)s "
              "bc_diffs=%(bc_diff)d")

    if samples is None:
        samples = demux.keys()

    for samp, idx, seq, qual, bc_ori, bc_cor, bc_err in fetch(demux, samples):
        seq_id = id_fmt % {'sample': samp, 'idx': idx, 'bc_ori': bc_ori,
                           'bc_cor': bc_cor, 'bc_diff': bc_err}
        yield formatter(seq_id, seq, qual.astype(np.uint8))


def to_per_sample_ascii(demux, samples=None):
    """Consume a demuxxed HDF5 file and yield sequence records per sample

    Parameters
    ----------
    demux : h5py.File
        The demux file to operate on
    samples : list, optional
        Samples to pull out. If None, then all samples will be examined.
        Defaults to None.

    Returns
    -------
    sample : str
        The sample name
    generator
        A formatted fasta or fastq record. The format is determined based on
        the presence/absence of qual scores. If qual scores exist, then fastq
        is returned, otherwise fasta is returned.
    """
    if samples is None:
        samples = demux.keys()

    for samp in samples:
        yield samp, to_ascii(demux, samples=[samp])


def fetch(demux, samples=None, k=None):
    """Fetch sequences from a HDF5 demux file

    Parameters
    ----------
    demux : h5py.File
        The demux file to operate on.
    samples : list, optional
        Samples to pull out. If None, then all samples will be examined.
        Defaults to None.
    k : int, optional
        Randomly select (without replacement) k sequences from a sample. Only
        samples in which the number of sequences are >= k are considered. If
        None, all sequences for a sample are returned. Defaults to None.

    Returns
    -------
    generator
        Yields (sample, index, sequence, qual, original_barcode,
                corrected_barcode, barcode_error)
    """
    if samples is None:
        samples = demux.keys()

    for sample in samples:
        if sample not in demux:
            continue

        pjoin = partial(os.path.join, sample)

        # h5py only has partial fancy indexing support and it is limited to a
        # boolean vector.
        indices = np.ones(demux[sample].attrs['n'], dtype=bool)
        if k is not None:
            if demux[sample].attrs['n'] < k:
                continue

            to_keep = np.arange(demux[sample].attrs['n'])
            np.random.shuffle(to_keep)
            indices = np.logical_not(indices)
            indices[to_keep[:k]] = True

        seqs = demux[pjoin(dset_paths['sequence'])][indices]

        # only yield qual if we have it
        quals = repeat(None)
        if demux.attrs['has-qual']:
            if len(indices) == 1:
                if indices[0]:
                    quals = demux[pjoin(dset_paths['qual'])][:]
            else:
                quals = demux[pjoin(dset_paths['qual'])][indices, :]

        bc_original = demux[pjoin(dset_paths['barcode_original'])][indices]
        bc_corrected = demux[pjoin(dset_paths['barcode_corrected'])][indices]
        bc_error = demux[pjoin(dset_paths['barcode_error'])][indices]

        iter_ = zip(repeat(sample), np.arange(indices.size)[indices], seqs,
                    quals, bc_original, bc_corrected, bc_error)

        for item in iter_:
            yield item


def stats(demux):
    """Return file stats

    Parameters
    ----------
    demux : {str, h5py.File, h5py.Group}
        The file or group to get stats from

    Returns
    -------
    stat
        The corresponding stats
    """
    with open_file(demux) as fh:
        attrs = fh.attrs
        obs_stats = stat(n=attrs['n'],
                         max=attrs['max'],
                         min=attrs['min'],
                         std=attrs['std'],
                         mean=attrs['mean'],
                         median=attrs['median'],
                         hist=attrs['hist'],
                         hist_edge=attrs['hist_edge'])

    return obs_stats
