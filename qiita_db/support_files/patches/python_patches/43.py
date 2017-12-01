# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

import qiita_db as qdb
from future.utils import viewitems


PJ = qdb.processing_job.ProcessingJob

# selecting all artifact ids
with qdb.sql_connection.TRN:
    sql = """SELECT artifact_id FROM qiita.artifact"""
    qdb.sql_connection.TRN.add(sql, [])

    all_artifacts = qdb.sql_connection.TRN.execute_fetchindex()

nodes = {}
for aid in all_artifacts:
    aid = aid[0]
    with qdb.sql_connection.TRN:
        sql = """SELECT parent_id, artifact_id
                 FROM qiita.artifact_descendants(%s)"""
        qdb.sql_connection.TRN.add(sql, [aid])
        edges = [tuple(e)
                 for e in qdb.sql_connection.TRN.execute_fetchindex()]

    for parent, child in edges:
        # By creating all the artifacts here we are saving DB calls
        if parent not in nodes:
            nodes[parent] = qdb.artifact.Artifact(parent)
        if child not in nodes:
            nodes[child] = qdb.artifact.Artifact(child)

        job_id = None
        with qdb.sql_connection.TRN:
            sql = """SELECT processing_job_id
                     FROM qiita.artifact_processing_job
                        JOIN qiita.processing_job USING (processing_job_id)
                        JOIN qiita.processing_job_status USING
                            (processing_job_status_id)
                     WHERE artifact_id = %s"""
            qdb.sql_connection.TRN.add(sql, [nodes[parent].id])
            job_ids = qdb.sql_connection.TRN.execute_fetchflatten()

        for job_id in job_ids:
            job = qdb.processing_job.ProcessingJob(job_id)
            if job.status == 'success' and job.outputs:
                for _, a in viewitems(job.outputs):
                    if a.id == child:
                        job_id = job.id
                        break
        if job_id is None:
            # inserting the missing values

            c = nodes[child]
            cmd_out = c.artifact_type
            if cmd_out == 'Demultiplexed':
                cmd_out = 'demultiplexed'
            elif cmd_out == 'BIOM':
                cmd_out = 'OTU table'
            else:
                # the actual DB has other possible values in
                # artifact_type
                continue

            cmd_out_id = qdb.util.convert_to_id(
                        cmd_out, "command_output", "name")

            # the owner of the study will create the job
            job = PJ.create(c.study.owner, c.processing_parameters, True)
            with qdb.sql_connection.TRN:
                sql = """INSERT INTO
                            qiita.artifact_output_processing_job
                            (artifact_id, processing_job_id,
                            command_output_id)
                         VALUES (%s, %s, %s)"""
                qdb.sql_connection.TRN.add(
                    sql, [child, job.id, cmd_out_id])

            job._update_children({parent: child})
            job._set_status('success')
