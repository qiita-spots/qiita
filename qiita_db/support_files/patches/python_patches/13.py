# 4 Jan, 2015
# This patch adds the default parameter set for OTU picking if it does not
# exist. If the Greengenes reference database does not exist in the DB,
# it requires the user input to provide the paths to the greengenes files

from qiita_db.sql_connection import SQLConnectionHandler
from qiita_db.reference import Reference


def user_input_path(msg):
    from os.path import isfile

    file_exists = False
    while not file_exists:
        user_path = raw_input(msg)
        file_exists = isfile(user_path)
    return user_path

conn_handler = SQLConnectionHandler()

# Check if the parameters already exist on the DB
params_exists = conn_handler.execute_fetchone(
    "SELECT EXISTS(SELECT * FROM qiita.processed_params_sortmerna)")[0]

if not params_exists:
    # The default parameters set does not exist.
    # Check if the Greengenes exist
    gg_id = conn_handler.execute_fetchone(
        "SELECT reference_id FROM qiita.reference "
        "WHERE reference_name=%s", ("Greengenes",))

    if gg_id:
        # The Greengenes reference already exists, fix the id
        gg_id = gg_id[0]
    else:
        # The Greengenes reference does not exist, ask the user for the
        # files so we can add it
        seq_path = user_input_path(
            "Insert the path to the Greengenes 97% fasta file: ")
        tax_path = user_input_path(
            "Insert the path to the Greengenes 97% taxonomy file: ")
        tree_path = user_input_path(
            "Insert the path to the Greengenes 97% tree file: ")
        gg_id = Reference.create('Greengenes', '13_8', seq_path,
                                 tax_path, tree_path).id

    # Add the default parameters set to the database
    conn_handler.execute(
        """INSERT INTO qiita.processed_params_sortmerna
            (reference_id, sortmerna_e_value, sortmerna_max_pos, similarity,
             sortmerna_coverage, threads)
           VALUES (%s, 1, 10000, 0.97, 0.97, 1)""", (gg_id, ))
