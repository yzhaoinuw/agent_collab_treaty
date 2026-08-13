# Next Steps

Use this checklist alongside `work_log.md`.

## Currently Hot

Active threads — read these first to know what work is in flight:

- **v0.5.0 released 2026-07-30.** Issue #12: the template is split into `AGENTS.md` (adopter-owned) and `treaty_conventions.md` (upstream-maintained), plus three opt-out questions, `treaty diff`, `verification_command`, and the decisions-not-content work-log rule. Watch for adopter reports of the one-time `AGENTS.md` conflict this update causes — that feedback is what should decide whether full P3 is ever worth doing. See [Issue #12 follow-ups](#issue-12-follow-ups-claude-opus-5).
- **v0.6.0 released 2026-08-01.** `treaty --version` (#13), real Copier-merge tests (#14), the prompt-led README, and a fix to `template/work_log.md`, which had been shipping pre-v0.5.0 work-log criteria that contradicted `treaty_conventions.md`. Its release issues (#13, #14) are closed.
- **v0.7.0 released 2026-08-01, from the Codex migration feedback (#15–#18) (claude-fable-5).** Codex (GPT-5) migrated four adopter repos to v0.6.0 and filed one issue per repo; the fixes shipped same-day: `treaty update --dry-run` now runs the real merge in a disposable clone and reports answer changes / updated files / conflicts with apply-matching exit codes (#16 closed; #18 closed as its duplicate), and a gitignored `.copier-answers.yml` is now caught at init, validate, and dry-run (#15's top item). Still open: #17 (first-class handling of newly introduced Copier answers — `--ask-new` / `--set` ideas) and the parked remainder of #15 (`treaty adopt`/`doctor`, risk-classed `treaty diff` headlines, `--version` source provenance). `dev → main` merge pending (maintainer).
- **v0.8.0 released 2026-08-12 — treaty docs moved into `treaty_docs/` (claude-opus-5).** New installs keep `treaty_conventions.md`, `next_steps.md`, `work_log.md`, and `work_log_archive/` under `treaty_docs/`; `AGENTS.md` and `project_overview.md` stay at the root. The `docs_dir` question renames the folder or takes `.` for the old flat layout. **Existing adopters are not migrated** — no recorded `docs_dir` means `treaty update` pins them flat, verified across 26 branch-vs-control runs on two operating systems (14 GitHub clones on macOS, 12 local clones on Windows via Codex/GPT-5) with identical results in every one. Also carries the Windows cp1252 crash fix and the absolutised local `--source`. On PyPI and verified by clean-venv install. **Watch for:** adopter reports of anything moving unexpectedly — that would contradict the compatibility guarantee and is the one outcome the whole design exists to prevent. Next in this thread is `treaty relocate` (see below) before recommending anyone move an existing repo.
- **`treaty init` from an untagged local template still records an unresolvable `_commit` (claude-opus-5, 2026-08-12).** Half of this is fixed: `--source` is now absolutised at install time (`_resolve_source`), so `_src_path` no longer resolves to the adopter's own repo and git commands run against the real template. What remains is Copier's own recording of `_commit` as a `git describe` string (`v0.7.0-12-g462ff24`) when installing from an untagged commit; that is not a resolvable ref, so `treaty diff`/`treaty update` on such a project still fail — now in the *correct* repo, with a raw plumbum traceback rather than a clear message. Released adopters are unaffected (they pin a real tag). Proposed: before using a recorded `_commit`, verify it with `git rev-parse --verify <ref>^{commit}` against a local template source and, when it fails, print a clear instruction to pass `--ref` explicitly instead of letting the traceback surface. Deliberately not bundled into the `_src_path` fix — it is a distinct defect and was not part of the approved scope.
- **Windows `git status --porcelain` can overreport updated files (claude-opus-5, 2026-08-12).** With `core.autocrlf=true`, porcelain lists line-ending-normalized files that a normalized `git diff --name-only` does not, so `_classify_status` can show more files under "Updated files" than substantively changed. Cosmetic, pre-existing, observed by Codex during the #20 Windows sweep. Low priority — no fix attempted. (The Unicode-arrow crash reported alongside it is **fixed** on `dev` in `fae916c`, shipping with the next release.)
- **Local adopter clones have drifted from their published state (claude-opus-5, 2026-08-12).** Cross-checking two independent sweeps: `desktop_app_source_updater` is pinned v0.4.1 on GitHub but v0.6.0 in the local working copy — a `treaty update` run locally and never pushed. `ai_crash_course` shows the same signature (identical pin, different conflict outcome between GitHub-clone and local-clone sweeps). Worth a pass to push or discard the local-only treaty updates before anyone reads adopter version numbers as authoritative.
- **v0.9.0 released 2026-08-13 — `treaty relocate` (claude-opus-5).** One command moves the working docs between layouts: `git mv`, link rewrites in `AGENTS.md`/`project_overview.md`, the `docs_dir` answer, and a `.gitignore` check, refusing to run before `treaty update`. `treaty validate` gained `treaty-doc-gitignored`. Windows-verified (Codex/GPT-5, #21). Minor rather than patch because the new validation code can newly fail an adopter's CI. **This is what unblocks recommending the nested layout to existing adopters** — the manual four-step procedure is gone from the README. Watch for: adopters hitting `treaty-doc-gitignored` and reading it as a regression rather than a latent problem it surfaced.
- **Adopters should update for this one.** Unlike most releases, v0.6.0 corrects docs that are actively wrong in every v0.5.0 project, not merely dated. Nine of eleven adopting repos were pinned two or more minors back as of 2026-08-01; Codex migrated four the same day (`sleep_scoring`, `desktop_app_source_updater`, `fp_analysis`, `pupil_tracking`), so five remain the outstanding work.
- Background: the adoption-badge feature shipped in v0.3.1; a follow-up logo color/layout polish landed afterward. The `ADOPTERS_TOKEN` PAT secret was added 2026-07-06, resolving the weekly workflow's code-search rate-limiting. On 2026-07-26 the counter was fixed to read `yzhaoinuw/*` repos directly (code search indexes only 6 of our 13 adopting repos); the badge went 6 -> 13.
- **Zenodo DOI: v0.7.0 (2026-08-01) is the first release since the integration was enabled**, so its GitHub Release should trigger the first archive (claude-fable-5). Follow-up: confirm the Zenodo record exists, then add the concept DOI to `CITATION.cff` under `identifiers:`, and consider a DOI badge in the README.
- **Adopters badge links to a search that disagrees with it** (open, small). The badge now reads 13, but its link goes to the GitHub code-search results page, which shows only the ~6 indexed repos. Options: point the link at a maintained `ADOPTERS.md` list, at the README badge section, or leave it and accept the mismatch. Needs a decision before anyone treats the link as authoritative.

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

- **Update the adopting repos.** Every `yzhaoinuw/*` repo carrying the treaty is now a v0.4.1 adopter facing the one-time `AGENTS.md` conflict. Running `treaty diff` then `treaty update` across them is both the migration and the first real-world test of whether the split behaves as measured.
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
