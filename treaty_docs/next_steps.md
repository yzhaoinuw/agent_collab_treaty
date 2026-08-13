# Next Steps

Use this checklist alongside `work_log.md`.

## Currently Hot

Active threads — read these first to know what work is in flight:

- **Current release: v0.9.0 (2026-08-13) — `treaty relocate` (claude-opus-5).** One command moves the working docs between layouts: `git mv`, link rewrites in `AGENTS.md`/`project_overview.md`, the `docs_dir` answer, and a `.gitignore` check, refusing to run before `treaty update`. `treaty validate` gained `treaty-doc-gitignored`. Windows-verified by Codex/GPT-5 (#21, closed 2026-08-13 with nothing outstanding). **This is what unblocks recommending the nested layout to existing adopters.** Two things to watch, both from this thread: adopters hitting `treaty-doc-gitignored` and reading it as a regression rather than the latent problem it surfaces, and any report of docs moving unexpectedly on `treaty update` — that would contradict the v0.8.0 compatibility guarantee the whole design exists to protect.
- **Adopter pins, surveyed 2026-08-13 via the GitHub API (claude-opus-5).** 17 Copier-managed `yzhaoinuw/*` repos — 14 public and 3 private, so the badge's public-only count of 14 is correct, not undercounting. Only `mouse-pupil-analysis` is on v0.9.0. The rest: v0.7.0 ×1, v0.6.0 ×2 (`sleep_scoring`, `fp_analysis`), v0.5.0 ×2, v0.4.1 ×2, v0.3.3 ×2, v0.3.2 ×5, v0.3.1 ×1, v0.2.0 ×1. **This supersedes the old "nine of eleven / five remain" tally, which was stale.** The v0.6.0 argument still stands for the **13 repos pinned below it**: v0.6.0 corrected `template/work_log.md`, which had been shipping pre-v0.5.0 work-log criteria that contradict `treaty_conventions.md` — those docs are actively wrong, not merely dated.
- **Open issues.** #22 — Windows adopter report on a v0.6→v0.9 update and docs relocation, filed 2026-08-13, **not yet reviewed**. #19 — proposed `## User-Facing Docs` section for `template/treaty_conventions.md.jinja`; the issue's own open question is whether doc-quality guidance is in the treaty's scope, so this **needs a maintainer decision before any code**. #17 — first-class handling of newly introduced Copier answers (`--ask-new` / `--set`), partly mitigated by the real `--dry-run` but not implemented; `docs_dir` in v0.8.0 hit exactly this shape and was solved with a per-question pin (`_legacy_layout_data`), not a general mechanism. #15 — parked remainder only: `treaty adopt`/`doctor`, risk-classed `treaty diff` headlines, `--version` source provenance.
- **`treaty init` from an untagged local template still records an unresolvable `_commit` (claude-opus-5, 2026-08-12).** Half of this is fixed: `--source` is now absolutised at install time (`_resolve_source`), so `_src_path` no longer resolves to the adopter's own repo and git commands run against the real template. What remains is Copier's own recording of `_commit` as a `git describe` string (`v0.7.0-12-g462ff24`) when installing from an untagged commit; that is not a resolvable ref, so `treaty diff`/`treaty update` on such a project still fail — now in the *correct* repo, with a raw plumbum traceback rather than a clear message. Released adopters are unaffected (they pin a real tag). Proposed: before using a recorded `_commit`, verify it with `git rev-parse --verify <ref>^{commit}` against a local template source and, when it fails, print a clear instruction to pass `--ref` explicitly instead of letting the traceback surface. Deliberately not bundled into the `_src_path` fix — it is a distinct defect and was not part of the approved scope.
- **Local adopter clones have drifted from their published state (claude-opus-5, 2026-08-12; re-confirmed 2026-08-13).** `desktop_app_source_updater` is still pinned v0.4.1 on GitHub but was v0.6.0 in the local working copy — a `treaty update` run locally and never pushed. `ai_crash_course` shows the same signature (identical pin, different conflict outcome between the GitHub-clone and local-clone sweeps). Worth a pass to push or discard the local-only treaty updates, because until then the pin survey above reads GitHub state that some local clones contradict.
- **Adopters badge links to a search that disagrees with it** (open, small). The badge reads 14 — the correct public count — but its link goes to the GitHub code-search results page, which indexes only a fraction of those repos. Options: point the link at a maintained `ADOPTERS.md` list, at the README badge section, or leave it and accept the mismatch. Needs a decision before anyone treats the link as authoritative.
- **Windows `git status --porcelain` can overreport updated files (claude-opus-5, 2026-08-12).** With `core.autocrlf=true`, porcelain lists line-ending-normalized files that a normalized `git diff --name-only` does not, so `_classify_status` can show more files under "Updated files" than substantively changed. Cosmetic and pre-existing. **Priority lowered 2026-08-13:** the #21 sweep predicted this would false-positive `relocate`'s clean-tree guard and it did not reproduce, so the quirk evidently needs files whose stored line endings actually differ, not merely `autocrlf` enabled. No fix attempted.
- **Shipped, nothing outstanding on the releases themselves:** v0.5.0 (2026-07-30 — #12 template split into adopter-owned `AGENTS.md` and upstream `treaty_conventions.md`, opt-out questions, `treaty diff`; see [Issue #12 follow-ups](#issue-12-follow-ups-claude-opus-5)) · v0.6.0 (2026-08-01 — `treaty --version` #13, real Copier-merge tests #14, prompt-led README) · v0.7.0 (2026-08-01 — real `--dry-run` merge preview #16/#18, gitignored-answers detection from #15) · v0.8.0 (2026-08-12 — the `docs_dir` nested layout, verified non-migrating for existing adopters across 26 branch-vs-control runs on two operating systems). Full detail is in `work_log.md` and `work_log_archive/`; keep it out of this list.

When an agent (or human) creates or significantly updates a thread/plan here, include model + version, effort/thinking mode, and token budget (if known) in parentheses after the thread name or at the end of the status line, using the same compact convention as `work_log.md`.

Other sections below are background or paused; treat them as reference unless a new request reopens them.

## Parked: automated update notifications (claude-opus-5)

Status: **designed, deliberately not built** (2026-08-01). Do not start this without a fresh decision.

The problem: as of 2026-08-01, 9 of 11 adopting repos are pinned two or more minor versions behind (seven on v0.3.2, one on v0.2.0), so nobody checks for treaty updates by hand.

The design considered: a composite action in this repo at `.github/actions/treaty-update/`, called by ~15 lines of workflow in each adopting repo. Weekly, it would run `treaty diff`, then `treaty update`, and open a PR **in the adopter's own repo** only when the tree actually changed — no version parsing, no server, nothing pushed from here. On conflicts the PR would still open, labeled, with the pre-update `treaty diff` in the body and a prompt for the adopter's agent to resolve it.

**Why it was parked, and it is a good reason:** treaty docs from several releases back still serve their purpose. The format has been stable since ~v0.3, so being behind costs an adopter very little. Automating the update would add a scheduled job to every adopting repo to solve a problem that is not actually hurting anyone.

Revisit only if a future release makes older docs genuinely wrong rather than merely dated — a breaking rename, or guidance that becomes misleading. Open questions if it is ever picked up: whether a PR containing conflict markers is acceptable (it is what makes the branch agent-resolvable, but it breaks linters on that branch), and that `GITHUB_TOKEN`-created PRs do not trigger the adopter's other workflows.

## Issue #12 follow-ups (claude-opus-5)

Status: P1, P2, P4, P5, P6, and the two P3-lite items shipped in **v0.5.0** (released 2026-07-30).

Open follow-ups:

- **Update the adopting repos.** Still the largest open item, and no longer a single cohort: pins now range from v0.2.0 to v0.9.0 (see the 2026-08-13 survey in "Currently Hot"). Every repo pinned below v0.5.0 still faces the one-time `AGENTS.md` conflict from the template split; `treaty diff` then `treaty update` is both the migration and the real-world test of whether the split behaves as measured.
- **Full P3 (`project_kind`) is deliberately deferred**, per the issue's own recommendation. Revisit only if adopters still report vocabulary mismatch now that the split and the opt-out questions have landed. The two cheap parts (`env_activation=none`, `verification_command`) are already in.
- **`treaty diff` could gain `--json`** for scripting, and could report *which lines* within a modified section drifted. Neither is needed yet.
- **The 150-line guidance is now met by default (132 lines)** but is not enforced. A `treaty validate` check for it would close #11 mechanically; unclear whether that is welcome or annoying, since adopters legitimately add sections.

## Conflict-safe treaty update: closed (claude-opus-4.8)

Status: **issue #10 closed 2026-07-30.** Kept here as the record of how it was resolved.

Items 1–4 shipped in **v0.4.0** (`src/agent_collab_treaty/cli.py`): unmerged-file detection with a non-zero exit, the post-update summary, `treaty update --dry-run`, and answer preservation by default with `--interactive` as the opt-in.

Item 5 shipped in **v0.5.0**, but not as specified. It asked for managed-section markers in `template/AGENTS.md.jinja`; what landed instead splits the template by *maintenance ownership* — `AGENTS.md` for adopter answers, `treaty_conventions.md` for upstream-maintained mechanics. Markers would have carved one file into regions and asked the merge to respect them; the split removes the collision instead. Worth remembering if marker-style solutions come up again for another file.

Items 6 and 7 became standalone issues on 2026-07-30, and both closed on 2026-08-01:

- [**#13 `treaty --version`**](https://github.com/yzhaoinuw/agent_collab_treaty/issues/13) — done. Eager top-level callback printing the CLI version plus, inside an installed project, the pinned `_commit` and `_src_path`.
- [**#14 real Copier-merge tests**](https://github.com/yzhaoinuw/agent_collab_treaty/issues/14) — done. `tests/test_update_integration.py` runs genuine three-way merges over git-backed scratch projects, and `CopierConfigContractTests` guards the `copier.yml` declaration order the answer migration depends on. That guard was mutation-tested rather than just observed green.

## Background / Paused

Sections below this line are older threads kept for context. They're not the current focus, but recording the state they were left in saves the next agent from re-deriving it.

## Adopters badge history

The adoption-badge feature shipped in v0.3.1; a logo color/layout polish followed. The `ADOPTERS_TOKEN` PAT secret was added 2026-07-06, resolving the weekly workflow's code-search rate-limiting. On 2026-07-26 the counter was fixed to read `yzhaoinuw/*` repos directly, because code search indexes only a fraction of our repos; the badge went 6 -> 13, and reads 14 as of 2026-08-13. The one open decision is the badge's link target — see "Currently Hot".

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
