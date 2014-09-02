#!/usr/bin/env python

from __future__ import division

# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

import numpy as np

from unittest import TestCase, main

from qiita_ware.util import per_sample_sequences


def mock_sequence_iter(items):
    return ({'SequenceID': sid, 'Sequence': seq} for sid, seq in items)


class UtilTests(TestCase):
    def setUp(self):
        np.random.seed(123)

    def test_per_sample_sequences_simple(self):
        max_seqs = 10
        exp = sorted([('b_0', 'AATTGGCC-b2'),
                      ('a_0', 'AATTGGCC-a5'),
                      ('a_1', 'AATTGGCC-a1'),
                      ('a_2', 'AATTGGCC-a4'),
                      ('b_1', 'AATTGGCC-b1'),
                      ('a_3', 'AATTGGCC-a2'),
                      ('c_0', 'AATTGGCC-c3'),
                      ('a_4', 'AATTGGCC-a3'),
                      ('c_1', 'AATTGGCC-c1'),
                      ('c_2', 'AATTGGCC-c2')])
        obs = per_sample_sequences(mock_sequence_iter(sequences), max_seqs)
        self.assertEqual(sorted(obs), exp)

    def test_per_sample_sequences_complex(self):
        max_seqs = 2
        exp = sorted([('b_0', 'AATTGGCC-b2'),
                      ('b_1', 'AATTGGCC-b1'),
                      ('a_0', 'AATTGGCC-a2'),
                      ('a_1', 'AATTGGCC-a3'),
                      ('c_0', 'AATTGGCC-c1'),
                      ('c_1', 'AATTGGCC-c2')])
        obs = per_sample_sequences(mock_sequence_iter(sequences), max_seqs)
        self.assertEqual(sorted(obs), exp)


# comment indicates the expected random value
sequences = [
    ('a_1', 'AATTGGCC-a1'),  # 2, 3624216819017203053
    ('a_2', 'AATTGGCC-a2'),  # 5, 5278339153051796802
    ('b_1', 'AATTGGCC-b1'),  # 4, 4184670734919783522
    ('b_2', 'AATTGGCC-b2'),  # 0, 946590342492863505
    ('a_4', 'AATTGGCC-a4'),  # 3, 4048487933969823850
    ('a_3', 'AATTGGCC-a3'),  # 7, 7804936597957240377
    ('c_1', 'AATTGGCC-c1'),  # 8, 8868534167180302049
    ('a_5', 'AATTGGCC-a5'),  # 1, 3409506807702804593
    ('c_2', 'AATTGGCC-c2'),  # 9, 8871627813779918895
    ('c_3', 'AATTGGCC-c3')   # 6, 7233291490207274528
]


if __name__ == '__main__':
    main()
