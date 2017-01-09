# There are 2 things that need to be done in this patch:
# 1) Correct the rarefaction depth of the existing jobs and artifcats
# 2) Purge filepaths

from json import dumps

from biom import load_table

from qiita_db.util import purge_filepaths
from qiita_db.artifact import Artifact
from qiita_db.sql_connection import TRN


# 1) Correct the rarefaction depth of the existing jobs and artifcats
with TRN:
    sql = """SELECT command_id
             FROM qiita.software_command
             WHERE name = 'Single Rarefaction'"""
    TRN.add(sql)
    cmd_id = TRN.execute_fetchlast()

    sql = "SELECT artifact_id FROM qiita.artifact WHERE command_id = %s"
    TRN.add(sql, [cmd_id])

    sql_update_artifact = """UPDATE qiita.artifact
                             SET command_parameters = %s
                             WHERE artifact_id = %s"""
    sql_update_job = """UPDATE qiita.processing_job
                        SET command_parameters = %s
                        WHERE processing_job_id = (
                            SELECT processing_job_id
                            FROM qiita.artifact_output_processing_job
                            WHERE artifact_id = %s)"""

    for a_id in TRN.execute_fetchflatten():
        a = Artifact(a_id)
        params = a.processing_parameters.values
        # load the biom table to check the rarefaction depth
        # Magic numbers: since we added the artifacts on the patch 47.sql, we
        # know that these artifacts have only 1 file, hence the first 0.
        # Each element of the filepath list is a 3-tuple with filepath_id,
        # filepath and filepath type, and we are interested in the filepath
        # (index 1)
        t = load_table(a.filepaths[0][1])
        params['depth'] = t[:, 0].sum()
        TRN.add(sql_update_artifact, [dumps(params), a_id])
        TRN.add(sql_update_job, [dumps(params), a_id])

# 2) Purge filepaths
purge_filepaths()
