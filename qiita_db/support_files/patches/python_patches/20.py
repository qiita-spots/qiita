# Mar 27, 2015
# This patch relaxes the sample template metadata constraints on the database,
# so from now on they're going to be enforced by code, except
# required_sample_info_status which is completely deprecated
# This python patch is modifying the schema of the database, but given that
# a lot of data has to be moved before the SQL patches can be applied,
# they are added at the end of the queue, so all changes (data movements and
# schema changes) are done in a single transaction block

from qiita_db.sql_connection import SQLConnectionHandler

conn_handler = SQLConnectionHandler()

# Relaxing constraints on the Sample Template
# Retrieve all study ids that have a sample template
sql = """SELECT DISTINCT study_id from qiita.required_sample_info"""
study_ids = set(s[0] for s in conn_handler.execute_fetchall(sql))

queue_name = "PATCH_20"
conn_handler.create_queue(queue_name)

sql_select = """SELECT sample_id, physical_location, has_physical_specimen,
                       has_extracted_data, sample_type, collection_timestamp,
                       host_subject_id, description, latitude, longitude
                FROM qiita.required_sample_info
                WHERE study_id=%s"""

sql_cols = """INSERT INTO qiita.study_sample_columns
                (study_id, column_name, column_type)
              VALUES (%s, 'physical_specimen_location', 'varchar'),
                     (%s, 'physical_specimen_remaining', 'bool'),
                     (%s, 'dna_extracted', 'bool'),
                     (%s, 'sample_type', 'varchar'),
                     (%s, 'collection_timestamp', 'timestamp'),
                     (%s, 'host_subject_id', 'varchar'),
                     (%s, 'description', 'varchar'),
                     (%s, 'latitude', 'float8'),
                     (%s, 'longitude', 'float8')"""

sql_alter = """
ALTER TABLE qiita.{0} ADD COLUMN physical_specimen_location varchar;
ALTER TABLE qiita.{0} ADD COLUMN physical_specimen_remaining bool;
ALTER TABLE qiita.{0} ADD COLUMN dna_extracted bool;
ALTER TABLE qiita.{0} ADD COLUMN sample_type varchar;
ALTER TABLE qiita.{0} ADD COLUMN collection_timestamp timestamp;
ALTER TABLE qiita.{0} ADD COLUMN host_subject_id varchar;
ALTER TABLE qiita.{0} ADD COLUMN description varchar;
ALTER TABLE qiita.{0} ADD COLUMN latitude float8;
ALTER TABLE qiita.{0} ADD COLUMN longitude float8"""

sql_update = """UPDATE qiita.{0}
                SET physical_specimen_location=%s,
                    physical_specimen_remaining=%s,
                    dna_extracted=%s,
                    sample_type=%s,
                    collection_timestamp=%s,
                    host_subject_id=%s,
                    description=%s,
                    latitude=%s,
                    longitude=%s
                WHERE sample_id=%s"""

for s_id in study_ids:
    # Get the data from the requried_sample_info
    data = conn_handler.execute_fetchall(sql_select, (s_id,))

    # Add rows to the study_sample_columns table
    # 9 -> the number of rows that we are adding, see `sql_cols`
    conn_handler.add_to_queue(queue_name, sql_cols, [s_id] * 9)

    # Get the dynamic table name
    table_name = "sample_%d" % s_id

    # Add the columns to the dynamic table
    conn_handler.add_to_queue(queue_name, sql_alter.format(table_name))

    # Add the values for each sample
    for sample_data in data:
        sample_data = dict(sample_data)
        conn_handler.add_to_queue(
            queue_name, sql_update.format(table_name),
            (sample_data['physical_location'],
             sample_data['has_physical_specimen'],
             sample_data['has_extracted_data'],
             sample_data['sample_type'],
             sample_data['collection_timestamp'],
             sample_data['host_subject_id'],
             sample_data['description'],
             sample_data['latitude'],
             sample_data['longitude'],
             sample_data['sample_id']))

# Once all data has been moved, we can drop the columns from the
# requried_sample_info table; and drop the required_sample_info_status table
conn_handler.add_to_queue(
    queue_name,
    """ALTER TABLE qiita.required_sample_info
        DROP COLUMN physical_location""")
conn_handler.add_to_queue(
    queue_name,
    """ALTER TABLE qiita.required_sample_info
        DROP COLUMN has_physical_specimen""")
conn_handler.add_to_queue(
    queue_name,
    """ALTER TABLE qiita.required_sample_info
        DROP COLUMN has_extracted_data""")
conn_handler.add_to_queue(
    queue_name,
    """ALTER TABLE qiita.required_sample_info
        DROP COLUMN sample_type""")
conn_handler.add_to_queue(
    queue_name,
    """ALTER TABLE qiita.required_sample_info
        DROP COLUMN required_sample_info_status_id""")
conn_handler.add_to_queue(
    queue_name,
    """ALTER TABLE qiita.required_sample_info
        DROP COLUMN collection_timestamp""")
conn_handler.add_to_queue(
    queue_name,
    """ALTER TABLE qiita.required_sample_info
        DROP COLUMN host_subject_id""")
conn_handler.add_to_queue(
    queue_name,
    """ALTER TABLE qiita.required_sample_info
        DROP COLUMN description""")
conn_handler.add_to_queue(
    queue_name,
    """ALTER TABLE qiita.required_sample_info
        DROP COLUMN latitude""")
conn_handler.add_to_queue(
    queue_name,
    """ALTER TABLE qiita.required_sample_info
        DROP COLUMN longitude""")
conn_handler.add_to_queue(
    queue_name, """DROP TABLE qiita.required_sample_info_status""")

# Relaxing constrains on the prep template
# Retrieve all prep template ids
sql = """SELECT prep_template_id from qiita.prep_template"""
prep_ids = set(p[0] for p in conn_handler.execute_fetchall(sql))

sql_select = """SELECT sample_id, center_name, center_project_name, emp_status
                FROM qiita.common_prep_info
                    JOIN qiita.emp_status USING (emp_status_id)
                WHERE prep_template_id=%s"""

sql_cols = """INSERT INTO qiita.prep_columns
                (prep_template_id, column_name, column_type)
              VALUES (%s, 'center_name', 'varchar'),
                     (%s, 'center_project_name', 'varchar'),
                     (%s, 'emp_status', 'varchar')"""

sql_alter = """
ALTER TABLE qiita.{0} ADD COLUMN center_name varchar;
ALTER TABLE qiita.{0} ADD COLUMN center_project_name varchar;
ALTER TABLE qiita.{0} ADD COLUMN emp_status varchar"""

sql_update = """UPDATE qiita.{0}
                SET center_name=%s,
                    center_project_name=%s,
                    emp_status=%s
                WHERE sample_id=%s"""

for p_id in prep_ids:
    # Get the data from the common_prep_info
    data = conn_handler.execute_fetchall(sql_select, (p_id,))

    # Add rows to the prep_columns table
    # 3 -> the number of rows that we are adding, see `sql_cols`
    conn_handler.add_to_queue(queue_name, sql_cols, [p_id] * 3)

    # Get the dynamic table name
    table_name = "prep_%d" % p_id

    # Add the columns to the dynamic table
    conn_handler.add_to_queue(queue_name, sql_alter.format(table_name))

    # Add the values for each sample
    for sample_data in data:
        sample_data = dict(sample_data)
        conn_handler.add_to_queue(
            queue_name, sql_update.format(table_name),
            (sample_data['center_name'],
             sample_data['center_project_name'],
             sample_data['emp_status'],
             sample_data['sample_id']))

# Once all data has been moved, we can drop the columns from the
# common_prep_info table; and drop the emp_status table
conn_handler.add_to_queue(
    queue_name,
    """ALTER TABLE qiita.common_prep_info DROP COLUMN center_name""")
conn_handler.add_to_queue(
    queue_name,
    """ALTER TABLE qiita.common_prep_info DROP COLUMN center_project_name""")
conn_handler.add_to_queue(
    queue_name,
    """ALTER TABLE qiita.common_prep_info DROP COLUMN emp_status_id""")
conn_handler.add_to_queue(
    queue_name, """DROP TABLE qiita.emp_status""")

# All database changes have been added to the queue, execute the queue
conn_handler.execute_queue(queue_name)
