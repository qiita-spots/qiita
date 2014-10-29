# Changes to the Production Database Schema or Data

1. We keep "unpatched" versions of the SQL and DBS files in the repository
2. We keep fully patched versions of the SQL, DBS, and HTML files in the repository
3. We keep a patch files for each patch as required in a "patches" directory, named with a 4-digit number (e.g., 0000.sql)

The developer workflow for making changes to the database schema will be:

1. Load the fully patched DBS file (e.g., qiita-db.dbs)
2. Make desired changes
3. Save the DBS file under a different name (e.g., foo.dbs)
4. Select "Compare Schemas with Other Project From File" from the "Synchronization" menu
5. Compare foo.dbs with qiita-db.dbs
6. Click the button to prefer all of your new changes
7. Save the patch file with the next number (e.g., 0001.sql)
8. Edit the patch file and add general comments including a date, and (where necessary) specific comments

One drawback is that developers will need to have [DBSchema](http://www.dbschema.com/) to develop for this project.

If you need to submit a patch that changes only data but does not alter the schema, you should still create a patch file with the next ordinal name (e.g., 0002.sql) with your changes.
