# Next Steps

Use this checklist alongside `work_log.md`.

## Currently Hot

Active threads — read these first to know what work is in flight:

- **Conflict-safe treaty update: phase 2** — issue #10 items 5–7 are deferred to a dedicated branch next session. Items 1–4 (conflict detection + non-zero exit, post-update summary, `--dry-run`, answer preservation by default) shipped in **v0.4.0** (released 2026-07-17). See [Conflict-safe treaty update: phase 2](#conflict-safe-treaty-update-phase-2-claude-opus-48).
- Background: the adoption-badge feature shipped in v0.3.1; a follow-up logo color/layout polish landed afterward. The `ADOPTERS_TOKEN` PAT secret was added 2026-07-06, resolving the weekly workflow's code-search rate-limiting.

When an agent (or human) creates or significantly updates a thread/plan here, include model + version, effort/thinking mode, and token budget (if known) in parentheses after the thread name or at the end of the status line, using the same compact convention as `work_log.md`.

Other sections below are background or paused; treat them as reference unless a new request reopens them.

## Conflict-safe treaty update: phase 2 (claude-opus-4.8)

Status: items 1–4 implemented on `dev` (2026-07-16); items 5–7 deferred to a dedicated branch.

Issue #10 asked for a conflict-aware, safer `treaty update`. Shipped now (items 1–4, in `src/agent_collab_treaty/cli.py`):

- Detect unmerged files after Copier returns and exit non-zero when any remain.
- Print a post-update summary: old → new template version, answer changes, updated files, conflicted files, and the exact next git commands.
- `treaty update --dry-run` previews the diff without writing (Copier `pretend=True`).
- Recorded answers are reused by default; re-answering is now the explicit `--interactive` opt-in. `--defaults` is kept as a hidden deprecated no-op for back-compat.

Deferred to a dedicated branch next session (items 5–7). The maintainer asked to keep these off `dev` until then — branch off `dev` when starting:

- **#5 Managed-section markers / migration proposal.** For heavily customized `AGENTS.md`, replace whole-file conflicts with stable managed-section markers (or an adjacent migration proposal) so adopters' concise custom docs survive updates. This is a template-authoring redesign in `template/AGENTS.md.jinja`, not just a CLI change — the largest of the three and the one worth designing before coding.
- **#6 `treaty --version`.** Add a top-level Typer callback printing the CLI version and, when run inside an installed project, the recorded template version from `.copier-answers.yml`.
- **#7 End-to-end update tests.** Add real Copier-run update tests (git-backed scratch projects) covering clean updates, customized-file conflicts, answer preservation, and exit status. Phase-1 tests mock Copier/git; this matrix exercises the real three-way merge, as verified manually this session against a v0.3.2 → v0.3.3 adopter.

## Background / Paused

Sections below this line are older threads kept for context. They're not the current focus, but recording the state they were left in saves the next agent from re-deriving it.

## Existing Docs Adoption (gpt-5)

Status: implemented first pass; future explicit migration command deferred

- Implemented a conservative `treaty init` adoption preflight that detects existing canonical treaty files, case-mismatched treaty-looking files such as `Work_Log.md`, and common overlapping project/agent docs such as `TODO.md`, `ROADMAP.md`, `NOTES.md`, and `CLAUDE.md`.
- Preserves existing matching template paths through Copier `skip_if_exists`.
- Blocks noncanonical treaty-looking paths before copying, because on Windows they can prevent canonical treaty files from being created.
- Leaves broader migration tooling for later: a future explicit `treaty adopt` or `treaty migrate` command could summarize overlap, preserve originals in a user-approved archive or bridge, and create fresh canonical treaty files without silent rewrites.

## Session Documentation Rules (gpt-5)

Status: implemented

- Added a "When To Update Treaty Docs" section to root `AGENTS.md` and the installable `template/AGENTS.md.jinja`.
- Clarified in `template/work_log.md` that agents should log substantive sessions by default, skip trivial/off-the-book exchanges, and preserve useful evidence from reverted experiments.
- Updated README workflow guidance and Copier's post-copy message so downstream users see the same rule.

## Legacy Overlap Validation (gpt-5)

Status: implemented

- Added `treaty validate --migration-hints` for concise, non-destructive overlap guidance during adoption.
- Reused adoption preflight detection while filtering out ordinary existing canonical treaty files, so normal validation stays strict and quiet.
- Added tests confirming default validation does not mention overlapping docs, while `--migration-hints` reports them.
