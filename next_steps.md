# Next Steps

Use this checklist alongside `work_log.md`.

## Currently Hot

Active threads — read these first to know what work is in flight:

- No active threads right now. Add the next concrete follow-up here when it becomes actionable. (The adoption-badge feature shipped in v0.3.1; a follow-up logo color/layout polish landed afterward.)

When an agent (or human) creates or significantly updates a thread/plan here, include model + version, effort/thinking mode, and token budget (if known) in parentheses after the thread name or at the end of the status line, using the same compact convention as `work_log.md`.

Other sections below are background or paused; treat them as reference unless a new request reopens them.

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
