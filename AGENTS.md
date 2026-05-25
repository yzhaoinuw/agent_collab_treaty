# Guidelines and Tips for Agents

This file is the first thing any agent (Claude, Codex, or other) should read when joining a session on this repo. It defines the runtime, the common tasks, the conventions, and the project-specific reminders. Keep it short and current.

## Runtime Environment

When running code, tests, or the application for this repository, use:

- [name of the conda env / virtualenv / nvm version / etc.]

Typical startup:

```
[activation command — e.g. `conda activate <env>` or `source .venv/bin/activate` or `nvm use`]
```

After activation, use that environment for commands such as:

- [test runner, e.g. `pytest` or `npm test`]
- [app launch, e.g. `python run.py` or `npm run dev`]
- import checks, one-off scripts, etc.

## Common Tasks

Short recipes for the things you'll usually do in a session. All commands assume the env above is active.

Run the app for manual testing:

```
[app launch command]
```

Run the test suite (the CI-equivalent subset — skips slow or optional-dependency tests):

```
[test command — e.g. `pytest -v -m "not slow"` or `npm run test:unit`]
```

Run the full suite, including any slow or optional-dependency tests:

```
[full test command]
```

Pre-flight checklist before committing:

- Formatter / linter is clean (matches the CI format job): `[formatter command]`
- Test suite is green (matches the CI test job): `[test command]`
- A new entry has been prepended to `work_log.md` describing what was done, intended profiling signal if any, and the verification commands that were actually run.

If the change touches active modules, confirm imports still work — the smoke tests in `[tests/test_smoke.py or equivalent]` cover this.

Fetch recent work log context efficiently — instead of reading the full file, grep the date anchors and read just the slice you need:

```
grep -nE '^## [0-9]{4}-[0-9]{2}-[0-9]{2}' work_log.md
```

Take the line numbers of the first N entries you want, then read from the first one through just before entry N+1. `work_log_archive.md` uses the same convention for older entries. The same anchor-grep pattern works for any structured Markdown doc in the repo (`project_overview.md`, `next_steps.md`) — `grep -n '^## ' <file>` for the section map, then a targeted slice read rather than loading the whole file.

See [`project_overview.md`](project_overview.md) for the active vs. legacy code map before touching anything substantial.

## Git Ownership Note

If Git reports a "detected dubious ownership" warning for this repo, mark this repository as safe.

Windows (PowerShell):

```powershell
git config --global --add safe.directory C:/path/to/this/repo
```

macOS / Linux:

```bash
git config --global --add safe.directory "$HOME/path/to/this/repo"
```

This is the preferred fix unless the repository ownership itself needs to be changed at the OS level.

## Pre-commit Note

If your stack uses [pre-commit](https://pre-commit.com) and it cannot write to its default cache location, set a repo-local cache before running it.

Windows (PowerShell):

```powershell
$env:PRE_COMMIT_HOME = "C:\path\to\this\repo\.pre-commit-cache"
python -m pre_commit run --all-files
```

macOS / Linux:

```bash
export PRE_COMMIT_HOME="$PWD/.pre-commit-cache"
python -m pre_commit run --all-files
```

Adjust the formatter / linter invocation for your stack (e.g., `npx lint-staged`, `cargo fmt`, `gofmt -l .`).

## Commit Message Guidelines

Commit messages should use:

- a short title line
- a short body with flat bullet points for additional requested changes when a commit contains multiple user-requested updates

Commit message bullets should describe high-level added or changed behavior, not implementation details.

For feature commits, mention only the user-facing behavior that was added or changed.

Do not mention tests, docs, project memory updates, or behind-the-scenes implementation details in a feature commit message unless that internal work is itself the main purpose of the commit.

## Project-Specific Reminders

Add domain-specific gotchas here. These are the things that aren't obvious from reading the code and that an agent would otherwise have to learn the hard way.

Examples (delete and replace with your own):

- [Don't blow away debug breadcrumbs / parameter-rich filenames during pipeline iteration — they're load-bearing for explaining regressions later.]
- [Migrations must be reviewed against the staging snapshot before merge; the schema in `db/schema.sql` is the source of truth, not the ORM model.]
- [The `api/v1/` surface is frozen; new endpoints land under `api/v2/`.]
