from __future__ import division

# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

import os
import tempfile
from unittest import TestCase, main

import h5py
import numpy as np
import numpy.testing as npt

from qiita_ware.demux import (buffer1d, buffer2d, _has_qual,
                              _per_sample_lengths, _summarize_lengths,
                              _set_attr_stats, _construct_datasets, to_hdf5,
                              format_fasta_record, to_ascii, stat,
                              to_per_sample_ascii)


class BufferTests(TestCase):
    def setUp(self):
        self.dset_1d = np.zeros(100, dtype=int)
        self.dset_2d = np.zeros((100, 100), dtype=int)

    def test_init(self):
        b1d = buffer1d(self.dset_1d, max_fill=10)
        b2d = buffer2d(self.dset_2d, max_fill=10)

        npt.assert_equal(b1d.dset, self.dset_1d)
        npt.assert_equal(b2d.dset, self.dset_2d)
        self.assertEqual(b1d._n, 0)
        self.assertEqual(b2d._n, 0)
        self.assertEqual(b1d._idx, 0)
        self.assertEqual(b2d._idx, 0)
        self.assertEqual(b1d._max_fill, 10)
        self.assertEqual(b2d._max_fill, 10)
        npt.assert_equal(b1d._buf, np.zeros(10, dtype=int))
        npt.assert_equal(b2d._buf, np.zeros((10, 100), dtype=int))

    def test_write(self):
        b1d = buffer1d(self.dset_1d, max_fill=10)
        b2d = buffer2d(self.dset_2d, max_fill=10)

        exp1d = np.zeros(10, dtype=int)
        exp1d[:9] = np.arange(9)
        exp2d = np.zeros((10, 100), dtype=int)
        exp2d[:9, :9] = np.tril(np.repeat(np.arange(9), 9).reshape(9, 9).T)
        for i in np.arange(9):
            b1d.write(i)
            b2d.write(np.arange(i+1))

        npt.assert_equal(b1d._buf, exp1d)
        npt.assert_equal(b2d._buf, exp2d)

        for i in np.arange(2):
            b1d.write(i)
            b2d.write(np.arange(i+1))

        exp1d = np.zeros(10, dtype=int)
        exp1d[0] = 1
        exp2d = np.zeros((10, 100), dtype=int)
        exp2d[0, 1] = 1

        npt.assert_equal(b1d._buf, exp1d)
        npt.assert_equal(b2d._buf, exp2d)

    def test_is_full(self):
        b1d = buffer1d(self.dset_1d, max_fill=10)
        b2d = buffer2d(self.dset_2d, max_fill=10)

        self.assertFalse(b1d.is_full())
        self.assertFalse(b2d.is_full())

        b1d._n = 10
        b2d._n = 10

        self.assertTrue(b1d.is_full())
        self.assertTrue(b2d.is_full())

        b1d._n = 20
        b2d._n = 20

        self.assertTrue(b1d.is_full())
        self.assertTrue(b2d.is_full())

        b1d._n = 0
        b2d._n = 0

    def test_flush(self):
        # tested via write and destructor
        pass

    def test_destructor(self):
        b1d = buffer1d(self.dset_1d, max_fill=10)
        b2d = buffer2d(self.dset_2d, max_fill=10)

        for i in np.arange(9):
            b1d.write(i)
            b2d.write(np.arange(i+1))

        npt.assert_equal(b1d.dset, np.zeros(100, dtype=int))
        npt.assert_equal(b2d.dset, np.zeros((100, 100), dtype=int))

        del b1d
        del b2d

        exp1d = np.zeros(100, dtype=int)
        exp1d[:9] = np.arange(9)
        exp2d = np.zeros((100, 100), dtype=int)
        exp2d[:9, :9] = np.tril(np.repeat(np.arange(9), 9).reshape(9, 9).T)

        npt.assert_equal(self.dset_1d, exp1d)
        npt.assert_equal(self.dset_2d, exp2d)


class DemuxTests(TestCase):
    def setUp(self):
        self.hdf5_file = h5py.File('test', driver='core', backing_store=False)
        self.to_remove = []

    def tearDown(self):
        self.hdf5_file.close()
        for f in self.to_remove:
            os.remove(f)

    def test_has_qual(self):
        with tempfile.NamedTemporaryFile('r+', suffix='.fna') as f:
            f.write(seqdata)
            f.flush()
            f.seek(0)

            self.assertFalse(_has_qual(f.name))

        with tempfile.NamedTemporaryFile('r+', suffix='.fq') as f:
            f.write(fqdata)
            f.flush()
            f.seek(0)

            self.assertTrue(_has_qual(f.name))

    def test_per_sample_lengths(self):
        with tempfile.NamedTemporaryFile('r+', suffix='.fna') as f:
            f.write(seqdata)
            f.flush()
            f.seek(0)

            obs = _per_sample_lengths(f.name)

        exp = {'a': [1, 2, 3], 'b': [3, 4]}
        self.assertEqual(obs, exp)

        with tempfile.NamedTemporaryFile('r+', suffix='.fna') as f:
            f.write(seqdata_with_underscores)
            f.flush()
            f.seek(0)

            obs = _per_sample_lengths(f.name)

        exp = {'a_x': [1, 2, 3], 'b_x': [3, 4]}
        self.assertEqual(obs, exp)

    def test_summarize_lengths(self):
        lens = {'a': [1, 2, 3], 'b': [3, 4]}
        exp = ({'a': stat(min=1, max=3, std=.81649658092772603, mean=2.0,
                          median=2.0, n=3,
                          hist=np.array([1, 0, 0, 0, 0, 1, 0, 0, 0, 1]),
                          hist_edge=np.array([1., 1.2, 1.4, 1.6, 1.8, 2, 2.2,
                                              2.4, 2.6, 2.8, 3.])),
                'b': stat(min=3, max=4, std=0.5, mean=3.5, median=3.5, n=2,
                          hist=np.array([1, 0, 0, 0, 0, 0, 0, 0, 0, 1]),
                          hist_edge=np.array([3., 3.1, 3.2, 3.3, 3.4, 3.5, 3.6,
                                              3.7, 3.8, 3.9, 4.]))},
               stat(min=1, max=4, mean=2.6, median=3.0, std=1.019803902718557,
                    hist=np.array([1, 0, 0, 1, 0, 0, 2, 0, 0, 1]), n=5,
                    hist_edge=np.array([1., 1.3, 1.6, 1.9, 2.2, 2.5, 2.8, 3.1,
                                        3.4, 3.7, 4.])))
        obs_samp, obs_full = _summarize_lengths(lens)
        exp_samp, exp_full = exp

        self.assertEqual(len(obs_samp), 2)

        for k in obs_samp:
            self._stat_equal(obs_samp[k], exp_samp[k])
        self._stat_equal(obs_full, exp_full)

    def _stat_equal(self, obs, exp):
        self.assertEqual(obs.n, exp.n)
        self.assertEqual(obs.min, exp.min)
        self.assertEqual(obs.max, exp.max)
        self.assertEqual(obs.mean, exp.mean)
        self.assertEqual(obs.std, exp.std)
        self.assertEqual(obs.median, exp.median)
        npt.assert_equal(obs.hist, exp.hist)
        npt.assert_almost_equal(obs.hist_edge, exp.hist_edge)

    def test_set_attr_stats(self):
        s = stat(min=1, max=4, mean=2.6, median=3.0, std=1.019803902718557,
                 hist=np.array([1, 0, 0, 1, 0, 0, 2, 0, 0, 1]), n=5,
                 hist_edge=np.array([1., 1.3, 1.6, 1.9, 2.2, 2.5, 2.8, 3.1,
                                     3.4, 3.7, 4.]))
        _set_attr_stats(self.hdf5_file, s)
        self._attr_stat_equal(self.hdf5_file.attrs, s)

        self.hdf5_file.create_group('test')
        _set_attr_stats(self.hdf5_file['test'], s)
        self._attr_stat_equal(self.hdf5_file['test'].attrs, s)

    def _attr_stat_equal(self, attrs, stat_obj):
        self.assertEqual(attrs['n'], stat_obj.n)
        self.assertEqual(attrs['min'], stat_obj.min)
        self.assertEqual(attrs['max'], stat_obj.max)
        self.assertEqual(attrs['mean'], stat_obj.mean)
        self.assertEqual(attrs['median'], stat_obj.median)
        self.assertEqual(attrs['std'], stat_obj.std)
        npt.assert_equal(attrs['hist'], stat_obj.hist)
        npt.assert_almost_equal(attrs['hist_edge'], stat_obj.hist_edge)

    def test_construct_datasets(self):
        lens = {'a': [1, 2, 3], 'b': [3, 4]}
        sample_stats, _ = _summarize_lengths(lens)
        _construct_datasets(sample_stats, self.hdf5_file)

        self.assertEqual(len(self.hdf5_file.keys()), 2)
        self.assertTrue('a' in self.hdf5_file)
        self.assertTrue('a/sequence' in self.hdf5_file)
        self.assertTrue('a/qual' in self.hdf5_file)
        self.assertTrue('a/barcode/corrected' in self.hdf5_file)
        self.assertTrue('a/barcode/original' in self.hdf5_file)
        self.assertTrue('a/barcode/error' in self.hdf5_file)
        self.assertTrue(self.hdf5_file['a'].attrs['n'], 3)
        self.assertTrue('b' in self.hdf5_file)
        self.assertTrue('b/sequence' in self.hdf5_file)
        self.assertTrue('b/qual' in self.hdf5_file)
        self.assertTrue('b/barcode/corrected' in self.hdf5_file)
        self.assertTrue('b/barcode/original' in self.hdf5_file)
        self.assertTrue('b/barcode/error' in self.hdf5_file)
        self.assertTrue(self.hdf5_file['b'].attrs['n'], 2)

    def test_to_hdf5(self):
        with tempfile.NamedTemporaryFile('r+', suffix='.fna',
                                         delete=False) as f:
            f.write(seqdata)
            f.flush()
            f.close()

            to_hdf5(f.name, self.hdf5_file)
            self.to_remove.append(f.name)

        npt.assert_equal(self.hdf5_file['a/sequence'][:], np.array(["x", "xy",
                                                                    "xyz"]))
        npt.assert_equal(self.hdf5_file['a/qual'][:],
                         np.array([[0, 0, 0], [0, 0, 0], [0, 0, 0]]))
        npt.assert_equal(self.hdf5_file['a/barcode/original'][:],
                         np.array(["abc", "aby", "abz"]))
        npt.assert_equal(self.hdf5_file['a/barcode/corrected'][:],
                         np.array(["abc", "ybc", "zbc"]))
        npt.assert_equal(self.hdf5_file['a/barcode/error'][:],
                         np.array([0, 2, 3]))

        npt.assert_equal(self.hdf5_file['b/sequence'][:],
                         np.array(["xyz", "abcd"]))
        npt.assert_equal(self.hdf5_file['b/qual'][:],
                         np.array([[0, 0, 0, 0], [0, 0, 0, 0]]))
        npt.assert_equal(self.hdf5_file['b/barcode/original'][:],
                         np.array(["abx", "abw"]))
        npt.assert_equal(self.hdf5_file['b/barcode/corrected'][:],
                         np.array(["xbc", "wbc"]))
        npt.assert_equal(self.hdf5_file['b/barcode/error'][:],
                         np.array([1, 4]))

    def test_format_fasta_record(self):
        exp = ">a\nxyz\n"
        obs = format_fasta_record("a", "xyz", 'ignored')
        self.assertEqual(obs, exp)

    def test_to_ascii(self):
        with tempfile.NamedTemporaryFile('r+', suffix='.fq',
                                         delete=False) as f:
            f.write(fqdata)
            f.flush()
            f.close()
            to_hdf5(f.name, self.hdf5_file)
            self.to_remove.append(f.name)

        exp = [(b"@a_0 orig_bc=abc new_bc=abc bc_diffs=0\nxyz\n+\nABC\n"),
               (b"@b_0 orig_bc=abw new_bc=wbc bc_diffs=4\nqwe\n+\nDFG\n"),
               (b"@b_1 orig_bc=abw new_bc=wbc bc_diffs=4\nqwe\n+\nDEF\n")]

        obs = list(to_ascii(self.hdf5_file, samples=['a', 'b']))
        self.assertEqual(obs, exp)

    def test_to_per_sample_ascii(self):
        with tempfile.NamedTemporaryFile('r+', suffix='.fq',
                                         delete=False) as f:
            f.write(fqdata)
            f.flush()
            f.close()
            to_hdf5(f.name, self.hdf5_file)
            self.to_remove.append(f.name)

        exp = [('a', [(b"@a_0 orig_bc=abc new_bc=abc bc_diffs=0\nxyz\n+\n"
                       "ABC\n")]),
               ('b', [(b"@b_0 orig_bc=abw new_bc=wbc bc_diffs=4\nqwe\n+\n"
                       "DFG\n"),
                      (b"@b_1 orig_bc=abw new_bc=wbc bc_diffs=4\nqwe\n+\n"
                       "DEF\n")])]

        obs = [(s[0], list(s[1])) for s in to_per_sample_ascii(self.hdf5_file)]
        self.assertEqual(obs, exp)

    def test_fetch(self):
        # implicitly tested with test_to_ascii
        pass


seqdata = """>a_1 orig_bc=abc new_bc=abc bc_diffs=0
x
>b_1 orig_bc=abx new_bc=xbc bc_diffs=1
xyz
>a_3 orig_bc=aby new_bc=ybc bc_diffs=2
xy
>a_2 orig_bc=abz new_bc=zbc bc_diffs=3
xyz
>b_2 orig_bc=abw new_bc=wbc bc_diffs=4
abcd
"""

seqdata_with_underscores = """>a_x_1 orig_bc=abc new_bc=abc bc_diffs=0
x
>b_x_1 orig_bc=abx new_bc=xbc bc_diffs=1
xyz
>a_x_3 orig_bc=aby new_bc=ybc bc_diffs=2
xy
>a_x_2 orig_bc=abz new_bc=zbc bc_diffs=3
xyz
>b_x_2 orig_bc=abw new_bc=wbc bc_diffs=4
abcd
"""

fqdata = """@a_1 orig_bc=abc new_bc=abc bc_diffs=0
xyz
+
ABC
@b_1 orig_bc=abw new_bc=wbc bc_diffs=4
qwe
+
DFG
@b_2 orig_bc=abw new_bc=wbc bc_diffs=4
qwe
+
DEF
"""

if __name__ == '__main__':
    main()
