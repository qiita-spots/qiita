# Code Review — Summary of Recommendations

Generated: 2026-03-30

## Fixed

| # | Issue | Location | Status |
|---|-------|----------|--------|
| 1 | Auth bypass — added `return` after `_set_error()` in INSDC_download | `qiita_ware/private_plugin.py:456` | Done |
| 2 | Added `@authenticated` to `UserMessagesHandler.post()` | `qiita_pet/handlers/user_handlers.py:397` | Done |
| 3 | Open redirect — validate `next` param is same-origin via `urlparse` | `qiita_pet/handlers/auth_handlers.py:145-156` | Done |
| 4 | Replaced `shell=True` with list args in launchers and `launch_local()` | `scripts/qiita-private-launcher:40-41`, `scripts/qiita-private-launcher-slurm:51-57`, `qiita_db/processing_job.py:228-232` | Done |
| 5 | Used `shlex.quote()` for SSH command | `qiita_ware/commands.py:89` | Done |

## Fix Short-Term

| # | Issue | Location | Effort |
|---|-------|----------|--------|
| 6 | Replace `{% raw %}` with proper escaping for user content (study notes, system messages) | `qiita_pet/templates/study_ajax/base_info.html:214`, `qiita_pet/templates/sitebase.html:14-17` | Medium |
| 7 | Sanitize `bootstrapAlert()` — use `.text()` or DOMPurify | `qiita_pet/static/js/qiita.js:13-25` | Small |
| 8 | Add try-finally for SSH connections and file handles | `qiita_ware/commands.py:150-169,321-323` | Small |
| 9 | Add security headers (CSP, X-Frame-Options, HSTS) to Tornado config | `qiita_pet/webserver.py:359-365` | Small |
| 10 | Pin `qiita-files` and `supervisor` to specific versions/tags | `setup.py:145,150` | Small |

## Fix Medium-Term

| # | Issue | Location | Effort |
|---|-------|----------|--------|
| 11 | Implement CSRF token handling across AJAX calls | Multiple handlers in `qiita_pet/handlers/` | Large |
| 12 | Migrate from `nose` to `pytest` | `setup.py:125,142` | Large |
| 13 | Update `collections.Iterable` to `collections.abc.Iterable` | `qiita_db/processing_job.py:9` | 1 line |
| 14 | Add version lower bounds to dependencies | `setup.py:113-144` | Small |
| 15 | Replace credential-in-environment patterns with safer alternatives | `qiita_ware/commands.py:294-327` | Medium |
