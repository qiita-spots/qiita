#!/usr/bin/env python
from __future__ import division
from json import dumps
from os.path import join

from redis import Redis

from qiita_db.job import Job
from qiita_db.util import get_db_files_base_dir

from qiita_ware.cluster import qiita_compute, system_call
from qiita_ware.exceptions import ComputeError


# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

r_server = Redis()


def _job_comm_wrapper(user, job, analysis_id, r_server=r_server):
    """Wraps the job command execution to allow redis communication"""
    name, command = job.command
    options = job.options
    # create json base for websocket messages
    msg = {
        "analysis": analysis_id,
        "msg": None,
        "command": "%s: %s" % (job.datatype, name)
    }

    o_fmt = ' '.join(['%s %s' % (k, v) for k, v in options.items()])
    c_fmt = str("%s %s" % (command, o_fmt))

    # send running message to user wait page
    job.status = 'running'
    msg["msg"] = "Running"
    print "!!!!!!!!!!!!!!!!!!!!!!! RUNNING %s!" % name
    r_server.rpush(user + ":messages", dumps(msg))
    r_server.publish(user, dumps(msg))

    # run the command
    try:
        system_call(c_fmt)
    except Exception as e:
        job.status = 'error'
        msg["msg"] = "ERROR"
        print "!!!!!!!!!!!!!!!!!!!!!!! ERROR %s!" % name
        r_server.rpush(user + ":messages", dumps(msg))
        r_server.publish(user, dumps(msg))
        raise RuntimeError("Failed compute on job id %d: %s\n%s" %
                           (job_id, e, c_fmt))

    msg["msg"] = "Completed"
    print "!!!!!!!!!!!!!!!!!!!!!!! COMPLETED %s!" % name
    r_server.rpush(user + ":messages", dumps(msg))
    r_server.publish(user, dumps(msg))
    # FIX THIS Should not be hard coded
    job.add_results([(options["--output_dir"], "directory")])
    job.status = 'completed'


def _run_wrapper(user, analysis, commands, rarefaction_depth):
    """Main function controlling an analysis run"""
    # create the biom tables and add jobs to the analysis
    print "!!!!!!!!!!!!!! WRAPPER START"
    analysis.build_files(rarefaction_depth)
    print "!!!!!!!!!!!!!! FILES BUILT"
    mapping_file = analysis.mapping_file
    biom_tables = analysis.biom_tables
    for data_type, command in commands:
        opts = {
            "--otu_table_fp": biom_tables[data_type],
            "--mapping_fp": mapping_file
        }
        # HARD CODED HACKY THING FOR DEMO, FIX  Issue #164
        if command == "Beta Diversity" and data_type in {'16S', '18S'}:
            opts["--tree_fp"] = join(get_db_files_base_dir(), "reference",
                                     "gg_97_otus_4feb2011.tre")
        elif command == "Beta Diversity":
            opts["--parameter_fp"] = join(get_db_files_base_dir(),
                                          "reference", "params_qiime.txt")
        job = Job.create(data_type, command, opts, analysis)

    # fire off jobs asynchronously, holding onto AsyncResult objects
    jobstats = []
    for job_id in analysis.jobs:
        job = Job(job_id)
        if job.status == 'queued':
            jobstats.append(qiita_compute.submit_async(
                _job_comm_wrapper, user, job, analysis.id))

    # wait until all jobs are done
    all_good = True
    for job in jobstats:
        job.wait()
        if not job.successful():
            all_good = False

    # send websockets message that we are done running all jobs
    msg["msg"] = "allcomplete"
    msg["command"] = ""
    r_server.rpush(user + ":messages", dumps(msg))
    r_server.publish(user, dumps(msg))
    # set final analysis status
    if all_good:
        analysis.status = "completed"
    else:
        analysis.status = "error"


def run_analysis(user, analysis, commands, rarefaction_depth=None):
    """Build the jobs for an analysis and run them all asynchronously

    user : User object
        user making the analysis
    analysis : analysis object
        the analysis to be run
    commands : list of tuples
        list of commands to add in the form [(command name, sys command)]
    rarefaction_depth : int, optional
        the rarefaction depth for biom table creation, if needed

    Notes
    -----
    This is a wrapper that just sets analysis to running and fires off the
    actual work in an async ipython call. This stops the function from blocking
    and offloads all the work to ipython.
    """
    analysis.status = "running"
    qiita_compute.submit_async(
        _run_wrapper, user, analysis, commands, rarefaction_depth)
