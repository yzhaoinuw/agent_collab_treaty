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
.\.venv\Scripts\treaty.exe validate --help
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
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\treaty.exe --help
.\.venv\Scripts\treaty.exe validate .
.\.venv\Scripts\python.exe -c "import agent_collab_treaty, agent_collab_treaty.cli; print('import ok')"
```

There is now a small `unittest` suite focused on validation behavior. For CLI/template changes, still use focused smoke tests for the paths you touch and record the exact commands in `work_log.md`.

Pre-flight checklist before committing:

- `git diff --check` is clean.
- Unit tests and CLI/import smoke tests relevant to the change pass.
- `treaty validate .` passes for the repo's own dogfooded treaty docs.
- Template changes were tested by rendering into a scratch directory.
- User-facing docs (`README.md`, `project_overview.md`, and template docs as applicable) match the behavior.
- A new entry has been prepended to `work_log.md` describing what was done, including model/version metadata when available and the verification commands actually run.

## When To Update Treaty Docs

At the end of any substantive work session, update `work_log.md` unless the user explicitly asks not to document it, says it is off the book, or the exchange was clearly trivial.

A session is substantive when it includes any of:

- file edits
- meaningful validation, debugging, profiling, or artifact inspection
- a technical decision or reversal
- discovered evidence future agents should not have to rediscover
- branch, PR, release, deployment, or environment state changes
- unfinished follow-up that belongs in `next_steps.md`

No work-log entry is usually needed for casual Q&A, explanation-only exchanges with no lasting project state, or tiny one-off commands with no future coordination value.

Log experiments when they produce reusable evidence, a decision, or a warning for future agents, even if the code change is reverted. Skip pure scratch work when it has no future coordination value or the user wants it omitted.

When a session creates or changes future work, update `next_steps.md` in the same pass: add concrete follow-ups, remove completed items, and keep "Currently Hot" accurate.

## Branch Handoff Discipline

The integration branch for this single-maintainer repo is `main`. Before switching away from an experimental or feature branch, fully resolve the work on that branch. Confirm whether the branch contains all intended changes, whether those changes are committed, and whether the user expects them merged, pushed, or intentionally left parked.

Useful checks before switching or merging:

```powershell
git status --short --branch
git log --oneline --left-right --cherry-pick main...HEAD
git merge-base --is-ancestor main HEAD
```

### Automated commits on `main`

The `update-adopters-badge` workflow (`.github/workflows/update-adopters-badge.yml`) runs weekly and, when the adopter count changes, pushes a `github-actions[bot]` commit **directly to `main`** (scheduled workflows run on the default branch). This means `main` can move ahead of your local clone and ahead of `dev` on its own.

Before merging `dev → main`, always `git pull` (or `git fetch` then check) `main` first, so you merge onto the bot's latest commit instead of diverging from it. If `main` and `dev` have already diverged because of a bot commit, diagnose with the checks above and ask before any rebase/force-push/merge surgery — do not "fix then report."

## Agent Roles and PR Policy

This repo distinguishes the **boss agent** from **contributing agents**:

- **Boss agent** — the lead agent running the project (currently Claude). The boss agent commits directly on `dev` and pushes; it does **not** open pull requests for its own work, even substantive code. The maintainer then merges `dev → main`.
- **Contributing agents** — any other agent making changes. These work on a branch and **open a pull request** for review before anything reaches `dev` or `main`.

Why: this is a single-maintainer repo with a lead agent. PR overhead does not pay for itself on the boss agent's own changes, but PRs remain the review gate for other agents' contributions. `dev` is the staging branch; `main` is the release/integration branch.

## PR Merge Strategy

This applies whenever a PR is used (contributing-agent changes, or any change the maintainer chooses to route through a PR). Boss-agent changes reach `main` via a plain `dev → main` merge with no PR.

When merging PRs from `dev` into `main`, prefer `gh pr merge --rebase` (or `--squash`) over the default `--merge`. The merge-commit option creates a commit on `main` that is not in `dev`'s history, so the two branches diverge on the DAG even when their working trees match. A follow-on commit on either branch (for example, a version bump made after the PR merges) then can't be fast-forwarded across — it has to be cherry-picked or merged manually.

`--rebase` keeps `main` and `dev` pointing at the same commit after the merge, so post-merge follow-ups stay linear.

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
  - Before writing any dated entry, verify the workstation / repo-local date (`date +%F` on macOS/Linux, `Get-Date -Format yyyy-MM-dd` on Windows) and use that. When the model-context date and the local environment disagree — which happens across a UTC midnight boundary — trust the local date. Never write a future-dated entry. `treaty validate` enforces this: it fails with `work-log-future-date` when any entry is dated after the local date.

- `next_steps.md`
  - Use when planning or continuing unfinished work from previous sessions.
  - The "Currently Hot" pointer at the top names active threads; read it first.
  - Remove items after they are completed. Add concrete follow-ups when they become actionable.

- `project_overview.md`
  - Use when onboarding to the codebase structure or when a task touches an unfamiliar area.
  - The "What Looks Active vs. Legacy" section is the most important map before editing.

- `README.md`
  - Use when changing user-facing setup, installation, release flow, packaging, or input-file expectations.

- Treaty badge (in README)
  - `treaty init` offers (opt-in) a centrally-hosted "Agent Collab Treaty - adopted" badge. It is a pure visibility signal that links back to this treaty repository. No asset files are added to your project; the image updates automatically if the design improves later. The badge is fully optional. The tri-color SVG (Codex blue / Claude amber / Grok dark) is the primary recommendation — its text is outlined to vector paths, so it renders identically on GitHub across every platform. The single-color shields.io variant is a fallback only for READMEs that also render outside GitHub (e.g. PyPI/npm), where raw SVG may be blocked.

- Adopter tracking (`scripts/count_adopters.sh` + adopters badge in README)
  - `scripts/count_adopters.sh` counts public repos that reference the treaty via GitHub code search (using your `gh` auth), dedupes, and excludes the treaty repo itself and the `pydigger` crawler. Run it on demand; it has no servers and no cost. The count is a **floor** — code search only indexes a subset of public repos, with lag.
  - The `adopters` badge near the top of `README.md` (between the `<!-- adopters-badge:start/end -->` markers) displays that count and links to the live code-search results. It is refreshed weekly by the `update-adopters-badge` workflow, which reuses the script and only rewrites the number when it is > 0.

- `template/`
  - Use when changing what `treaty init` installs into downstream projects.
  - Keep template docs generic and project-agnostic; root docs should stay specific to this repo.

- `copier.yml`
  - Use when adding or changing questions, defaults, Copier configuration, or post-copy messaging.

- `.github/workflows/`
  - Use when changing release or TestPyPI publishing behavior, or the weekly `update-adopters-badge` workflow that refreshes the README adopters count.

## Git Ownership Note

If Git reports a "detected dubious ownership" warning for this repo, mark this repository as safe:

```powershell
git config --global --add safe.directory C:/Users/yzhao/python_projects/agent_collab_treaty
```

This is the preferred fix unless repository ownership itself needs to be changed at the OS level.

## Release / Tag Checklist

Treat any request that combines **commit + push + tag** — or "cut a release" / "publish version X" — as a release. A release requires a documentation gate that must clear *before* the tag is created or pushed, not after. Run this checklist in status before creating an annotated tag:

- Version metadata bumped (`pyproject.toml`) and consistent with the tag you are about to create.
- Changelog / release notes updated if the repo has one. (This repo has no `change_log.txt`; its release history lives in `work_log.md` plus the GitHub Release body.)
- User-facing docs (`README.md`, `project_overview.md`, template docs) updated when behavior changed.
- `work_log.md` updated with the implementation summary, the verification commands actually run, and the release / branch / tag state.
- Verification recorded — the focused or full checks from the pre-flight checklist passed and are noted in the work log.
- Any dated artifact uses the verified local date, not an unverified model-context date (see the dated-entry rule under Documentation → `work_log.md`).

Only after every applicable item is done: create the annotated tag and push. Then verify the pushed refs landed where you expect:

```powershell
git ls-remote --tags origin
git ls-remote --heads origin <branch>
```

If a tag or branch ref is missing or points at the wrong commit after the push, fix it before treating the release as complete.

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
- Keep validation checks grounded in the documented treaty shape. If you tighten `treaty validate`, update tests and dogfooded docs in the same change.
- Local agent pointer files such as `CLAUDE.md`, `CODEX.md`, and `GEMINI.md` are ignored in this repo to keep the package repo vendor-neutral. Downstream pointer files generated by the template are opt-in through the `agent_pointers` Copier question.
