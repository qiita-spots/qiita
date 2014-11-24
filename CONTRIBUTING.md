#Making Database Changes
After the initial production release of Qiita, changes to the database schema will require patches; the database can no longer be dropped and recreated using the most recent schema because all the data would be lost! Therefore, patches must be applied instead.

##Approach

1. We keep "unpatched" versions of the SQL and DBS files in the repository
2. We keep fully patched versions of the DBS and HTML files in the repository
3. We keep a patch file for each patch as required in the `qiita_db/support_files/patches` directory. Note that **the patches will be applied in order based on the natural sort order of their filename** (e.g., `2.sql` will be applied before `10.sql`, and `10.sql` will be applied before `a.sql`)

##Developer Workflow

1. Load the fully patched DBS file (e.g., `qiita-db.dbs`) in [DBSchema](http://www.dbschema.com/)
2. Make desired changes
3. Save the DBS file *under a different name* (e.g., `foo.dbs`)
4. Select *Compare Schemas with Other Project From File* from the *Synchronization* menu
5. Compare `foo.dbs` with `qiita-db.dbs`
6. Click the button to prefer all of your new changes
7. Save the patch file with the next number (e.g., `1.sql`)
8. Edit the patch file and add general comments including a date, and (where necessary) specific comments

One drawback is that developers will need to have [DBSchema](http://www.dbschema.com/) to develop for this project.

##Data Patches

If you need to submit a patch that changes only data but does not alter the schema, you should still create a patch file with the next name (e.g., `2.sql`) with your changes. Note that a patch should *not* be created if the modifications do not apply to Qiita databases in general; data patches are only necessary in some cases, e.g., if the terms in an ontology change.

##Python Patches

Occasionally, SQL alone cannot effect the desired changes, and a corresponding python script must be run after the SQL patch is applied. If this is the case, a python file should be created in the `patches/python_patches` directory, and it should have the same basename as the SQL file. For example, if there is a patch `4.sql` in the `patches` directory, and this patch requires a python script be run after the SQL is applied, then the python file should be placed at `patches/python_patches/4.py`. Note that not every SQL patch will have a corresponding python patch, but every python patch will have a corresponding SQL patch.

If in the future we discover a use-case where a python patch must be applied for which there *is no corresponding SQL patch*, then a blank SQL patch file will still need to created.