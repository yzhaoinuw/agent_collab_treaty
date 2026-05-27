# Guidelines and Tips for Agents

This file is the first thing any agent (Claude, Codex, or other) should read when joining a session on this repo. It defines the runtime, common tasks, conventions, and project-specific reminders for maintaining the Agent Collab Treaty package itself.

## Startup Rule

At the beginning of a new chat or agent session for this project, read this file first and do not automatically read every markdown file in the repository. Use the [Documentation](#documentation) map below to decide which other files are relevant to the current task.

## What This Repo Maintains

This repository publishes `agent-collab-treaty`, a small Python package exposing the `treaty` CLI. The CLI installs and updates a Copier template containing the standard collaboration docs:

- `AGENTS.md`
- `project_overview.md`
- `next_steps.md`
- `work_log.md`
- `work_log_archive/`

Important boundary: the repo root dogfoods the treaty for this project, while `template/` is the product shipped into user projects. Do not copy root-level `AGENTS.md`, `next_steps.md`, `work_log.md`, or `project_overview.md` into the template unless the change is intentionally part of the installable treaty.

## Runtime Environment

There is no dedicated conda environment for this repo yet. For local work on Windows, use the base Miniconda Python unless you create a project venv:

```powershell
C:\Users\yzhao\miniconda3\python.exe --version
```

For isolated development:

```powershell
C:\Users\yzhao\miniconda3\python.exe -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e .
```

The package requires Python 3.10+ and depends on:

- `copier>=9.0`
- `typer>=0.12`

## Common Tasks

Install the package locally in editable mode:

```powershell
.\.venv\Scripts\python.exe -m pip install -e .
```

Show the CLI:

```powershell
.\.venv\Scripts\treaty.exe --help
.\.venv\Scripts\treaty.exe init --help
.\.venv\Scripts\treaty.exe update --help
```

Smoke-test rendering the template into a scratch directory:

```powershell
$scratch = Join-Path $env:TEMP "treaty-smoke"
if (Test-Path $scratch) { Remove-Item -LiteralPath $scratch -Recurse -Force }
.\.venv\Scripts\treaty.exe init $scratch --source . --defaults --data integration_branch=main --data env_activation="conda activate example" --data test_command="pytest"
Get-ChildItem $scratch
```

Build distribution artifacts:

```powershell
.\.venv\Scripts\python.exe -m pip install --upgrade build
.\.venv\Scripts\python.exe -m build
```

Run the CI-equivalent checks:

```powershell
git diff --check
.\.venv\Scripts\treaty.exe --help
.\.venv\Scripts\python.exe -c "import agent_collab_treaty, agent_collab_treaty.cli; print('import ok')"
```

There is not yet a committed automated test suite. Until one exists, use focused smoke tests for the CLI paths you touch and record the exact commands in `work_log.md`.

Pre-flight checklist before committing:

- `git diff --check` is clean.
- CLI/import smoke tests relevant to the change pass.
- Template changes were tested by rendering into a scratch directory.
- User-facing docs (`README.md`, `project_overview.md`, and template docs as applicable) match the behavior.
- A new entry has been prepended to `work_log.md` describing what was done, including model/version metadata when available and the verification commands actually run.

## Branch Handoff Discipline

The integration branch for this single-maintainer repo is `main`. Before switching away from an experimental or feature branch, fully resolve the work on that branch. Confirm whether the branch contains all intended changes, whether those changes are committed, and whether the user expects them merged, pushed, or intentionally left parked.

Useful checks before switching or merging:

```powershell
git status --short --branch
git log --oneline --left-right --cherry-pick main...HEAD
git merge-base --is-ancestor main HEAD
```

## Documentation

Read these documents only as needed. The map below names each file and when it is worth opening.

- `work_log.md` and `work_log_archive/`
  - Use when the task needs recent implementation history, experiment outcomes, or verification breadcrumbs.
  - The live `work_log.md` holds at most the 5 most recent unique calendar dates. Default to reading only the two most recent dated entries.
  - Find date anchors with ripgrep and read only the slice you need:
    `rg -n '^## [0-9]{4}-[0-9]{2}-[0-9]{2}' work_log.md`
  - When older context is needed, open the matching file under `work_log_archive/`, or grep across both:
    `rg -n '^## [0-9]{4}-[0-9]{2}-[0-9]{2}' work_log.md work_log_archive/`
  - When prepending a dated entry, if today's calendar date already has a `## YYYY-MM-DD` header at the top, add a new `###` session subsection under it. Do not start a second `## YYYY-MM-DD` header for the same date.
  - When prepending a new date would push the live log past 5 unique calendar dates, move the oldest 5 dates as a chunk into `work_log_archive/work_log_<earliest>_to_<latest>.md`.

- `next_steps.md`
  - Use when planning or continuing unfinished work from previous sessions.
  - The "Currently Hot" pointer at the top names active threads; read it first.
  - Remove items after they are completed. Add concrete follow-ups when they become actionable.

- `project_overview.md`
  - Use when onboarding to the codebase structure or when a task touches an unfamiliar area.
  - The "What Looks Active vs. Legacy" section is the most important map before editing.

- `README.md`
  - Use when changing user-facing setup, installation, release flow, packaging, or input-file expectations.

- `template/`
  - Use when changing what `treaty init` installs into downstream projects.
  - Keep template docs generic and project-agnostic; root docs should stay specific to this repo.

- `copier.yml`
  - Use when adding or changing questions, defaults, Copier configuration, or post-copy messaging.

- `.github/workflows/`
  - Use when changing release or TestPyPI publishing behavior.

## Git Ownership Note

If Git reports a "detected dubious ownership" warning for this repo, mark this repository as safe:

```powershell
git config --global --add safe.directory C:/Users/yzhao/python_projects/agent_collab_treaty
```

This is the preferred fix unless repository ownership itself needs to be changed at the OS level.

## Release Notes

The package is published as `agent-collab-treaty` on PyPI. Release automation lives in:

- `.github/workflows/test-publish.yml` for manual TestPyPI dry-runs.
- `.github/workflows/release.yml` for `v*` tag pushes to PyPI plus GitHub Release creation.

Both workflows use PyPI Trusted Publishing (OIDC). See the README "Releasing to PyPI" section before changing release behavior.

## Commit Message Guidelines

Commit messages should use:

- a short title line
- a short body with flat bullet points for additional requested changes when a commit contains multiple user-requested updates

Commit message bullets should describe high-level added or changed behavior, not implementation details. For feature commits, mention only the user-facing behavior that was added or changed. Do not mention tests, docs, project memory updates, or behind-the-scenes implementation details unless that internal work is itself the main purpose of the commit.

## Project-Specific Reminders

- Keep the root-vs-template boundary explicit. Root docs are this repo's dogfood state; `template/` is the installable treaty.
- When changing `template/AGENTS.md.jinja`, also consider whether `README.md`, root `AGENTS.md`, and `project_overview.md` need matching guidance.
- `treaty update` depends on Copier's answers file in rendered projects. Do not remove or rename `template/.copier-answers.yml.jinja` without testing update behavior.
- This repo currently has no committed tests. Prefer adding focused tests before broad CLI behavior changes, especially for `treaty init`, `treaty update`, and future validation logic.
- Local agent pointer files such as `CLAUDE.md`, `CODEX.md`, and `GEMINI.md` are ignored in this repo to keep the package repo vendor-neutral. If the template begins generating pointer files for downstream projects, make that behavior conditional and documented.
