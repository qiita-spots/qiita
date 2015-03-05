#Contributing to Qiita

Qiita is an open source software package, and we welcome community contributions. You can find the source code and test code for Qiita under public revision control in the Qiita git repository on [GitHub](http://github.com/biocore/qiita). We very much welcome contributions.

This document covers what you should do to get started with contributing to Qiita. You should read this whole document before considering submitting code to Qiita. This will save time for both you and the Qiita developers.

#General Notes on Development

Adding source code to Qiita, can take place in three different modules:

* `qiita_pet`: Contains the graphical user interface layer of the system.
* `qiita_db`: Contains the bridge layer between the python objects and the SQL database.
* `qiita_ware`: Contains the logic of the system and functions that can generally be called from a python script (see the scripts directory).

###Configuration file

The Qiita configuration file determines how the package interacts with your system’s resources (redis, postgres and the IPython cluster). Thus you should review the documentation detailed here (WE ARE STILL MISSING THIS LINK), but especially bear in mind the following points:

* An example version of this file can be found here `qiita_core/support_files/qiita_config.txt` and if you don’t set a `QIITA_CONFIG_FP` environment variable, that’s the file that Qiita will use.
* The `[main]` section sets a `TEST_ENVIRONMENT` variable, which determines whether your system will be running unit tests or if it a demo/production system. You will want to set the value to TRUE if you are running the unit tests.

**A note on data accumulation**: Qiita keeps data in the `BASE_DATA_DIR` as the system gets used. When you drop a Qiita environment and create a fresh testing environment, the “old” data that was generated from the previous environment should be **manually** deleted (or, at least, removed from the data directories in the `BASE_DATA_DIR`).

###Unit tests

Unit tests in Qiita are located inside the tests/test folder of every sub-module, for example `qiita_db/test/test_metadata_template.py`. These can be executed on a per-file basis or using `nosetests` from the base directory.

During test creation make sure the test class is decorated with `@qiita_test_checker()` if database modifications are done during tests. This will automatically drop and rebuild the qiita schema before each test case is executed.

Coverage testing is in effect, so run tests using `nosetests --with-coverage [test_file.py]` to check what lines of new code in your pull request are not tested.

###Scripts

Scripts in Qiita are located inside the scripts directory, their actions will rely on the settings described in the Qiita config file, for example if you are dropping a database, the database that will be dropped is the one described by the `DATABASE` setting. The following is a list of the most commonly used commands during development:

* `qiita_env make` will create a new environment (as specified by the Qiita config file).
* `qiita_env drop` will delete the environment (as specified by the Qiita config file).
* `qiita_env start_cluster qiita_general`, starts an IPython cluster named ‘qiita_general’. Normally you’ll want to wait a few seconds for the engines to start and become responsive (30-40 seconds depending on your system).
* `qiita_env stop_cluster qiita_general`, terminates a cluster named ‘qiita_general’.
* `qiita webserver start`, will start the Qiita web-application running on port 8888, you can change this using the `--port` flag, for example `--port=7532`.

##Making Database Changes
After the initial production release of Qiita, changes to the database schema will require patches; the database can no longer be dropped and recreated using the most recent schema because all the data would be lost! Therefore, patches must be applied instead.

###Approach

1. We keep "unpatched" versions of the SQL and DBS files in the repository
2. We keep fully patched versions of the DBS and HTML files in the repository
3. We keep a patch file for each patch as required in the `qiita_db/support_files/patches` directory. Note that **the patches will be applied in order based on the natural sort order of their filename** (e.g., `2.sql` will be applied before `10.sql`, and `10.sql` will be applied before `a.sql`)

###Developer Workflow

1. Load the fully patched DBS file (e.g., `qiita-db.dbs`) in [DBSchema](http://www.dbschema.com/)
2. Make desired changes
3. Save the DBS file *under a different name* (e.g., `foo.dbs`)
4. Select *Compare Schemas with Other Project From File* from the *Synchronization* menu
5. Compare `foo.dbs` with `qiita-db.dbs`
6. Click the button to prefer all of your new changes
7. Save the patch file with the next number (e.g., `1.sql`)
8. Edit the patch file and add general comments including a date, and (where necessary) specific comments

One drawback is that developers will need to have [DBSchema](http://www.dbschema.com/) to develop for this project.

###Data Patches

If you need to submit a patch that changes only data but does not alter the schema, you should still create a patch file with the next name (e.g., `2.sql`) with your changes. Note that a patch should *not* be created if the modifications do not apply to Qiita databases in general; data patches are only necessary in some cases, e.g., if the terms in an ontology change.

###Python Patches

Occasionally, SQL alone cannot effect the desired changes, and a corresponding python script must be run after the SQL patch is applied. If this is the case, a python file should be created in the `patches/python_patches` directory, and it should have the same basename as the SQL file. For example, if there is a patch `4.sql` in the `patches` directory, and this patch requires a python script be run after the SQL is applied, then the python file should be placed at `patches/python_patches/4.py`. Note that not every SQL patch will have a corresponding python patch, but every python patch will have a corresponding SQL patch.

If in the future we discover a use-case where a python patch must be applied for which there *is no corresponding SQL patch*, then a blank SQL patch file will still need to created.
