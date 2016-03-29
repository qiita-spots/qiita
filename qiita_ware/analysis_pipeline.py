#!/usr/bin/env python
from __future__ import division
from os.path import join
from sys import stderr

from future.utils import viewitems
from biom import load_table

from qiita_db.job import Job
from qiita_db.reference import Reference
from qiita_db.software import Command
from qiita_db.logger import LogEntry
from qiita_db.util import get_db_files_base_dir
from qiita_ware.wrapper import ParallelWrapper, system_call_from_job


# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------


def _build_analysis_files(analysis, r_depth=None,
                          merge_duplicated_sample_ids=False, **kwargs):
    """Creates the biom tables and mapping file, then adds to jobs

    Parameters
    ----------
    analysis : Analysis object
        The analysis to build files for
    r_depth : int, optional
        Rarefaction depth for biom table creation. Default: None, no
        rarefaction is applied
    merge_duplicated_sample_ids : bool, optional
        If the duplicated sample ids in the selected studies should be
        merged or prepended with the artifact ids. False (default) prepends
        the artifact id

    Raises
    ------
    RuntimeError
        No jobs are attached to the given analysis
    """
    if not analysis.jobs:
        raise RuntimeError("Analysis %d has no jobs attached!" % analysis.id)

    # create the biom tables and add jobs to the analysis
    analysis.status = "running"
    analysis.build_files(r_depth, merge_duplicated_sample_ids)
    mapping_file = analysis.mapping_file
    biom_tables = analysis.biom_tables

    # add files to existing jobs
    for job in analysis.jobs:
        if job.status == 'queued':
            opts = {
                "--otu_table_fp": biom_tables[job.datatype],
                "--mapping_fp": mapping_file
            }
            job_opts = job.options
            job_opts.update(opts)
            job.options = job_opts


def _finish_analysis(analysis, **kwargs):
    """Checks job statuses and finalized analysis and redis communication

    Parameters
    ----------
    analysis: Analysis
        Analysis to finalize.
    kwargs : ignored
        Necessary to have in parameters to support execution via moi.
    """
    # check job exit statuses for analysis result status
    all_good = True
    for job in analysis.jobs:
        if job.status == "error":
            all_good = False
            break

    # set final analysis status
    if all_good:
        analysis.status = "completed"
    else:
        analysis.status = "error"


def _generate_analysis_tgz(analysis, **kwargs):
    """Generates the analysis tgz

    Parameters
    ----------
    analysis: Analysis
        Analysis to generate the tgz command from
    kwargs : ignored
        Necessary to have in parameters to support execution via moi.
    """
    from qiita_db.sql_connection import TRN
    from qiita_db.util import get_mountpoint, get_mountpoint_path_by_id
    from os.path import join
    from subprocess import Popen, PIPE

    fps_ids = analysis.all_associated_filepath_ids
    with TRN:
        sql = """SELECT filepath, data_directory_id FROM qiita.filepath
                    WHERE filepath_id IN %s"""
        TRN.add(sql, [tuple(fps_ids)])

        full_fps = [join(get_mountpoint_path_by_id(mid), f)
                    for f, mid in TRN.execute_fetchindex()]

        _, analysis_mp = get_mountpoint('analysis')[0]
        tgz = join(analysis_mp, '%d_files.tgz' % analysis.id)
        cmd = 'tar zcf %s %s' % (tgz, ' '.join(full_fps))

        proc = Popen(cmd, universal_newlines=True, shell=True, stdout=PIPE,
                     stderr=PIPE)
        stdout, stderr = proc.communicate()
        return_value = proc.returncode

        if return_value == 0:
            analysis._add_file(tgz, 'tgz')

    return stdout, stderr, return_value


class RunAnalysis(ParallelWrapper):
    def _construct_job_graph(self, analysis, commands, comm_opts=None,
                             rarefaction_depth=None,
                             merge_duplicated_sample_ids=False):
        """Builds the job graph for running an analysis

        Parameters
        ----------
        analysis: Analysis object
            Analysis to finalize.
        commands : list of tuples
            Commands to add as jobs in the analysis.
            Format [(data_type, command name), ...]
        comm_opts : dict of dicts, optional
            Options for commands. Format {command name: {opt1: value,...},...}
            Default None (use default options).
        rarefaction_depth : int, optional
            Rarefaction depth for analysis' biom tables. Default None.
        merge_duplicated_sample_ids : bool, optional
            If the duplicated sample ids in the selected studies should be
            merged or prepended with the artifact ids. False (default) prepends
            the artifact id
        """
        self._logger = stderr
        self.analysis = analysis
        analysis_id = analysis.id

        # Add jobs to analysis
        if comm_opts is None:
            comm_opts = {}

        tree_commands = ["Beta Diversity", "Alpha Rarefaction"]
        for data_type, biom_fp in viewitems(analysis.biom_tables):
            biom_table = load_table(biom_fp)
            # getting reference_id and software_command_id from the first
            # sample of the biom. This decision was discussed on the qiita
            # meeting on 02/24/16
            metadata = biom_table.metadata(biom_table.ids()[0])
            reference_id = metadata['reference_id']
            software_command_id = metadata['command_id']

            reference = Reference(reference_id)
            tree = reference.tree_fp

            for data_type, command in commands:
                # get opts set by user, else make it empty dict
                opts = comm_opts.get(command, {})
                if command in tree_commands:
                    if tree != '':
                        opts["--tree_fp"] = tree
                    else:
                        opts["--parameter_fp"] = join(
                            get_db_files_base_dir(), "reference",
                            "params_qiime.txt")

                if command == "Alpha Rarefaction":
                    opts["-n"] = 4

                Job.create(data_type, command, opts, analysis, reference,
                           Command(software_command_id), return_existing=True)

        # Create the files for the jobs
        files_node_name = "%d_ANALYSISFILES" % analysis_id
        self._job_graph.add_node(files_node_name,
                                 func=_build_analysis_files,
                                 args=(analysis, rarefaction_depth,
                                       merge_duplicated_sample_ids),
                                 job_name='Build analysis',
                                 requires_deps=False)

        # Add the jobs
        job_nodes = []
        for job in analysis.jobs:
            node_name = "%d_JOB_%d" % (analysis_id, job.id)
            job_nodes.append(node_name)
            job_name = "%s: %s" % (job.datatype, job.command[0])
            self._job_graph.add_node(node_name,
                                     func=system_call_from_job,
                                     args=(job.id,),
                                     job_name=job_name,
                                     requires_deps=False)

            # Adding the dependency edges to the graph
            self._job_graph.add_edge(files_node_name, node_name)

        # tgz-ing the analysis results
        tgz_node_name = "TGZ_ANALYSIS_%d" % (analysis_id)
        job_name = "tgz_analysis_%d" % (analysis_id)
        self._job_graph.add_node(tgz_node_name,
                                 func=_generate_analysis_tgz,
                                 args=(analysis,),
                                 job_name=job_name,
                                 requires_deps=False)
        # Adding the dependency edges to the graph
        for job_node_name in job_nodes:
            self._job_graph.add_edge(job_node_name, tgz_node_name)

        # Finalize the analysis.
        node_name = "FINISH_ANALYSIS_%d" % analysis.id
        self._job_graph.add_node(node_name,
                                 func=_finish_analysis,
                                 args=(analysis,),
                                 job_name='Finalize analysis',
                                 requires_deps=False)
        self._job_graph.add_edge(tgz_node_name, node_name)

    def _failure_callback(self, msg=None):
        """Executed if something fails"""
        # set the analysis to errored
        self.analysis.status = 'error'

        if self._update_status is not None:
            self._update_status("Failed")

        # set any jobs to errored if they didn't execute
        for job in self.analysis.jobs:
            if job.status not in {'error', 'completed'}:
                job.status = 'error'

        LogEntry.create('Runtime', msg, info={'analysis': self.analysis.id})
