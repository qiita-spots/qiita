# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## ABSOLUTE HARD REQUIREMENTS
- NEVER use `rm` without permission

## Project Overview

Qiita (pronounced "cheetah") is an open-source platform for managing and analyzing 'omics data (microbiome, metabolomics, etc.). It provides a web GUI and CLI tools with support for third-party analysis plugins. Production instance: qiita.microbio.me.

## Architecture

Four main modules:
- **qiita_pet**: Web GUI layer — Tornado web framework, HTML templates, JavaScript (jQuery), REST API handlers
- **qiita_db**: Database bridge — Python ORM-like classes over PostgreSQL with inline SQL. Key models: Study, Artifact, Analysis, User, ProcessingJob, PrepTemplate, SampleTemplate, Software
- **qiita_ware**: Business logic — EBI submissions, private plugin execution, metadata pipelines, CLI operations
- **qiita_core**: Configuration management — reads config from `QIITA_CONFIG_FP` env var, environment setup utilities

Database interactions use `TRN` (transaction) objects with `TRN.add(sql, [params])` — never use Python string formatting for SQL parameters (psycopg2 parameterized queries only). Table/column names may use `str.format()`.

Plugins communicate via API proxy handlers in `qiita_pet/handlers/api_proxy/`.

## Priorities

1. Test Driven Development (TDD)
2. Correct code as verified by tests
3. Maintainable code, using Don't Repeat Yourself (DRY) and Keep It Simple Stupid (KISS)
4. Performance

## Runtime Requirements

- Python 3.9 (setup.py incorrectly says 3.6 — CI and INSTALL.md use 3.9)
- PostgreSQL 13
- Redis 2.8.17+ — typically two instances: main on port 7777, redbiom on 6379
- Full integration environment (what CI runs) also requires **webdis** (Redis HTTP bridge), **nginx**, and **supervisord** to drive multiple qiita workers. Canonical wiring lives in `qiita_pet/supervisor_example.conf` and `qiita_pet/nginx_example.conf`; see `.github/workflows/qiita-ci.yml` for the full startup sequence

## Configuration

- Template config: `qiita_core/support_files/config_test.cfg` — copy and point `QIITA_CONFIG_FP` at it
- Other env vars that matter: `REDBIOM_HOST`, `QIITA_ROOTCA_CERT`
- `QIITA_JOB_SCHEDULER_EPILOGUE` must be *set* for the test suite to run, but does not need to point at a real file (CI sets it to a placeholder path)

## Common Commands

```bash
# Environment setup
export QIITA_CONFIG_FP=/path/to/config.cfg
qiita-env make                    # Create database environment
qiita-env make --no-load-ontologies  # Faster env creation (skips ontology load; what CI uses)
qiita-env drop                    # Drop database environment
qiita-test-install                # Register test plugins after qiita-env make
qiita plugins update              # Refresh installed plugins after config changes

# Web server
qiita pet webserver start         # Start on port 21174
qiita pet webserver start --port=7532

# Linting
ruff check qiita_* setup.py scripts/qiita* notebooks/*/*.py

# Testing (uses pytest; testpaths configured in setup.cfg)
pytest qiita_db --cov=qiita_db -v                          # Full module
pytest qiita_pet qiita_core qiita_ware --cov               # Other modules
pytest qiita_db/test/test_artifact.py --cov=qiita_db        # Single file
```

CI specifics:
- qiita_db tests run separately from qiita_pet/qiita_core/qiita_ware tests due to schema rebuild overhead from `@qiita_test_checker`
- CI invokes `coverage run -m pytest`, not bare `pytest`
- The `qtp-biom` plugin must be installed for the full suite to pass
- Two flaky EBI tests are deselected: `test_submit_EBI_parse_EBI_reply_failure`, `test_full_submission`
- The `qiita_pet qiita_core qiita_ware` matrix leg runs three additional post-test checks that will not surface if you only run pytest locally: `test_data_studies/commands.sh` (CLI study creation), `all-qiita-cron-job` (cron smoke test), and the fresh-production-DB row-count validation above

## Testing Conventions

If a test produces an **incorrect expected value**: DO NOT change the expected value without permission.


- Tests live in `<module>/test/test_*.py`
- Use `@qiita_test_checker()` decorator (from `qiita_core.util`) on test classes that modify the database — this auto-drops and rebuilds the qiita schema after the test class runs
- All tests within a decorated class must be independent of each other (execution order is not guaranteed)
- Test framework: `unittest.TestCase` run with `pytest`

## Branch Structure

- **master**: Production code (deployed to qiita.microbio.me)
- **dev**: Active development — all PRs target this branch
- **release-candidate**: Staging/freeze before deployment

## Database Schema Changes

Schema changes require patch files, never direct modification of the base schema:
- Patches go in `qiita_db/support_files/patches/` (applied in natural sort order by filename, e.g., `92.sql` before `100.sql`)
- All patches prior to 92.sql were merged into the base schema (patch 91.sql consolidation, May 2024)
- Test-only SQL changes go in `patches/test_db_sql/`
- Python patches go in `patches/python_patches/` with the same basename as their SQL patch (e.g., `4.py` for `4.sql`)
- A freshly-created **production** environment (`TEST_ENVIRONMENT = FALSE`) must result in zero rows across the `qiita` schema — CI fails the job if the summed `reltuples` is nonzero, so patches must not pre-populate production data

## SQL Style

- SQL keywords UPPERCASED (`SELECT`, `FROM`, `WHERE`)
- Use triple-quoted strings for multi-line SQL, single-line strings for short queries
- PEP8-style indentation: new lines for `SELECT`, `FROM`, `WHERE`, `JOIN` clauses
- Assign SQL to a variable before passing to `TRN.add(sql, [params])`

## PR Guidelines

- Maximum 200 lines changed (HTML/DBS/test data don't count, JavaScript does)
- PRs that leave master inconsistent must go to a separate branch first
- Every PR must add or review the entry under the upcoming-release section in `CHANGELOG.md`
