import qiita_db as qdb


# selecting all doi/pubmedids
with qdb.sql_connection.TRN:
    sql = """SELECT p.doi, pubmed_id, study_id
               FROM qiita.study_publication AS sp
               LEFT JOIN qiita.publication AS p ON (sp.publication = p.doi)
               WHERE p.doi NOT IN (
                 SELECT publication_doi FROM qiita.software_publication)"""
    qdb.sql_connection.TRN.add(sql)

    pubs = qdb.sql_connection.TRN.execute_fetchindex()

    # deleting all references to start from scratch
    sql = """DELETE FROM qiita.study_publication"""
    qdb.sql_connection.TRN.add(sql)
    qdb.sql_connection.TRN.execute()

    # reinserting following the new structure
    for doi, pid, sid in pubs:
        to_insert = []
        if doi is not None:
            to_insert.append([doi, True, sid])
        if pid not in to_insert:
            to_insert.append([pid, False, sid])

            sql = """INSERT INTO qiita.study_publication
                       (publication, is_doi, study_id)
                     VALUES (%s, %s, %s)"""
            qdb.sql_connection.TRN.add(sql, to_insert, many=True)
    qdb.sql_connection.TRN.execute()
