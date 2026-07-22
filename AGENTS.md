# Guidelines and Tips for Agents

The first file to read when joining a session on this repo. It defines the runtime, common tasks, conventions, and project-specific reminders for maintaining the Agent Collab Treaty package.

**Keep this file lean — aim for under 150 lines.** It is a quick-reference map, not a manual: when a topic needs more than a few tight lines, put the detail in the doc it points to (`README.md`, `project_overview.md`, `work_log.md`) and link there instead of growing this file.

## Startup Rule

At the start of a new session, read this file first; do not auto-read every markdown file. Use the [Documentation](#documentation) map to pick what else is relevant.

## What This Repo Maintains

This repo publishes `agent-collab-treaty`, a Python package exposing the `treaty` CLI, which installs and updates a Copier template of standard collaboration docs (`AGENTS.md`, `project_overview.md`, `next_steps.md`, `work_log.md`, `work_log_archive/`).

**Root-vs-template boundary:** the repo root dogfoods the treaty for this project; `template/` is the product shipped into user projects. Do not copy root-level treaty docs into `template/` unless the change is intentionally part of the installable treaty. Keep root docs specific to this repo and template docs generic.

## Runtime Environment

Python 3.10+; depends on `copier>=9.0` and `typer>=0.12`. There is no dedicated conda env. For isolated dev:

```bash
python -m venv .venv && .venv/bin/python -m pip install -e .
```

On Windows use the base Miniconda Python (`C:\Users\yzhao\miniconda3\python.exe`) and `.\.venv\Scripts\`.

## Common Tasks

See `README.md` for full command examples. The CI-equivalent pre-flight checks:

```bash
git diff --check
python -m unittest discover -s tests -v
treaty --help && treaty validate .
python -c "import agent_collab_treaty, agent_collab_treaty.cli; print('import ok')"
```

Smoke-test template rendering by `treaty init`-ing into a scratch dir; build with `python -m build`.

Pre-flight checklist before committing:

- `git diff --check` clean.
- Unit tests and CLI/import smoke tests for the change pass.
- `treaty validate .` passes for the dogfooded docs.
- Template changes tested by rendering into a scratch dir.
- User-facing docs (`README.md`, `project_overview.md`, template docs) match the behavior.
- A new `work_log.md` entry describes the work, model/version metadata, and the verification commands actually run.

## When To Update Treaty Docs

At the end of any substantive session, prepend a `work_log.md` entry unless the user says not to or the exchange was trivial. Substantive = file edits, meaningful validation/debugging, a decision or reversal, discovered evidence, branch/PR/release/env state changes, or unfinished follow-up. Log reverted experiments when they leave reusable evidence, a decision, or a warning. Update `next_steps.md` in the same pass: add follow-ups, remove completed items, keep "Currently Hot" accurate.

## Agent Roles, PR Policy, and Merges

- **Boss agent** (currently Claude): commits directly on `dev` and pushes; opens **no** PRs for its own work, even substantive code. The maintainer merges `dev → main`.
- **Contributing agents** (any other): work on a branch and open a **PR** for review before anything reaches `dev`/`main`.

`dev` is staging; `main` is release/integration. Boss-agent changes reach `main` via a plain `dev → main` merge (fast-forward), no PR. When a PR *is* used, prefer `gh pr merge --rebase` (or `--squash`) over `--merge`: a merge commit puts a commit on `main` that is not in `dev`, so the branches diverge on the DAG even when their trees match.

## Branch Handoff & Automated Commits on `main`

Before switching away from a feature/experimental branch, resolve its work: confirm changes are committed and whether the user wants them merged, pushed, or parked.

The `update-adopters-badge` workflow runs weekly and, when the count changes, pushes a `github-actions[bot]` commit **directly to `main`**, so `main` can move ahead of your local clone and of `dev` on its own. **Always `git fetch`/pull `main` before merging `dev → main`.** If they have already diverged from a bot commit, diagnose (`git status -sb`, `git log --left-right --cherry-pick main...HEAD`) and ask before any rebase/force-push/merge surgery — do not "fix then report."

## Release / Tag Checklist

Treat commit + push + tag (or "cut a release" / "publish version X") as a release. Clear this doc gate **before** creating or pushing the tag:

- Version bumped in `pyproject.toml` **and** `src/agent_collab_treaty/__init__.py`, consistent with the tag.
- User-facing docs updated when behavior changed. (No changelog file; release history lives in `work_log.md` plus the GitHub Release body.)
- `work_log.md` updated with the summary, verification commands run, and release/branch/tag state, using the verified local date.

Then create the annotated tag and push. Pushing a `v*` tag triggers `.github/workflows/release.yml` (PyPI trusted publishing + GitHub Release). Afterward verify refs with `git ls-remote --tags origin` and `git ls-remote --heads origin <branch>`. `test-publish.yml` is a manual TestPyPI dry-run.

## Commit Message Guidelines

Short title line; a short body with flat bullets when a commit bundles several requested changes. Bullets describe high-level user-facing behavior added or changed, not implementation, tests, docs, or memory — unless that internal work is the commit's main purpose.

## Documentation

Read these only as needed:

- **`work_log.md`** / **`work_log_archive/`** — recent implementation history, experiments, verification breadcrumbs. The live log holds at most the **5 most recent unique dates**; default to reading the two most recent. Find anchors with `rg -n '^## [0-9]{4}-[0-9]{2}-[0-9]{2}' work_log.md`. When prepending: if today already has a `## YYYY-MM-DD` header, add a `###` session under it; when a new date would exceed 5 dates, move the oldest 5 as a chunk into `work_log_archive/work_log_<earliest>_to_<latest>.md`. Verify the local date first (`date +%F`); never write a future-dated entry (`treaty validate` fails with `work-log-future-date`).
- **`next_steps.md`** — unfinished work; read the "Currently Hot" pointer first and remove items when done.
- **`project_overview.md`** — codebase structure; "What Looks Active vs. Legacy" is the key map.
- **`README.md`** — user-facing setup, install, release flow, packaging.
- **`template/`** — what `treaty init` installs (keep it generic). **`copier.yml`** — questions, defaults, post-copy messaging. **`.github/workflows/`** — release and adopters-badge automation.
- **Treaty & adopters badges (README):** `treaty init` offers an opt-in "adopted" badge (tri-color SVG primary; shields.io fallback for non-GitHub renders). `scripts/count_adopters.sh` counts public adopters via GitHub code search (a floor); the `adopters` badge is refreshed weekly and only rewritten on a clean positive count. An `ADOPTERS_TOKEN` PAT reduces throttling.

## Project-Specific Reminders

- Keep the root-vs-template boundary explicit (see above).
- When changing `template/AGENTS.md.jinja`, check whether `README.md`, root `AGENTS.md`, and `project_overview.md` need matching updates.
- Do not remove or rename `template/.copier-answers.yml.jinja` without testing `treaty update`.
- Keep `treaty validate` grounded in the documented treaty shape; update tests and dogfooded docs in the same change when you tighten it.
- Local pointer files (`CLAUDE.md`, `CODEX.md`, `GEMINI.md`) are gitignored to keep the repo vendor-neutral; downstream pointers are opt-in via the `agent_pointers` Copier question.
- If Git warns about "dubious ownership," mark the repo safe: `git config --global --add safe.directory <path>`.
