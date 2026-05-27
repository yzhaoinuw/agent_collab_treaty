# Project Overview

This document orients a new agent or human collaborator to the Agent Collab Treaty codebase. Keep it current when the active CLI, template layout, or release process changes.

## What This Repo Is

`agent-collab-treaty` is a small Python package that publishes the `treaty` CLI. The CLI installs and updates a Copier template containing a shared documentation contract for human + multi-agent collaboration on any codebase.

The product is not an agent runtime. It is the coordination layer agents read before doing work: `AGENTS.md`, `project_overview.md`, `next_steps.md`, `work_log.md`, and `work_log_archive/`.

## Active Runtime Path

### 1. Package entry point

[`pyproject.toml`](pyproject.toml)

- Defines package metadata for `agent-collab-treaty`.
- Requires Python 3.10+.
- Declares the console script: `treaty = "agent_collab_treaty.cli:app"`.
- Uses Hatchling to build the wheel from `src/agent_collab_treaty`.

### 2. CLI module

[`src/agent_collab_treaty/cli.py`](src/agent_collab_treaty/cli.py)

- Defines the Typer app and the `treaty init`, `treaty update`, and `treaty validate` commands.
- `treaty init` calls `copier.run_copy(...)` with the official template source by default: `gh:yzhaoinuw/agent_collab_treaty`.
- `treaty update` calls `copier.run_update(...)` with `overwrite=True`; the target must be a git-tracked Copier subproject.
- `treaty validate` reports line-numbered treaty-doc issues and exits non-zero by default; `--warn-only` keeps it advisory.
- `_parse_data(...)` turns repeatable `--data key=value` arguments into the dict passed to Copier.

### 3. Validator module

[`src/agent_collab_treaty/validation.py`](src/agent_collab_treaty/validation.py)

- Checks required treaty paths, `work_log.md` session metadata, verification subsections, date rotation, duplicate dates, and `next_steps.md` Currently Hot anchors.
- Returns structured issues with file, line, code, and message fields for CLI output and tests.

### 4. Copier template configuration

[`copier.yml`](copier.yml)

- Points Copier at the `template/` subdirectory.
- Requires Copier 9.0+.
- Defines the current template questions: `integration_branch`, `env_activation`, `test_command`, and `agent_pointers`.
- Prints post-copy guidance about filling placeholders and wiring agent pointer files.

### 5. Installable treaty template

[`template/`](template/)

- Contains the files installed into downstream projects.
- `template/AGENTS.md.jinja` is rendered with the Copier answers.
- `template/.copier-answers.yml.jinja` records the source, commit, and answers so `treaty update` can work later.
- Optional pointer templates render `CLAUDE.md`, `.cursor/rules/treaty.mdc`, `.windsurf/rules/treaty.md`, and `.aider.conf.yml` when selected.
- Other template docs are plain Markdown starting points for project-specific context.

### 6. Release automation

[`.github/workflows/test-publish.yml`](.github/workflows/test-publish.yml) and [`.github/workflows/release.yml`](.github/workflows/release.yml)

- TestPyPI dry-runs are manual via `workflow_dispatch`.
- Real PyPI releases happen on `v*` tag pushes.
- Both workflows use PyPI Trusted Publishing (OIDC); no API token should be added to repo secrets.

## Repo Structure Map

```text
project_root/
|- .github/workflows/
|  |- release.yml
|  `- test-publish.yml
|- src/agent_collab_treaty/
|  |- __init__.py
|  |- cli.py
|  `- validation.py
|- template/
|  |- .copier-answers.yml.jinja
|  |- AGENTS.md.jinja
|  |- next_steps.md
|  |- project_overview.md
|  |- work_log.md
|  `- work_log_archive/
|- work_log_archive/
|- AGENTS.md
|- copier.yml
|- LICENSE
|- next_steps.md
|- project_overview.md
|- pyproject.toml
|- README.md
`- work_log.md
```

## What Looks Active vs. Legacy

### Active / relevant now

- [`src/agent_collab_treaty/cli.py`](src/agent_collab_treaty/cli.py) - active CLI implementation.
- [`copier.yml`](copier.yml) - active Copier configuration and template questions.
- [`template/`](template/) - active installable treaty content.
- [`README.md`](README.md) - public user and maintainer documentation.
- [`.github/workflows/`](.github/workflows/) - active PyPI/TestPyPI release automation.
- Root [`AGENTS.md`](AGENTS.md), [`next_steps.md`](next_steps.md), [`work_log.md`](work_log.md), and this file - dogfooded docs for maintaining this repo.

### Likely older or secondary

- There are no known legacy code paths yet.
- [`work_log_archive/`](work_log_archive/) is historical context, not active code.
- Local pointer files such as `CLAUDE.md`, `CODEX.md`, and `GEMINI.md` are intentionally ignored if created locally.

## Tests And Fixtures

The committed test suite currently focuses on validation behavior:

- [`tests/test_validation.py`](tests/test_validation.py) - temporary project fixtures for valid docs, missing metadata/verification, work-log rotation, and broken Currently Hot anchors.

Broader CLI/template verification is still smoke-test based:

- Install editable package into a venv.
- Run `treaty --help`, `treaty init --help`, and `treaty update --help`.
- Run `python -m unittest discover -s tests -v`.
- Run `treaty validate .`.
- Render `treaty init` into a scratch directory using `--source . --defaults --data ...`.
- For update behavior, use a git-tracked scratch project because Copier requires git for three-way updates.
- Run `git diff --check` before committing.

The most important future test fixtures will be temporary downstream projects rendered from `template/` and then updated across template revisions.

## User Data Expectations

The CLI has no external data model beyond Copier answers.

Current template inputs:

- `integration_branch`: target branch name for downstream project handoff guidance. Default: `main`.
- `env_activation`: downstream project's environment activation command. May be blank and filled later.
- `test_command`: downstream project's CI-equivalent test command. May be blank and filled later.
- `agent_pointers`: optional list of agent-specific pointer files to generate. Default: none.

Non-interactive callers pass answers with repeatable `--data key=value` options.

## Practical Mental Model

If you only want to understand the current product, read files in this order:

1. [`README.md`](README.md)
2. [`src/agent_collab_treaty/cli.py`](src/agent_collab_treaty/cli.py)
3. [`copier.yml`](copier.yml)
4. [`template/AGENTS.md.jinja`](template/AGENTS.md.jinja)
5. [`template/project_overview.md`](template/project_overview.md)
6. [`next_steps.md`](next_steps.md)
7. [`work_log.md`](work_log.md)

The key idea: `treaty init` copies the template into a target repo, and `treaty update` later applies upstream template changes using Copier metadata. Everything else is documentation quality, update safety, and agent-discovery ergonomics.

## Questions Worth Clarifying Later

- What minimum broader CLI/template test suite should gate future releases.
- Whether the GitHub-URL install fallback should remain prominent now that the package is on PyPI.
- Whether the package should include a first-run command that audits an existing repo and suggests project-specific values before rendering the treaty.
