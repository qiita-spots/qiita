#!/usr/bin/env python
r"""HDF5 demultiplexed DDL

The full DDL is below. The summarized version is here:

    Attributes off of ./ for the full file:

    n         : int, the number of sequences
    max       : int, the max sequence length
    min       : int, the min sequence length
    mean      : float, the mean sequence length
    std       : float, the standard deviation of sequence length
    median    : float, the median sequence length

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

The full HDF5 DDL:

HDF5 "name_of_file.dmx" {
GROUP "/" {
   ATTRIBUTE "max" {
      DATATYPE  H5T_STD_I64LE
      DATASPACE  SCALAR
   }
   ATTRIBUTE "mean" {
      DATATYPE  H5T_IEEE_F64LE
      DATASPACE  SCALAR
   }
   ATTRIBUTE "min" {
      DATATYPE  H5T_STD_I64LE
      DATASPACE  SCALAR
   }
   ATTRIBUTE "n" {
      DATATYPE  H5T_STD_I64LE
      DATASPACE  SCALAR
   }
   ATTRIBUTE "std" {
      DATATYPE  H5T_IEEE_F64LE
      DATASPACE  SCALAR
   }
   GROUP "sample_name" {
      ATTRIBUTE "max" {
         DATATYPE  H5T_STD_I64LE
         DATASPACE  SCALAR
      }
      ATTRIBUTE "mean" {
         DATATYPE  H5T_IEEE_F64LE
         DATASPACE  SCALAR
      }
      ATTRIBUTE "min" {
         DATATYPE  H5T_STD_I64LE
         DATASPACE  SCALAR
      }
      ATTRIBUTE "n" {
         DATATYPE  H5T_STD_I64LE
         DATASPACE  SCALAR
      }
      ATTRIBUTE "std" {
         DATATYPE  H5T_IEEE_F64LE
         DATASPACE  SCALAR
      }
      GROUP "barcode" {
         DATASET "corrected" {
            DATATYPE  H5T_STRING {
               STRSIZE 12;
               STRPAD H5T_STR_NULLPAD;
               CSET H5T_CSET_ASCII;
               CTYPE H5T_C_S1;
            }
            DATASPACE  SIMPLE { ( N ) / ( N ) }
         }
         DATASET "error" {
            DATATYPE  H5T_STD_I64LE
            DATASPACE  SIMPLE { ( N ) / ( N ) }
         }
         DATASET "original" {
            DATATYPE  H5T_STRING {
               STRSIZE 12;
               STRPAD H5T_STR_NULLPAD;
               CSET H5T_CSET_ASCII;
               CTYPE H5T_C_S1;
            }
            DATASPACE  SIMPLE { ( N ) / ( N ) }
         }
      }
      DATASET "qual" {
         DATATYPE  H5T_STD_I64LE
         DATASPACE  SIMPLE { ( N, M ) / ( N, M ) }
      }
      DATASET "sequence" {
         DATATYPE  H5T_STRING {
            STRSIZE 151;
            STRPAD H5T_STR_NULLPAD;
            CSET H5T_CSET_ASCII;
            CTYPE H5T_C_S1;
         }
         DATASPACE  SIMPLE { ( N ) / ( M ) }
      }
   }
}
}
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
from collections import defaultdict, namedtuple

import h5py
import numpy as np
from future.utils import viewitems, viewvalues
from future.builtins import zip

from skbio.parse.sequences import load
from skbio.format.sequences import format_fastq_record

# track some basic stats about the samples
stat = namedtuple('stat', 'n max min mean median std')

# centralized incase paths change
dset_paths = {'sequence': 'sequence',
              'barcode_original': 'barcode/original',
              'barcode_corrected': 'barcode/corrected',
              'barcode_error': 'barcode/error',
              'qual': 'qual'}


class buffer_(object):
    """Buffer baseclass that sits on top of an HDF5 dataset

    Notes
    -----
    The intent of the buffer is to minimize direct writes against HDF5 datasets
    and to instead perform bulk operations against the h5py API. The 'stdio'
    driver for h5py also enables system buffers, but in practice, there is
    still a large amount of overhead when writing small pieces of data
    incrementally to h5py datasets.
    """
    def __init__(self, dset, mode, max_fill=10000):
        """Construct thy self

        Parameters
        ----------
        dset : h5py.Dataset
            The dataset to buffer
        max_fill : unsigned int
            The maximum fill for the buffer
        """
        self.dset = dset
        self.mode = mode

        self._current_fill = 0
        self._n = 0
        self._idx = 0
        self._max_fill = max_fill
        self._alloc()


    def __del__(self):
        """Flush when the buffer is deconstructed"""
        if self.mode == 'w':
            self.flush()

    def read(self):
        """Pull from dset into buffer"""
        if self.mode != 'r':
            raise IOError("Buffer is not in read mode!")

        if self.exhausted():
            self.fill()

        data = self._buf[self._n]
        self._n += 1

        return data

    def write(self, data):
        """Deposit into the buffer, write to dataset if necessary

        Parameters
        ----------
        data : scalar or np.array
            The data is dependent on the underlying buffer
        """
        if self.mode != 'w':
            raise IOError("Buffer is not in write mode!")

        self._write(data)
        self._n += 1

        if self.is_full():
            self.flush()

    def __iter__(self):
        while True:
            try:
                yield self.read()
            except IndexError:
                raise StopIteration

    def _write(self, data):
        raise NotImplementedError

    def _alloc(self):
        raise NotImplementedError

    def is_full(self):
        """Determine if the buffer is full"""
        return self._n >= self._max_fill

    def exhausted(self):
        """Determine if we've read through the buffer"""
        return (self._n >= self._current_fill) or (self._idx == 0)

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

    def fill(self):
        """Fill the buffer"""
        dset_size = self.dset.shape[0]
        start, end = self._idx, self._idx + self._max_fill

        if start >= dset_size:
            raise IndexError("Dataset exhausted!")

        # make sure we don't slice to far
        if end > dset_size:
            end = dset_size

        self._buf[:(end - start)] = self.dset[start:end]

        self._idx += end - start
        self._current_fill = end - start
        self._n = 0


class buffer1d(buffer_):
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


class buffer2d(buffer_):
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
        sample_id = record['SequenceID'].split('_', 1)[0]
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
        sample_stats[sid] = stat(n=lens.size, max=lens.max(), std=lens.std(),
                                 min=lens.min(), mean=lens.mean(),
                                 median=np.median(lens))

        all_lengths[pos:pos+lens.size] = lens
        pos += lens.size

    full_stats = stat(n=all_lengths.size, max=all_lengths.max(),
                      min=all_lengths.min(), std=all_lengths.std(),
                      mean=all_lengths.mean(), median=np.median(all_lengths))

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
        {str : buffer_} where str is the dataset path and the buffer_ is either
        `buffer1d` or `buffer2d`.
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
        return buftype(dset, 'w')

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
        buffers[path] = create_dataset(path, int, rows, cols)

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

    """
    # walk over the file and collect summary stats
    sample_stats, full_stats = _summarize_lengths(_per_sample_lengths(fp))

    # construct the datasets, storing per sample stats and full file stats
    buffers = _construct_datasets(sample_stats, h5file)
    _set_attr_stats(h5file, full_stats)
    h5file.attrs['has-qual'] = _has_qual(fp)

    for rec in load(fp):
        parts = rec['SequenceID'].split()
        sample = parts[0].rsplit('_', 1)[0]
        bc_diffs = int(parts[-1].split('=', 1)[1])
        corr_bc = parts[-2].split('=', 1)[1]
        orig_bc = parts[-3].split('=', 1)[1]

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
    """Consume a demux HDF5 file and yield fastq records

    Parameters
    ----------
    demux : h5py.File
        The demux file to operate on

    Returns
    -------
    generator
        A formatted fastq record
    """
    if demux.attrs['has-qual']:
        formatter = format_fastq_record
    else:
        formatter = format_fasta_record

    id_fmt = ("%(sample)s_%(idx)d orig_bc=%(bc_ori)s new_bc=%(bc_cor)s "
              "bc_diffs=%(bc_diff)d")

    if samples is None:
        samples = demux.keys()

    for sample in samples:
        pjoin = partial(os.path.join, sample)

        seq = buffer1d(demux[pjoin(dset_paths['sequence'])], 'r')
        qual = buffer2d(demux[pjoin(dset_paths['qual'])], 'r')
        bc_ori = buffer1d(demux[pjoin(dset_paths['barcode_original'])], 'r')
        bc_cor = buffer1d(demux[pjoin(dset_paths['barcode_corrected'])], 'r')
        bc_err = buffer1d(demux[pjoin(dset_paths['barcode_error'])], 'r')

        iter_ = zip(seq, qual, bc_ori, bc_cor, bc_err)
        for i, (s, q, o, c, e) in enumerate(iter_):
            seq_id = id_fmt % {'sample': sample, 'idx': i, 'bc_ori': o,
                               'bc_cor': c, 'bc_diff': e}
            yield formatter(seq_id, s, q)
