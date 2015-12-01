# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import TestCase, main
from os.path import isdir, exists, join
from os import remove, close
from shutil import rmtree
from tempfile import mkstemp, mkdtemp

from tgp.pick_otus import (write_parameters_file,
                           generate_pick_closed_reference_otus_cmd)


class PickOTUsTests(TestCase):
    def setUp(self):
        self._clean_up_files = []

    def tearDown(self):
        for fp in self._clean_up_files:
            if exists(fp):
                if isdir(fp):
                    rmtree(fp)
                else:
                    remove(fp)

    def test_write_parameters_file(self):
        parameters = {
            "reference": 1, "sortmerna_e_value": 1, "sortmerna_max_pos": 10000,
            "similarity": 0.97, "sortmerna_coverage": 0.97, "threads": 1,
            "input_data": 1}

        fd, fp = mkstemp()
        close(fd)
        self._clean_up_files.append(fp)

        write_parameters_file(fp, parameters)

        with open(fp, 'U') as f:
            obs = f.read()
        exp = EXP_PARAMS
        self.assertEqual(obs, exp)

    def test_generate_pick_closed_reference_otus_cmd(self):
        output_dir = mkdtemp()
        self._clean_up_files.append(output_dir)
        filepaths = [('/directory/seqs.fna', 'preprocessed_fasta'),
                     ('/directory/seqs.demux', 'preprocessed_demux')]
        parameters = {
            "reference": 1, "sortmerna_e_value": 1, "sortmerna_max_pos": 10000,
            "similarity": 0.97, "sortmerna_coverage": 0.97, "threads": 1,
            "input_data": 1}
        reference_fps = [('/directory/refseqs.fna', 'reference_seqs'),
                         ('/directory/reftax.txt', 'reference_tax'),
                         ('/directory/reftree.tre', 'reference_tree')]

        obs = generate_pick_closed_reference_otus_cmd(
            filepaths, output_dir, parameters, reference_fps)
        exp = ("pick_closed_reference_otus.py -i /directory/seqs.fna "
               "-r /directory/refseqs.fna -o {0}/cr_otus -p {0}/cr_params.txt "
               "-t /directory/reftax.txt".format(output_dir))
        self.assertEqual(obs, exp)

    def test_generate_pick_closed_reference_otus_cmd_valueerror(self):
        filepaths = [('/directory/seqs.log', 'log'),
                     ('/directory/seqs.demux', 'preprocessed_demux')]
        parameters = {
            "reference": 1, "sortmerna_e_value": 1, "sortmerna_max_pos": 10000,
            "similarity": 0.97, "sortmerna_coverage": 0.97, "threads": 1,
            "input_data": 1}
        reference_fps = [('/directory/refseqs.fna', 'reference_seqs'),
                         ('/directory/reftax.txt', 'reference_tax'),
                         ('/directory/reftree.tre', 'reference_tree')]
        output_dir = "/directory/out"

        with self.assertRaises(ValueError):
            generate_pick_closed_reference_otus_cmd(
                filepaths, output_dir, parameters, reference_fps)

EXP_PARAMS = """pick_otus:sortmerna_max_pos\t10000
pick_otus:similarity\t0.97
pick_otus:sortmerna_coverage\t0.97
pick_otus:threads\t1
"""

if __name__ == '__main__':
    main()
