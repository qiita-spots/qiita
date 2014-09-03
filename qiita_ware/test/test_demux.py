#!/usr/bin/env python

from __future__ import division

# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from os import remove
from unittest import TestCase, main

import h5py
import numpy as np
import numpy.testing as npt

from qiita_ware.demux import AutoExtendHDF5


class HDF5AutoExtendTests(TestCase):
    def setUp(self):
        self.hdf5_file = h5py.File('_test_file.hdf5','w')
        self.obj = AutoExtendHDF5(self.hdf5_file)

    def tearDown(self):
        remove('_test_file.hdf5')

    def test_create_dataset(self):
        """Create something"""
        self.obj.create_dataset('test_group/test_ds', int)
        self.assertEqual(np.array([0], int),
                         self.obj.f['test_group/test_ds'][:])
        self.assertEqual(self.obj._known_datasets, ['test_group/test_ds'])

    def test_append(self):
        """Check the implicit resizing"""
        name = 'test_group/test_ds'
        fetch = lambda x: x[name][:x[name].attrs['next_item']]
        size = lambda x: x[name].size

        self.obj.create_dataset(name, self.obj.vlenint)
        ds1 = np.array([1, 2, 3, 4])
        ds2 = np.array([5, 10, 20, 50])
        ds3 = np.array([44, 44, 44, 123, 123])
        ds4 = np.array([1])

        self.obj.append(name, ds1)
        npt.assert_equal(fetch(self.obj.f)[0], ds1)
        self.assertEqual(self.obj.f[name].attrs['next_item'], 1)
        self.assertEqual(size(self.obj.f), 1)

        self.obj.append(name, ds2)
        exp = [ds1, ds2]
        obs = fetch(self.obj.f)
        self.assert_jagged_equal(obs, exp)
        self.assertEqual(self.obj.f[name].attrs['next_item'], 2)
        self.assertEqual(size(self.obj.f), 2)

        self.obj.append(name, ds3)
        exp = [ds1, ds2, ds3]
        obs = fetch(self.obj.f)
        self.assert_jagged_equal(obs, exp)
        self.assertEqual(self.obj.f[name].attrs['next_item'], 3)
        self.assertEqual(size(self.obj.f), 4)

        self.obj.append(name, ds4)
        exp = [ds1, ds2, ds3, ds4]
        obs = fetch(self.obj.f)
        self.assert_jagged_equal(obs, exp)
        self.assertEqual(self.obj.f[name].attrs['next_item'], 4)
        self.assertEqual(size(self.obj.f), 4)

    def test_finalize(self):
        """Make sure we can finalize a dataset"""
        name = 'test_group/test_ds'
        fetch = lambda x: x[name][:]
        size = lambda x: x[name].size
        self.obj.create_dataset(name, self.obj.vlenint)
        self.obj.append(name, np.array([1, 2, 3]))
        self.obj.append(name, np.array([1, 2, 3]))
        self.obj.append(name, np.array([1, 2, 3]))
        self.obj.append(name, np.array([1, 2, 3]))
        self.obj.append(name, np.array([1, 2, 3]))

        self.assertEqual(size(self.obj.f), 8)
        exp = np.array([[1, 2, 3],
                        [1, 2, 3],
                        [1, 2, 3],
                        [1, 2, 3],
                        [1, 2, 3],
                        [0, 0, 0],
                        [0, 0, 0],
                        [0, 0, 0]])

        obs = fetch(self.obj.f)
        self.assert_jagged_equal(obs, exp)

        self.obj._finalize(name)
        exp = np.array([1, 2, 3] * 5).reshape(5, 3)
        obs = fetch(self.obj.f)
        self.assert_jagged_equal(obs, exp)

        self.assertFalse('next_item' in self.obj.f[name].attrs)

    def assert_jagged_equal(self, obs, exp):
        for o, e in zip(obs, exp):
            if not npt.assert_equal(o, e):
                return False
        return True

if __name__ == '__main__':
    main()
