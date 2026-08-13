# Guidelines and Tips for Agents

The first file to read when joining a session on this repo. It defines the runtime, common tasks, conventions, and project-specific reminders for maintaining the Agent Collab Treaty package.

**Keep this file lean — aim for under 150 lines.** It is a quick-reference map, not a manual: when a topic needs more than a few tight lines, put the detail in the doc it points to (`README.md`, `project_overview.md`, `treaty_docs/work_log.md`) and link there instead of growing this file.

## Startup Rule

At the start of a new session, read this file first; do not auto-read every markdown file. Use the [Documentation](#documentation) map to pick what else is relevant.

## What This Repo Maintains

This repo publishes `agent-collab-treaty`, a Python package exposing the `treaty` CLI, which installs and updates a Copier template of standard collaboration docs (`AGENTS.md` and `project_overview.md` at the repo root; `treaty_conventions.md`, `next_steps.md`, `work_log.md`, and `work_log_archive/` under `treaty_docs/`, or flat at the root when `docs_dir` is `.`).

**Template split (since v0.5.0):** `template/AGENTS.md.jinja` holds what adopters customize; `template/treaty_conventions.md.jinja` holds the mechanics we maintain. New generic guidance goes in conventions, not AGENTS — that's what keeps `treaty update` close to conflict-free downstream. The root repo does not install a `treaty_conventions.md` of its own: its `AGENTS.md` already links straight to the docs below.

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
python -m unittest discover -s tests -v          # ~13s; TREATY_SKIP_INTEGRATION=1 for ~0.2s
treaty --help && treaty --version && treaty validate .
python -c "import agent_collab_treaty, agent_collab_treaty.cli; print('import ok')"
```

`tests/test_update_integration.py` runs real git + Copier merges. Skipping it is fine mid-loop, but never skip it in the run you commit on — it is the only coverage of the three-way merge.

Smoke-test template rendering by `treaty init`-ing into a scratch dir; build with `python -m build`.

Pre-flight checklist before committing:

- `git diff --check` clean.
- Unit tests and CLI/import smoke tests for the change pass.
- `treaty validate .` passes for the dogfooded docs.
- Template changes tested by rendering into a scratch dir.
- User-facing docs (`README.md`, `project_overview.md`, template docs) match the behavior.
- A new `treaty_docs/work_log.md` entry describes the work, model/version metadata, and the verification commands actually run.

## When To Update Treaty Docs

At the end of any substantive session, prepend a `treaty_docs/work_log.md` entry unless the user says not to or the exchange was trivial. **The log records decisions about the project, not the content of the work produced** — the diff already says what changed, so log the decision, the reversal, the approach tried and discarded and why, evidence future agents shouldn't have to rediscover, and shared-state changes (branch/PR/release/env). Log reverted experiments when they leave reusable evidence, a decision, or a warning. Update `treaty_docs/next_steps.md` in the same pass: add follow-ups, remove completed items, keep "Currently Hot" accurate.

## Agent Roles, PR Policy, and Merges

- **Boss agent** (currently Claude): commits directly on `dev` and pushes; opens **no** PRs for its own work, even substantive code. The maintainer merges `dev → main`.
- **Contributing agents** (any other): work on a branch and open a **PR** for review before anything reaches `dev`/`main`.

`dev` is staging; `main` is release/integration. Boss-agent changes reach `main` via a plain `dev → main` merge (fast-forward), no PR. When a PR *is* used, prefer `gh pr merge --rebase` (or `--squash`) over `--merge`: a merge commit puts a commit on `main` that is not in `dev`, so the branches diverge on the DAG even when their trees match.

## Branch Handoff & Automated Commits on `main`

Before switching away from a feature/experimental branch, resolve its work: confirm changes are committed and whether the user wants them merged, pushed, or parked.

The `update-adopters-badge` workflow runs weekly and, when the count changes, pushes a `github-actions[bot]` commit **directly to `main`**, so `main` can move ahead of your local clone and of `dev` on its own. **Always `git fetch`/pull `main` before merging `dev → main`.** If they have already diverged from a bot commit, diagnose (`git status -sb`, `git log --left-right --cherry-pick main...HEAD`) and ask before any rebase/force-push/merge surgery — do not "fix then report."

## Release / Tag Checklist

Treat commit + push + tag (or "cut a release" / "publish version X") as a release. Clear this doc gate **before** creating or pushing the tag:

- Version bumped in `pyproject.toml` **and** `src/agent_collab_treaty/__init__.py`, consistent with the tag. Update `version:` and `date-released:` in `CITATION.cff` in the same pass — but **leave its `identifiers:` DOI alone**: that is the Zenodo *concept* DOI, which already resolves to the newest archive. Swapping in the per-release version DOI would pin every future citation to one release.
- User-facing docs updated when behavior changed. (No changelog file; release history lives in `treaty_docs/work_log.md` plus the GitHub Release body.)
- `treaty_docs/work_log.md` updated with the summary, verification commands run, and release/branch/tag state, using the verified local date.

Then create the annotated tag and push. Pushing a `v*` tag triggers `.github/workflows/release.yml` (PyPI trusted publishing + GitHub Release). Afterward verify refs with `git ls-remote --tags origin` and `git ls-remote --heads origin <branch>`. `test-publish.yml` is a manual TestPyPI dry-run.

## Commit Message Guidelines

Short title line; a short body with flat bullets when a commit bundles several requested changes. Bullets describe high-level user-facing behavior added or changed, not implementation, tests, docs, or memory — unless that internal work is the commit's main purpose.

## Documentation

Read these only as needed:

- **`treaty_docs/work_log.md`** / **`treaty_docs/work_log_archive/`** — recent implementation history, experiments, verification breadcrumbs. The live log holds at most the **5 most recent unique dates**; default to reading the two most recent. Find anchors with `rg -n '^## [0-9]{4}-[0-9]{2}-[0-9]{2}' treaty_docs/work_log.md`. When prepending: if today already has a `## YYYY-MM-DD` header, add a `###` session under it; when a new date would exceed 5 dates, move the oldest 5 as a chunk into `treaty_docs/work_log_archive/work_log_<earliest>_to_<latest>.md`. Verify the local date first (`date +%F`); never write a future-dated entry (`treaty validate` fails with `work-log-future-date`).
- **`treaty_docs/next_steps.md`** — unfinished work; read the "Currently Hot" pointer first and remove items when done.
- **`project_overview.md`** — codebase structure; "What Looks Active vs. Legacy" and "Authored vs. Derived" are the key maps.
- **`README.md`** — user-facing setup, install, update, badge. **`CONTRIBUTING.md`** — human-contributor front door; also holds the release/publishing mechanics (workflows, trusted publishing) that used to live in the README's Developer Notes.
- **`template/`** — what `treaty init` installs (keep it generic). **`copier.yml`** — questions, defaults, post-copy messaging. **`.github/workflows/`** — release and adopters-badge automation.
- **Treaty & adopters badges (README):** `treaty init` offers an opt-in "adopted" badge (tri-color SVG primary; shields.io fallback for non-GitHub renders). `scripts/count_adopters.sh` counts public adopters from two sources: `yzhaoinuw/*` repos are listed and read **directly** via the repos API, and code search covers third parties. Do not go back to code-search-only — it does not index most of our newer repos and undercounted 13 adopters as 6 (see `treaty_docs/work_log.md`, 2026-07-26); the third-party half remains a floor for the same reason. The `adopters` badge is refreshed weekly and only rewritten on a clean positive count. An `ADOPTERS_TOKEN` PAT reduces throttling.

## Project-Specific Reminders

- Keep the root-vs-template boundary explicit (see above).
- When changing `template/AGENTS.md.jinja` or `template/treaty_conventions.md.jinja`, check whether `README.md`, root `AGENTS.md`, and `project_overview.md` need matching updates.
- **Never rename a `##` heading in the template docs.** A three-way merge reads a rename as a delete plus an unrelated add, so every downstream adopter gets a conflict that cannot be auto-resolved. Change the body and leave the heading.
- **Never move or rename a template *file* to change an adopter's layout.** Copier applies a template-side move as "delete the adopter's customized file, write a pristine one at the new path" — it does not merge, does not conflict, and does not warn. Verified 2026-08-11: a naive move wiped a customized `work_log.md`, leaving only `D work_log.md` in `git status`. A `_migrations` hook preserves the content but then conflicts in every adopter's file, even on a pure move with no content change. Layout is therefore a *Copier answer* (`docs_dir`), never a move.
- **The flat rendering's paths are frozen; its content is not.** Adopters installed before v0.8.0 are pinned to `docs_dir: '.'`, and the two kinds of drift in that rendering cost wildly different amounts:
  - **Paths — frozen permanently, no escape hatch.** No file may move, appear, or disappear in the flat rendering. Copier applies a path change as delete-plus-create: no merge, no conflict, no warning, and the adopter's customized file is gone. `tests/test_docs_dir.py::test_flat_layout_paths_are_frozen` diffs the path set against `v0.7.0`. If it fails, revert and express the layout as a Copier answer — **never** update that baseline.
  - **`treaty_conventions.md` content — free.** Adopters are told not to edit it, so their copy equals the merge base and upstream prose applies cleanly. It is the *cheapest* file to change, not the most expensive. New generic guidance belongs here.
  - **Content of the docs adopters edit** (`AGENTS.md`, `project_overview.md`, `work_log.md`, `next_steps.md`) — allowed but priced. Costs one visible conflict, and only for adopters who edited the same region. Justify it in the work log and batch it into a release.

  Measured 2026-08-13 across five real Copier updates (`FlatConventionsMergeTests`, `FlatWorkLogMergeTests`): no scenario lost adopter content. Those behavioral tests replaced a whole-tree byte-identity assertion that could only say "the bytes differ" — it blocked ordinary prose maintenance to prevent a data-loss mode that only path changes cause. **When a merge test tells you what a change costs, don't reach for a proxy that forbids it.**
- **Price a path/layout change as a migration before writing any of it.** Anything that changes what adopters have on disk needs one upfront pass over three questions — what Copier sees on the next `treaty update`, what the adopter must run and in what order, and what silently stops matching afterward (doc links, `.gitignore` allowlists, filename case, path separators). Skipping that pass is what stretched `docs_dir` across v0.8.0–v0.9.0: the flat-rendering freeze was discovered by conflict sweep rather than reasoning, and the four-step manual relocation guide shipped in v0.8.0 had to be replaced by `treaty relocate` a day later because every step of it fails quietly. **A migration we can only describe as a manual procedure is a command we have not written yet.**
- Rendering a *local* template source uses the source repo's git HEAD commit, not your working tree. Pass `--ref HEAD` (`treaty init … --ref HEAD`) to smoke-test uncommitted template edits, or you will silently test the last commit.
- `copier.yml` declares `test_command` with `when: false` as a legacy alias, and it must stay declared **after** `verification_command`. Copier renders defaults in declaration order and clears a `when: false` answer as it passes it, so reordering silently drops the migration.
- Do not remove or rename `template/.copier-answers.yml.jinja` without testing `treaty update`, and **never move it under `template/{{ docs_dir }}/`.** It must render to the adopter's repo root at every `docs_dir`: Copier reads it from there, and it is the file that records `docs_dir`, so it cannot live inside the folder it names. `relocate` edits it in place and never moves it.
- Keep `treaty validate` grounded in the documented treaty shape; update tests and dogfooded docs in the same change when you tighten it.
- Local pointer files (`CLAUDE.md`, `CODEX.md`, `GEMINI.md`) are gitignored to keep the repo vendor-neutral; downstream pointers are opt-in via the `agent_pointers` Copier question.
- If Git warns about "dubious ownership," mark the repo safe: `git config --global --add safe.directory <path>`.
