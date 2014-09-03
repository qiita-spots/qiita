#!/usr/bin/env python
from __future__ import division
from json import dumps

from redis import Redis

from qiita_db.job import Job

from qiita_ware.cluster import qiita_compute
from qiita_ware.exceptions import ComputeError


# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

r_server = Redis()


def run_analysis(user, analysis):
    """Run the commands within an Analysis object and sends user messages"""
    analysis.status = "running"
    all_good = True
    pubsub = r_server.pubsub()
    pubsub.subscribe(user)
    print "!!!!!!!!!!!!!!!! JOBS", analysis.jobs
    for job_id in analysis.jobs:
        job = Job(job_id)
        if job.status == 'queued':
            name, command = job.command
            options = job.options
            # create json base for websocket messages
            msg = {
                "analysis": analysis.id,
                "msg": None,
                "command": "%s: %s" % (job.datatype, name)
            }

            o_fmt = ' '.join(['%s %s' % (k, v) for k, v in options.items()])
            c_fmt = str("%s %s" % (command, o_fmt))

            # send running message to user wait page
            job.status = 'running'
            msg["msg"] = "Running"
            print "!!!!!!!!!!!!!!!!!!!!!!! RUNNING!"
            r_server.rpush(user + ":messages", dumps(msg))
            r_server.publish(user, dumps(msg))

            # run the command
            try:
                qiita_compute.submit_async(c_fmt)
            except Exception as e:
                all_good = False
                job.status = 'error'
                msg["msg"] = "ERROR"
                print "!!!!!!!!!!!!!!!!!!!!!!! ERROR!"
                r_server.rpush(user + ":messages", dumps(msg))
                r_server.publish(user, dumps(msg))
                print("Failed compute on job id %d: %s\n%s" %
                      (job_id, e, c_fmt))
                continue

            msg["msg"] = "Completed"
            print "!!!!!!!!!!!!!!!!!!!!!!! COMPLETED!"
            r_server.rpush(user + ":messages", dumps(msg))
            r_server.publish(user, dumps(msg))
            # FIX THIS Should not be hard coded
            job.add_results([(options["--output_dir"], "directory")])
            job.status = 'completed'

    # send websockets message that we are done
    msg["msg"] = "allcomplete"
    msg["command"] = ""
    r_server.rpush(user + ":messages", dumps(msg))
    r_server.publish(user, dumps(msg))
    pubsub.unsubscribe()
    # set final analysis status
    if all_good:
        analysis.status = "completed"
    else:
        analysis.status = "error"
