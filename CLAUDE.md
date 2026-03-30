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

Plugins communicate via API proxy handlers in `qiita_db/handlers/api_proxy/`.

## Priorities

1. Test Driven Development (TDD)
2. Correct code as verified by tests
3. Maintainable code, using Don't Repeat Yourself (DRY) and Keep It Simple Stupid (KISS)
4. Performance

## Common Commands

```bash
# Environment setup
export QIITA_CONFIG_FP=/path/to/config.cfg
qiita-env make                    # Create database environment
qiita-env drop                    # Drop database environment

# Web server
qiita pet webserver start         # Start on port 21174
qiita pet webserver start --port=7532

# Linting
ruff check qiita_* setup.py scripts/qiita* notebooks/*/*.py

# Testing (uses nosetests)
nosetests qiita_db --with-coverage -v                    # Full module
nosetests qiita_pet qiita_core qiita_ware --with-coverage  # Other modules
nosetests qiita_db/test/test_artifact.py --with-coverage    # Single file
```

CI runs qiita_db tests separately from qiita_pet/qiita_core/qiita_ware tests.

## Testing Conventions

If a test produces an **incorrect expected value**: DO NOT change the expected value without permission.


- Tests live in `<module>/test/test_*.py`
- Use `@qiita_test_checker()` decorator (from `qiita_core.util`) on test classes that modify the database — this auto-drops and rebuilds the qiita schema after the test class runs
- All tests within a decorated class must be independent of each other (execution order is not guaranteed)
- Test framework: `unittest.TestCase` run with `nosetests`

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

## SQL Style

- SQL keywords UPPERCASED (`SELECT`, `FROM`, `WHERE`)
- Use triple-quoted strings for multi-line SQL, single-line strings for short queries
- PEP8-style indentation: new lines for `SELECT`, `FROM`, `WHERE`, `JOIN` clauses
- Assign SQL to a variable before passing to `TRN.add(sql, [params])`

## PR Guidelines

- Maximum 200 lines changed (HTML/DBS/test data don't count, JavaScript does)
- PRs that leave master inconsistent must go to a separate branch first
