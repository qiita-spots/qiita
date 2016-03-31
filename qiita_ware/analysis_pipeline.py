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
    return analysis.generate_tgz()


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

        analysis.status = "running"
        # creating bioms at this point cause all this section runs on a worker
        # node, currently an ipython job
        analysis.build_files(rarefaction_depth, merge_duplicated_sample_ids)
        mapping_file = analysis.mapping_file

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

            for cmd_data_type, command in commands:
                if data_type != cmd_data_type:
                    continue

                # get opts set by user, else make it empty dict
                opts = comm_opts.get(command, {})
                opts["--otu_table_fp"] = biom_fp
                opts["--mapping_fp"] = mapping_file

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
