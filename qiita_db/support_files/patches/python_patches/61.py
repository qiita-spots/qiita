# October 30th, 2017
# A change introduced in July made all the parameters to be stored as strings
# The DB needs to be patched so all the artifacts follow this structure

from json import dumps

from qiita_db.sql_connection import TRN

with TRN:
    sql = """SELECT *
                FROM qiita.artifact
                    JOIN qiita.artifact_output_processing_job
                        USING (artifact_id)
                WHERE command_id IS NOT NULL"""
    TRN.add(sql)

    sql_update_artifact = """UPDATE qiita.artifact
                             SET command_parameters = %s
                             WHERE artifact_id = %s"""
    sql_update_job = """UPDATE qiita.processing_job
                        SET command_parameters = %s
                        WHERE processing_job_id = %s"""
    for ainfo in TRN.execute_fetchindex():
        ainfo = dict(ainfo)
        params = dumps(
            {k: str(v) for k, v in ainfo['command_parameters'].items()})
        TRN.add(sql_update_artifact, [params, ainfo['artifact_id']])
        TRN.add(sql_update_job, [params, ainfo['processing_job_id']])
