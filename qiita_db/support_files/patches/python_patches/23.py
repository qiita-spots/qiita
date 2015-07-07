# Mar 27, 2015
# Need to re-generate the files, given that some headers have changed

from qiita_db.sql_connection import TRN
from qiita_db.metadata_template import SampleTemplate, PrepTemplate

with TRN:
    # Get all the sample templates
    TRN.add("SELECT DISTINCT study_id from qiita.study_sample")
    study_ids = TRN.execute_fetchflatten()

    for s_id in study_ids:
        SampleTemplate(s_id).generate_files()

    # Get all the prep templates
    TRN.add("SELECT DISTINCT prep_template_id from qiita.prep_template")
    prep_ids = TRN.execute_fetchflatten()
    for prep_id in prep_ids:
        PrepTemplate(prep_id).generate_files()
