#!/usr/bin/env python

from __future__ import division

# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

import h5py
import numpy as np


def to_demux(iter_, h5file):
    """Represent demux data in an h5grp

    Parameters
    ----------
    iter_ : skbio.parse.sequences.SequenceIterator
        The sequence iterator providing data.
    h5grp : h5py.File
        The file to write into.

    Notes
    -----
    A group, per sample, will be created and within that group, 5 datasets will
    be constructed that correspond to sequence, original_barcode,
    corrected_barcode, barcode_errors, and qual.

    """
    pass


class AutoExtendHDF5(object):
    """Allow for implicitly extendable datasets"""
    vlenstr = h5py.special_dtype(vlen=str)
    vlenint = h5py.special_dtype(vlen=np.dtype('int32'))

    def __init__(self, f):
        self.f = f
        self._known_datasets = []

    def __del__(self):
        for n in self._known_datasets:
            self._finalize(n)

    def create_dataset(self, name, dtype):
        """Create a tracked dataset that will automatically reshape"""
        self.f.create_dataset(name, shape=(1,), maxshape=(None,),
                              chunks=True, dtype=dtype)
        self.f[name].attrs['next_item'] = 0  # idx to write next
        self._known_datasets.append(name)

    def append(self, name, data, growth_factor=1):
        """Append an automatically growable dataset"""
        next_item = self.f[name].attrs['next_item']

        # resize as needed
        if next_item >= self.f[name].size:
            new_size = int(self.f[name].size + next_item * growth_factor)
            self.f[name].resize((new_size,))

        # store the data
        self.f[name][next_item] = data
        self.f[name].attrs['next_item'] += 1

    def _finalize(self, name):
        """Resize a dataset to its correct size"""
        actual_size = self.f[name].attrs.get('next_item', None)

        if actual_size is None:
            return

        self.f[name].resize((actual_size,))
        del self.f[name].attrs['next_item']
