#Contributing to Qiita

Qiita is an open source software package, and we welcome community contributions. You can find the source code and test code for Qiita under public revision control in the Qiita git repository on [GitHub](http://github.com/biocore/qiita). We very much welcome contributions.

This document covers what you should do to get started with contributing to Qiita. You should read this whole document before considering submitting code to Qiita. This will save time for both you and the Qiita developers.

#General Notes on Development

Adding source code to Qiita, can take place in three different modules:

* `qiita_pet`: Contains the graphical user interface layer of the system, mainly written in Python, JavaScript and HTML (see [Tornado templates](http://tornado.readthedocs.org/en/latest/template.html)).
* `qiita_db`: Contains the bridge layer between the Python objects and the SQL database. In general this subpackage is mainly written in Python with a fair amount of inline PostgreSQL statements (see the section below on how to make database changes).
* `qiita_ware`: Contains the logic of the system and functions that can generally be called from a Python script (see the scripts directory), and it is mostly written in Python. Several workflows that can be achieved using the GUI, can also be reproduced through the command line using this subpackage.

Regardless of the module where you are adding new functionality, you should
always take into consideration how these new features affect users and whether
or not adding a new section or document to the documentation (found under the
`doc` folder) would be useful.

###The Qiita development rules

Since Qiita is a package that is continuously growing, we found ourselves in a position where development rules needed to be established so we can reduce both development and reviewer time. These rules are:

1. Pull Requests (PR) should be small: maximum 200 lines
  1. HTML files and DBS files (from DBSchema) do not count, but JavaScript does
  2. Test data do not count toward the line limit
  3. PR over this limit will only be allowed if it has been discussed with the developer team and it can potentially be done in a different branch.
2. The code in the master branch should always be consistent. If your PR is leaving master in an inconsistent state, it's a red flag that more changes need to be done, and the code has to go to its own branch until all modifications get in (see 1. iii). Ideally, these branches should exist for a short period of time (~24h) before getting merged into master again, in order to avoid merge conflicts. This means that both developers and reviewers agree on working/reviewing these issues fast.
3. If you are changing code and the reviewers provide suggestions on how to improve the code, make the change unless you can demonstrate that your current implementation is better than the suggestion. Suggested changes must also explain why they are better when given, and make a reasonable case for the change. Examples:
  * For performance improvements, the reviewer should provide code using IPython's `%timeit` magic (or similar).
  * Point to the [Contributing.md](https://github.com/biocore/qiita/blob/master/CONTRIBUTING.md) and/or the Code Guidelines (under construction).
  * For User Interface (UI) changes, explain how usability will be improved or describe the difficulties you found in your first interaction with the interface.
  * Code readability improvements, as code that is difficult to understand is hard to maintain. If the first time a reviewer reads the code does not understand the code at all, it is a red flag that the code is not going to be maintained.
4. Avoid competing PR. If you're working on an issue that can conflict with another developer, coordinate with him/her to get the work done. If coordination proves difficult, include the rest of the development team in the discussion to determine the best way to proceed.
5. If you find an issue while working on a PR, you must either:
  * if it's a small change and completely unrelated to your PR, stage your changes, create a new branch and submit a PR. It will likely be merged fast and will reduce the time that issue is going to be present in the code base.
  * if it's a big issue, create an issue on GitHub, make sure someone is assigned to the issue, and add a comment in the code with the issue number (e.g. `# See issue #XXX`). This will help other developers to identify the the source of the issue and it will likely be solved faster.
6. Group issues in blocks that can be solved together. Using the GitHub's label system will be the best way to do this.
7. When you start working in a complex issue, discussing the path that you're going to take to solve it with other developers will help to identify potential problems in your solution and to make a correct definition of the issue scope. Starting the discussion in the GitHub issue tracker is recommended. If no consensus could be reached in some solution, moving the discussion to a meeting will be the path to move forward.
8. UI development is tricky and really subjective. In order to smooth the progress, this should be the path to develop the UI:
  1. Discuss as a group (in meetings or in the issue tracker) the overall design of the new UI.
  2. The developer assigned to the issue, will mock up some view in straight HTML or with a static tornado page, and shares the view with the rest of the developer team.
  3. The developer team reach a consensus in the new UI layout, by modifying the mock up and/or providing constructive feedback to the assigned developer. After all, the developer team will be the first users of the new UI, so if something smells fishy it will become a bigger problem for the end users.
  4. After a consensus is reached, the assigned developer implements the new UI.
  5. Once the PR is issued, another round of improvements can be done until a consensus is reached. Sometimes, the first consensus is not the best layout; and new ideas/improvements are always welcome!
9. Last but not least, you are working as part of a team and you should try to help others when possible.


###Configuration file

The Qiita configuration file determines how the package interacts with your system’s resources (redis, postgres and the IPython cluster). Thus you should review the documentation detailed [here](https://docs.google.com/document/d/1u7kwLP31NM513-8xwpwvLbSQxYu0ehI6Jau1APR13e0/edit#), but especially bear in mind the following points:

* An example version of this file can be found here `qiita_core/support_files/qiita_config.txt` and if you don’t set a `QIITA_CONFIG_FP` environment variable, that’s the file that Qiita will use.
* The `[main]` section sets a `TEST_ENVIRONMENT` variable, which determines whether your system will be running unit tests or if it a demo/production system. You will want to set the value to TRUE if you are running the unit tests.

**A note on data accumulation**: Qiita keeps data in the `BASE_DATA_DIR` as the system gets used. When you drop a Qiita environment and create a fresh testing environment, the “old” data that was generated from the previous environment should be **manually** deleted (or, at least, removed from the data directories in the `BASE_DATA_DIR`).

###Unit tests

Unit tests in Qiita are located inside the tests/test folder of every sub-module, for example `qiita_db/test/test_metadata_template.py`. These can be executed on a per-file basis or using `nosetests` from the base directory.

During test creation make sure the test class is decorated with `@qiita_test_checker()` if database modifications are done during tests. This will automatically drop and rebuild the qiita schema before each test case is executed.

Coverage testing is in effect, so run tests using `nosetests --with-coverage [test_file.py]` to check what lines of new code in your pull request are not tested.

###Documentation

The documentation for Qiita is maintained as part of this repository, under the
`qiita_pet/support_files/doc` folder, for more information, see the README.md
file in `qiita_pet/support_files/doc/README.md`.

###Scripts

Scripts in Qiita are located inside the scripts directory, their actions will rely on the settings described in the Qiita config file, for example if you are dropping a database, the database that will be dropped is the one described by the `DATABASE` setting. The following is a list of the most commonly used commands during development:

* `qiita-env make` will create a new environment (as specified by the Qiita config file).
* `qiita-env drop` will delete the environment (as specified by the Qiita config file).
* `qiita-env start_cluster qiita-general`, starts an IPython cluster named ‘qiita-general’. Normally you’ll want to wait a few seconds for the engines to start and become responsive (30-40 seconds depending on your system).
* `qiita-env stop_cluster qiita-general`, terminates a cluster named ‘qiita-general’.
* `qiita pet webserver start`, will start the Qiita web-application running on port 21174, you can change this using the `--port` flag, for example `--port=7532`.

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

##SQL coding guidelines
Since the `qiita_db` code contains a mixture of python code and SQL code, here are some coding guidelines to add the SQL code to Qiita:

1. Any SQL keyword should be written uppercased:
  * Wrong: `select * from qiita.qiita_user`
  * Correct: `SELECT * FROM qiita.qiita_user`
2. Triple quotes are preferred for the SQL statements, unless the statement fits in a single line:
  * Wrong:
```python
sql = "SELECT processed_data_status FROM qiita.processed_data_status pds JOIN "
      "qiita.processed_data pd USING (processed_data_status_id) JOIN "
      "qiita.study_processed_data spd USING (processed_data_id) "
      "WHERE spd.study_id = %s"
```
  * Correct:
```python
sql = """SELECT processed_data_status
         FROM qiita.processed_data_status pds
            JOIN qiita.processed_data pd USING (processed_data_status_id)
            JOIN qiita.study_processed_data spd USING (processed_data_id)
         WHERE spd.study_id = %s"""
```