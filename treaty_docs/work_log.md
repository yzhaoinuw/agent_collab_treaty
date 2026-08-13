# Work Log

Prepend new session notes to the top of this file.

Rotation policy: the live log holds at most the **5 most recent unique calendar dates**. When a new date would push the file past 5 unique dates, move the oldest 5 dates as a chunk into a new file at `work_log_archive/work_log_<earliest>_to_<latest>.md`. The live file always holds at most 5 unique dates; each archive file always holds exactly 5.

If today's date already has a `## YYYY-MM-DD` header at the top, add a new `###` session subsection under it rather than starting a second `## YYYY-MM-DD` header for the same date.

<!--
Each session entry follows this shape:

## YYYY-MM-DD

### Short title for what was done (model + version, effort/thinking mode, token budget if known)

- bullet describing what was added or changed
- another bullet — keep them high-level and user/agent-facing, not implementation play-by-play
- if relevant, intended profiling signal or measurement:
  - what to look for in logs / output
  - what numbers were observed
- Verification:
  - the exact command(s) that were actually run
  - what passed / what was confirmed

Model / effort / token info goes in the parentheses after the `###` title when available from the system. Use whatever the model or interface actually reports — do not estimate or hallucinate. Omit any field that the interface does not surface.

- **Model**: the version string the interface reports (e.g. `grok-4.3`, `gpt-4o`, `claude-opus-4-7`).
- **Effort / thinking mode**: the effort knob the interface reports (e.g. `high`, `low`, `extended thinking`). Omit if no such knob exists or its setting is not surfaced.
- **Token budget**: **output tokens for the session** (output + thinking/reasoning tokens for models that report them separately, e.g. Claude with extended thinking). This is the cleanest cross-agent proxy for "amount produced." Omit if the interface does not surface a count.

Purely human-driven work can use `(human)`. Mixed human + agent sessions can combine them, e.g. `(human + grok-4.3, high)`.

Keep the parenthetical compact. Examples:
- `(grok-4.3, high, ~18k out)`
- `(gpt-4o, high, ~22k out)`
- `(claude-opus-4-7, extended thinking, ~30k out)`
- `(grok-4.3, low)`

Newest entry goes on top. If the session did multiple distinct pieces of work, use multiple `###` subsections under one `##` date header.
-->

## 2026-08-12

### Fixed a Windows crash in the treaty update summary (claude-opus-5)

- `_format_update_summary` printed `→` (U+2192), which is absent from cp1252 — the default console encoding on Windows — so `typer.echo` raised `UnicodeEncodeError`. Replaced with ASCII `->` in `cli.py` and in the five test assertions that pinned the old glyph.
- **Severity was higher than it looks, which is why this was worth a standalone fix.** In `update()` the merge is applied *before* the summary prints, so a Windows adopter got a fully applied update followed by a traceback — the natural reading is "the update failed", inviting a re-run or a manual revert of a change that actually succeeded. Shipped with the summary in v0.6.0.
- Found by Codex (GPT-5) during the Windows sweep on PR #20, where it was reported as an environment note (it worked around it with `PYTHONUTF8=1`). Reclassified as a bug after reproducing the encode failure directly.
- **Scoping decision:** kept off the `nested-docs` branch and committed straight to `dev`. The bug predates that branch and is unrelated to the layout work, so bundling it would have made a large layout review also a judgement on unrelated CLI output, and would have trapped a shippable fix behind an unmerged experiment. `nested-docs` will need a `dev` merge before it lands; expect a trivial conflict in `cli.py` and the touched test assertions.
- Checked the rest of the non-ASCII output rather than only the reported symptom: em-dash, curly quotes, and ellipsis all encode fine on cp1252, so no further changes. They would fail on legacy cp850/cp437, but those are not the modern console default and nothing has reported them — deliberately not churned.
- Verification:
  - `python -m unittest discover -s tests` — 59 tests, OK (1 skipped).
  - Re-ran the cp1252 simulation that reproduced the crash (encoding the rendered summary through a strict cp1252 writer): passes, output reads `Template version: v0.7.0 -> v0.8.0`.
  - `git diff --check`, `treaty --help`, `treaty --version`, `treaty validate .`, import smoke — all clean.

### Released v0.8.0 (claude-opus-5)

- Ships the `docs_dir` layout question (working docs under `treaty_docs/`, `AGENTS.md` and `project_overview.md` at the root), plus two pre-existing fixes that surfaced during its Windows review: the cp1252 crash in the update summary and the verbatim-recorded local template source. Minor bump, not major: the default layout for *new* installs changes, but no existing project is migrated and no CLI contract is broken.
- **The compatibility promise this release rests on:** every project installed before v0.8.0 is pinned to `docs_dir="."` by `_legacy_layout_data`, so `treaty update` moves nothing. Evidence, from two independent sweeps on different operating systems and different repo populations — 14 GitHub-cloned adopters on macOS (me) and 12 locally-cloned adopters on Windows (Codex/GPT-5) — each run twice against a v0.7.0 control: identical exit codes, identical touched-file sets, identical conflict sets, and zero relocation attempts in all 26 runs.
- Merged the `github-actions[bot]` adopters-badge commit (`0156677`, count 13 -> 14) from `main` into `dev` before releasing, so `dev -> main` stayed a fast-forward rather than diverging on the DAG. This is the weekly-workflow situation `AGENTS.md` warns about; diagnosed with `git log --left-right --cherry-pick` before touching anything.
- Verification:
  - `python -m unittest discover -s tests` — 79 tests, OK (1 skipped), run on the exact release commit.
  - `treaty --help`, `treaty --version` (reports 0.8.0), `treaty validate .`, `python -c "import agent_collab_treaty, agent_collab_treaty.cli"`, `git diff --check` — all clean.
  - Fresh render smoke-test into a scratch dir with `--ref HEAD`: nested layout installs and validates.
  - Version consistency confirmed across `pyproject.toml`, `src/agent_collab_treaty/__init__.py`, and `CITATION.cff` (`version:` and `date-released: 2026-08-12`).
  - Post-push ref verification with `git ls-remote --tags origin` and `git ls-remote --heads origin`.

### Merged PR #20 and absolutised local template sources (claude-opus-5)

- Merged `nested-docs` into `dev` as a **fast-forward**, deliberately not `--rebase`/`--squash`. `dev` was already an ancestor of the branch, so a fast-forward creates no merge commit and leaves `dev`/`main` unable to diverge on the DAG — which is the outcome the PR-merge rule in `AGENTS.md` exists to protect. It also preserves commit SHAs, and several are cited by hash in `work_log.md`, `next_steps.md`, and the PR discussion; rewriting them would have falsified our own records. GitHub marked #20 merged automatically once the head commit became reachable from `dev`.
- Fixed the `_src_path` half of the local-source papercut: `treaty init --source <local path>` now resolves the path to absolute before handing it to Copier (`_resolve_source`), so the recorded source keeps pointing at the template from anywhere. Remote specs (`gh:`, `https://`, `git+ssh://`) are passed through untouched, since they are not filesystem paths. Applied to `treaty diff --source` as well.
- **Deliberately only half the item.** The other half — Copier recording `_commit` as an unresolvable `git describe` string for untagged installs — is a distinct defect and was left alone rather than quietly widening an approved one-line fix. Effect after this change: the failure moves from "git runs in the adopter's own repository" (baffling) to "git runs in the correct template repository and fails on an unreal ref" (still a raw traceback). Re-logged in `next_steps.md` with a concrete proposal.
- Verification:
  - `python -m unittest discover -s tests` — 79 tests, OK (1 skipped); 4 new `_resolve_source` tests covering local paths, `.`, remote-spec passthrough, and what `init` actually hands Copier.
  - End-to-end: `treaty init --source . --ref HEAD` now records `_src_path: /Users/yuezhao/python_projects/agent_collab_treaty` instead of `.`.
  - `treaty validate .`, `git diff --check` — clean.

### Windows follow-up checks came back clean on PR #20 (claude-opus-5)

- Codex (GPT-5) re-ran the two remaining nested-layout checks on Windows at `815d0da`. Both pass: a case-mismatched `treaty_docs\Work_Log.md` resolves to the right docs directory (via both the recorded answer and the on-disk fallback) and yields `noncanonical-path-case` rather than `missing-required-file`; `treaty diff` against a nested project preserves relative paths, reports every doc under `treaty_docs/`, and still detects a heading rename inside the folder. Full suite 75 passed / 1 skipped with `PYTHONUTF8` explicitly absent, confirming the arrow fix holds at the real Windows console boundary.
- **Checked Codex's one deferral rather than accepting it.** It reported that `treaty init --source . --ref HEAD` produced a fixture whose `treaty diff` could not run, and classified it as a test-fixture limitation. Reproduced on `dev` with no layout branch involved — identical failure — so the classification is correct and it is not a #20 regression. But it is sharper than "fixture limitation": `_src_path: .` is recorded verbatim and afterwards resolves to the *adopter's own repo*, and an untagged install records `_commit` as an unresolvable `git describe` string. Logged in `next_steps.md` with a proposed fix; kept out of #20 for the same reason as the arrow.
- Nothing outstanding from the Windows side now blocks a merge decision on #20.
- Verification:
  - Reproduced the `_src_path` papercut on `dev` (`treaty init --source . --ref HEAD` then `treaty diff`) and on `nested-docs`; both record `_src_path: .` and a `git describe` `_commit`, both fail the same way.
  - `git rev-parse --verify v0.7.0-8-g815d0da` — not a ref, confirming the describe string is unresolvable.

### Acted on the Windows sweep from Codex (GPT-5) on PR #20 (claude-opus-5)

- **Fixed a real bug Codex found:** `root_prefix` was a hardcoded `../`, so a multi-segment `docs_dir` (e.g. `docs/agents`, which `README.md` advertises) rendered links resolving one level short — `docs/AGENTS.md`, which does not exist. Reproduced, then made the prefix depth-aware (`'../' * segment_count`). Verified at depths 1–3 plus a trailing-slash value; regression test added. Chose depth-awareness over restricting `docs_dir` to one segment because the README already documents the multi-segment form.
- **Independent Windows confirmation of the compatibility claim:** Codex swept 12 local Git adopters, each run twice (PR head `4203d4d` vs. an unmodified v0.7.0 control) — 12/12 identical exit codes, updated-file sets, and conflict sets; no `treaty_docs` mention anywhere; `docs_dir: None -> '.'` on all 12. `core.autocrlf=true`, full suite passed, and the byte-identical guard passed without touching its baseline.
- **Two sweeps disagreed on absolute numbers, and the reason matters.** Mine cloned GitHub default branches; Codex cloned local working directories. `desktop_app_source_updater` is v0.4.1 on GitHub but v0.6.0 locally — a `treaty update` that was **run locally and never pushed**. `ai_crash_course` is v0.3.1 in both but conflicted in my sweep and came back clean in Codex's, consistent with the same divergence. The *delta* (branch vs. control) was zero in both sweeps, which is the claim actually under test; the absolute conflict counts are a property of the snapshot, not of this change. Do not treat either sweep's conflict totals as the state of the published repos.
- Codex also covered three adopters my sweep missed (`career_dev`, plus local-only dirs) and skipped `vessel_pulsatility` (not a git repo, so Copier cannot update it).
- **Not fixed here, pre-existing:** `_format_update_summary` emits `→` (U+2192), which raises `UnicodeEncodeError` on a default Windows cp1252 console — confirmed locally by encoding the line. Codex worked around it with `PYTHONUTF8=1`. Introduced with the summary in v0.6.0, unrelated to this branch; kept out of PR #20 to keep the layout review clean. Also pre-existing: with `core.autocrlf=true`, `git status --porcelain` can list line-ending-normalized files that a normalized `git diff --name-only` does not, so `_classify_status` can overreport "Updated files" on Windows.
- Verification:
  - `python -m unittest discover -s tests` — 75 tests, OK (1 skipped); new `test_multi_segment_docs_dir_gets_a_depth_aware_root_prefix` passes and the v0.7.0 byte-identical guard still passes unchanged.
  - Rendered `docs_dir` at `treaty_docs`, `docs/agents`, `a/b/c`, `trailing/slash/`, and `.` — every `AGENTS.md` link resolves to a real file from the conventions doc's directory.
  - `treaty validate .`, `treaty --help`, `treaty --version`, import smoke, `git diff --check` — clean.

### Made the docs layout a Copier answer instead of a template move (claude-opus-5)

- Added a `docs_dir` question so adopters' working docs (`treaty_conventions.md`, `next_steps.md`, `work_log.md`, `work_log_archive/`) install under `treaty_docs/`, and dogfooded that layout in this repo. `AGENTS.md` and `project_overview.md` stay at the root — `AGENTS.md` because agents resolve the *nearest* file up the tree, so a nested one would scope to the wrong subtree, and `project_overview.md` because it is the one treaty doc a human newcomer opens, and keeping it put also keeps the most-customized file away from any relocation risk.
- **Decision: layout is an answer, never a template-side file move.** Measured on copier 9.15.1 in throwaway templates:
  - A naive move (template file relocated, no migration) **silently destroys adopter content**: Copier deletes the customized file and writes a pristine one at the new path. No conflict, no warning — only `D work_log.md` in `git status`. An adopter running `git add -A` loses the log from HEAD.
  - A `_migrations` before-hook doing `git mv` preserves content but then conflicts in **every** moved file for **every** adopter — verified even on a pure move with zero content change, because Copier renders the old version at the old path so the moved file always reads as add-vs-existing. It also requires `--trust`.
- Rejected approach worth not re-deriving: `_copier_operation` is **undefined** inside question defaults (probed directly — it renders as `UNDEFINED`), so Copier cannot distinguish copy from update on its own to pick a per-operation default. The legacy pin therefore lives in our CLI wrapper (`_legacy_layout_data`), which injects `docs_dir="."` when the answers file has no recorded value.
- Also rejected: `docs_dir=""` for the flat layout. An empty path segment makes Copier skip the entire directory (the same rule the `{% if %}` conditional-file trick relies on) and renders links as `/work_log.md`. The flat answer must be `"."`, which resolves to the root correctly.
- Recorded the resulting invariant in `AGENTS.md`: with `docs_dir="."` the template must render **byte-identical** to v0.7.0, because every pre-v0.8.0 adopter is pinned there. Found the hard way — a single added line in `project_overview.md`'s tree diagram conflicted for every adopter until the flat branch was made an exact match. `tests/test_docs_dir.py::test_flat_layout_is_byte_identical_to_v070` now diffs the whole rendered tree against the `v0.7.0` tag.
- **Warning for future verification runs on macOS:** `timeout` does not exist here (it is `gtimeout` from coreutils). The first adopter dry-run batch used it, so no dry-run actually executed and the harness reported a clean `exit=0` for all 14 repos. An all-green result that arrives too easily is the signal to check the harness, not the change.
- Shared state: branch `nested-docs` pushed to origin. Not merged to `dev` — a Windows pass is still outstanding, because `docs_dir` is now a path segment and `required_paths()` builds POSIX-style strings while Copier renders paths with the OS separator.
- Verification:
  - `python -m unittest discover -s tests` — 74 tests, OK (1 skipped); includes 13 new `docs_dir` tests and the byte-identical guard.
  - `treaty validate .` on this repo after the dogfood move — passed, resolving `docs_dir` via on-disk detection since this repo has no `.copier-answers.yml`.
  - `treaty --help`, `treaty --version`, `python -c "import agent_collab_treaty, agent_collab_treaty.cli"`, `git diff --check` — all clean.
  - Real-adopter dry-runs across all 14 Copier-managed `yzhaoinuw/*` repos, each run twice (branch vs. an unmodified-v0.7.0 control): **identical conflict sets and identical touched-file sets in 14/14**, zero occurrences of `treaty_docs` in any output, and `docs_dir: None → '.'` on every repo. Nothing was written to any remote.
  - End-to-end fixtures: v0.7.0 adopter updating (stays flat, no conflicts, history intact); the same project relocating and then taking a further upstream release (merges cleanly at the new paths); fresh install (nested, `treaty validate` passes).
- Side-finding, not addressed here: eight of the 14 adopters are pinned at v0.2.0–v0.3.3, predating the v0.5.0 AGENTS/conventions split, and will conflict on `AGENTS.md`/`project_overview.md` whenever they next update — independent of this change.


## 2026-08-01

### Released v0.7.0 (claude-fable-5)

- Cut v0.7.0 same-day as the work it ships: the real `treaty update --dry-run` merge preview with apply-matching exit codes (#16, with #18 closed as its duplicate) and gitignored `.copier-answers.yml` detection at init, validate, and dry-run (#15's top item). Minor bump because the dry-run exit-code contract changed (previously always 0; now non-zero on a predicted conflict).
- Version bumped in `pyproject.toml`, `src/agent_collab_treaty/__init__.py`, and `CITATION.cff` (`date-released` was already 2026-08-01). Annotated tag `v0.7.0` on the `dev` release commit, matching the v0.6.0 precedent; `release.yml` handles PyPI trusted publishing and the GitHub Release with generated notes. The `dev → main` merge is left to the maintainer per branch policy — at release time `main` was exactly one fast-forward behind `dev`, no bot commits.
- This is the first `v*` release since the Zenodo–GitHub integration was enabled, so it should trigger the first archive and mint the concept DOI. Follow-up (tracked in `next_steps.md`): confirm the Zenodo record, then add the DOI to `CITATION.cff` `identifiers:` and consider a README badge.
- Verification:
  - `git diff --check`; full `python -m unittest discover -s tests` (59 tests including the Copier-merge integration tests, no skips taken); `treaty validate .`; `treaty --version` reports 0.7.0; import smoke check.
  - After pushing: `git ls-remote --tags origin` shows `v0.7.0`, `git ls-remote --heads origin dev` matches local, and the release workflow run was watched to completion.

### Codex migration feedback triaged; dry-run made a real preview; ignored-metadata checks (claude-fable-5)

- Codex (GPT-5) migrated four adopter repos to v0.6.0 and filed one issue per repo: #15 (`sleep_scoring`, legacy hand-copied adoption), #16 (`desktop_app_source_updater`), #17 (`fp_analysis`), #18 (`pupil_tracking`). Overall verdict positive (7.5/10 on the hardest case), with no data loss and conflicts always flagged non-zero — the v0.5/v0.6 machinery held up in the field.
- **#16 and #18 are the same defect filed twice.** Codex's per-repo sessions ran ~90 seconds apart and did not see each other's issues (#18 cross-references #10/#14/#15 but not #16). Process lesson for future fan-out reviews: file sequentially against a shared issue list, or dedupe at the end. #18 closed as the duplicate.
- **Fixed the defect (#16/#18):** `treaty update --dry-run` printed only boilerplate because Copier's `pretend=True` never materializes the merge. It now runs the real update in a disposable `git clone` of the project's committed state and prints the same summary as apply (answer changes, updated files, conflicts). Exit-policy decision the issue left open: **dry-run exits non-zero when the merge would conflict, matching apply** — parity is the more scriptable contract. macOS gotcha: the temp clone path must be `.resolve()`d or Copier's repo-root detection trips over the `/var → /private/var` symlink.
- **Fixed #15's top item:** an adopter's `.gitignore` can silently swallow `.copier-answers.yml` (that is exactly what happened in `sleep_scoring`). `treaty init` now warns when git ignores the answers file, `treaty validate` gained `answers-file-gitignored`, and the dry run errors clearly when the answers file exists but is not committed. A *missing* answers file stays legal — this repo dogfoods the docs without Copier management — so only present-but-ignored is an error.
- Deliberately not done: #17's new-question handling (`--ask-new` / `--set`) — the dry-run fix at least previews the proposed defaults now. Flipping the opt-out question defaults to `false` was considered and rejected: `CopierConfigContractTests` pins them `true` by design ("existing code repos see no change"). #15's `treaty adopt`/`doctor`, risk-classed `treaty diff` headlines, and `--version` source provenance stay parked pending more adopter evidence.
- Verification:
  - `git diff --check`; full `python -m unittest discover -s tests` (59 tests, including 3 new real-Copier dry-run integration tests and 3 new validation tests); `treaty validate .`; `treaty --version`; import smoke check; `treaty update --help` renders the new dry-run contract.

### Added CONTRIBUTING.md; ORCID in CITATION.cff (claude-fable-5)

- Added the maintainer's ORCID (0000-0002-0819-5012) to `CITATION.cff`.
- **Reversed a same-day decision, at the maintainer's request:** the README restructure earlier today deliberately kept Developer Notes in the README instead of creating `CONTRIBUTING.md` ("revisit if it grows"). The maintainer reopened it in the Zenodo/citability context, and two things tipped it: `template/AGENTS.md.jinja`'s doc map already lists `CONTRIBUTING.md` "(if present)", and community guidelines are a checklist item if a JOSS-style submission ever happens.
- What moved: README "Developer Notes" (release workflows, cutting a release, trusted-publisher setup) → `CONTRIBUTING.md` § Releases. The README tail is now a short Contributing pointer, which also shortens the PyPI render.
- What deliberately did **not** move: nothing from `AGENTS.md` or `project_overview.md`. Those are the dogfooded treaty — the product itself — so `CONTRIBUTING.md` links into them (§ Common Tasks, § Project-Specific Reminders) rather than duplicating, which would create drift between copies.
- Cross-references updated: root `AGENTS.md` doc map, `project_overview.md` structure map and active-docs list.
- Verification:
  - `git diff --check`; full `python -m unittest discover -s tests -v` (51 tests incl. real Copier merges); `treaty validate .`; `treaty --version`; import smoke check.
  - `cffconvert --validate -i CITATION.cff` after the ORCID edit.
  - README ToC anchor `#contributing` matches the new heading; the only remaining "Developer Notes" mentions are historical work-log prose.

### Added CITATION.cff for Zenodo/DOI archiving (claude-fable-5)

Decision: archive the repo on Zenodo for a DOI. The reasoning that settled it — the value is citability (methods sections in the maintainer's research papers, software output on a CV) and archival permanence, not prestige; a DOI alone is not an academic contribution. A JOSS submission was considered and deliberately not pursued: a workflow/documentation tool is likely out of their research-software scope, and a paper about the workflow pattern itself would be the real route to credit if ever wanted.

- Added `CITATION.cff` (pinned to v0.6.0, released this date). GitHub now shows "Cite this repository", and Zenodo reads it as metadata. No DOI in the file yet — see below.
- Timing gotcha worth remembering: the maintainer enabled the Zenodo–GitHub integration *after* the v0.6.0 GitHub Release was created, and the webhook only fires on releases created after enabling. So no archive exists yet; the first DOI comes with the next `v*` release or a manual upload. Tracked in `next_steps.md`.
- `CITATION.cff` adds a third place the version lives. The release checklist in `AGENTS.md` now says to bump `version:` and `date-released:` there alongside `pyproject.toml` and `__init__.py`.
- Verification:
  - `cffconvert --validate -i CITATION.cff` (schema-valid CFF 1.2.0; pipx is absent on this machine, cffconvert was pip-installed into the base env).
  - `git diff --check`; full `python -m unittest discover -s tests -v` including the Copier-merge integration tests; `treaty validate .`; `treaty --help` / `--version` and import smoke checks.

### Released v0.6.0 (claude-opus-5)

Cut the release covering everything logged under this date plus 2026-07-30's issue work. Ran a pre-release audit rather than assuming the tree was ready, which turned up two gaps worth fixing first:

- The **post-install message contradicted the README**. It still told users to open `AGENTS.md` and fill placeholders by hand, with no mention of the agent prompt that had just become the documented path. That message reaches people who install via Copier directly and never read the README, so it mattered more than the README line did.
- **`treaty --version` was effectively invisible** — the whole deliverable of #13 appeared once, inside a collapsible.

The release body leads on the `template/work_log.md` fix, because it is the only change that makes an existing adopter's docs *wrong* rather than merely dated: every v0.5.0 adopter is carrying work-log criteria that contradict their own `treaty_conventions.md`. Updating is what corrects it. That is also the counterexample to the update-notification idea parked earlier the same day — being behind is usually harmless, which is why it was parked, but this release is the exception, so it is worth saying loudly in the notes rather than relying on adopters noticing.

- Verification:
  - Pre-release audit: version consistency, stale version references (two hits, both correct history), leftover TODO/FIXME (none — the hits are `adoption.py` detecting `TODO.md`, which is intended), and the post-copy message rendered from a real `treaty init`.
  - Full suite **51 tests, ~13s** including real Copier merges; `treaty validate .`; `git diff --check`; import check.
  - README: 15 external links 200, no dead anchors, ToC parity, PyPI render, adopters-badge `sed` pattern intact.
  - Fresh render: `AGENTS.md` 132 lines, `treaty_conventions.md` 98, `treaty validate` passes, and the new `work_log.md` → `treaty_conventions.md#work-log-discipline` link resolves against a real heading.
  - `git fetch` + divergence check before touching `main`; refs confirmed with `git ls-remote` after pushing; release workflow watched to completion; published wheel installed from PyPI in a clean venv.

### Restructured the README around install → usage → update (claude-opus-5)

The maintainer found the README dragging and branching instead of getting to the point. Reordered it so the value proposition is followed immediately by Install, Quick Start, Update, and Validate, with caveats pushed into `<details>` and maintainer material moved last under **Developer Notes**. Added a top-level table of contents.

Two judgment calls worth recording:

- **The problem was partly duplication, not just ordering.** The "Rotation Policy" section restated what `treaty_conventions.md` has owned since v0.5.0, and the maintenance-ownership split was explained twice in the intro. Reordering alone would have relocated the sprawl, so both were cut down to pointers. This is the README's half of the same principle the template now follows: say it in one place, link from the others.
- **A hand-maintained ToC is a rot risk** and GitHub already auto-generates one in its header menu — but that menu does not exist on PyPI, where this README is the package long description. Kept it, restricted to top-level headings so there is less to go stale.

Deliberately **not** done: moving Developer Notes into `CONTRIBUTING.md`. That is the conventional home and the treaty's own doc map already references it, but the maintainer asked to avoid a new doc, and the section is small enough that a README tail is fine. Revisit if it grows.

- Verification:
  - `readme_renderer[md]` render of the file — confirms it renders for PyPI and that `<details>`, `<summary>`, and `<table>` all survive PyPI's HTML sanitizer. This was the real risk of the collapsible approach and it needed checking rather than assuming.
  - Ran the adopters-badge workflow's exact `sed -E "s/adopters-[0-9]+-6d81f1/.../"` against the rewritten file — still matches, so the weekly badge refresh will not silently stop updating.
  - Anchor audit: every `](#...)` link resolves against a real heading; ToC entries and `##` sections match exactly in both directions; no other file links to a README anchor.
  - 315 → 273 lines, of which 101 sit inside 7 collapsibles, so 172 lines are visible on load — roughly half the original weight.

### Led the README with both purposes (claude-opus-5)

Follow-on to the restructure above, and the more consequential half. The maintainer named a **second purpose the README had never stated**: the treaty is also a work planning and logging system for humans — status, progress, something to report from — not only an agent-handoff protocol. Positioning, not a feature request.

- Rewrote the description as a lead plus two parallel bullets, **Agent handoff** and **Planning and work log, for you**. The two-jobs framing is what compressed it: both purposes share one sentence of setup instead of each needing a paragraph. Three paragraphs → one lead, two bullets, one closer.
- Deleted the second intro paragraph, which enumerated what agents learn from each file. Every item in it was already a row of the "What's In The Template" table two screens below — a mid-level explainer duplicating what it introduced. Nothing was relocated, because the table already carried it.
- Added three sentences to "The Workflow In Practice", which had been framed entirely around agent sessions. Without them the human-facing claim in the description had nothing downstream supporting it. They tie the second purpose to the existing decisions-not-activity rule: that rule is *why* the log reads as a status update rather than an audit trail.

Worth keeping in mind for future doc work here: a positioning claim added to the top of a README needs at least one section further down that makes it real, or it reads as marketing.

- Verification:
  - Confirmed "five Markdown files and an archive folder" against an actual `treaty init` render rather than counting from memory — `AGENTS.md`, `treaty_conventions.md`, `project_overview.md`, `next_steps.md`, `work_log.md`, plus `work_log_archive/`.
  - Re-ran the full check set after the edit: `readme_renderer[md]` render (collapsibles intact), the badge workflow's `sed` pattern, and the anchor audit. All clean. Final size 315 → 276 lines.

### Added a "See It In A Real Project" section to the README (claude-opus-5)

The README described a work log without ever showing one. Added a short section after "What's In The Template" linking to live treaty docs in two long-running adopters, plus this repo.

**Selected on evidence, not recall.** Surveyed all 27 public non-fork `yzhaoinuw` repos via the GitHub API, filtered to the 11 carrying `work_log.md`, and ranked by archive depth, session count, `next_steps.md` size, and recency. `sleep_scoring` (deepest history, most stars, published research software) and `fp_analysis` (longest span, richest live log, and a proper Copier-managed install) won, and they are complementary rather than redundant.

Two decisions worth keeping:

- **Linked `work_log.md` and `next_steps.md` only — deliberately not `AGENTS.md`.** Both adopters are pinned to pre-v0.5.0 templates (`fp_analysis` at `v0.3.2`; `sleep_scoring` was hand-copied and has no `.copier-answers.yml`), so their `AGENTS.md` shows the old undivided layout. Linking it would show a newcomer a structure the current release no longer produces. The log and roadmap formats are stable across versions, so they demonstrate the treaty without misrepresenting it.
- **Used absolute GitHub URLs for this repo's own two links**, not relative paths. Relative links break on PyPI, where this README is the package description, and these sit beside two absolute links in the same list.

The entry counts will drift as those repos grow. They only ever undercount, so staleness is safe — but a future session refreshing this section should re-measure rather than trust the numbers.

- Verification:
  - Counted archive chunks and dated entries by fetching and parsing each file, after a first pass **overcounted `sleep_scoring` as 9 chunks / ~45 dates** — the listing included `work_log_archive/README.md`, and the hand-adopted repo does not follow the exactly-5-dates-per-chunk rule. Corrected to 8 chunks / 39 dated entries before it reached the README.
  - `curl` over all 13 external links in the README — every one returns 200.
  - Anchor audit, ToC/section parity, `readme_renderer[md]` render, and the badge `sed` pattern — all clean.

### Shortened the prompts, and fixed the template gap that made them long (claude-opus-5)

The maintainer's point: a verbose prompt sample is evidence the **template** is under-specified, since the product thesis is that an agent knows what to do from minimal instruction. Re-derived each prompt by checking what a rendered project already tells an agent.

- `"Update the treaty."` is sufficient — verified `treaty_conventions.md` ships the full five-step procedure and `AGENTS.md` links to it, which the Startup Rule guarantees the agent reads. The old prompt restated our own product back at it.
- `"Fill out the docs in the treaty."` is sufficient for the placeholders (20 in `AGENTS.md`, 32 in `project_overview.md` — self-evident once read), but **one instruction genuinely had no home in the template**: leave `work_log.md` empty at onboarding. Added it to `template/work_log.md` rather than to the README prompt. That is the right fix: guidance an agent needs belongs where the agent will be, not in a README it may never see.
- Install prompt now names the package and the installer (`pip install agent-collab-treaty`) rather than the human-readable project name, so it works pasted into a cold session with no prior context.

**Found a real bug while in there.** `template/work_log.md` still carried the pre-v0.5.0 activity-shaped criteria ("file edits, meaningful validation or debugging...") — the P4 rewrite updated `treaty_conventions.md` and missed this copy, so the shipped template contradicted itself and duplicated a rule that now lives elsewhere. Replaced with the decisions-not-content line plus a pointer.

**Declined the literal "human read this / agent read this" split** the maintainer floated. The README's audience is humans deciding whether to adopt; the agent's instructions are the installed template. Needing an agent-facing section in the README would itself be the smell that the template is incomplete. Streamlined for humans instead: one prompt per section, mechanics behind `Prefer to run it yourself?` collapsibles. Visible-on-load prose dropped 172 → 160 lines even while adding the prompt blocks.

- Verification:
  - Rendered a fresh project and asserted each short prompt has in-repo support: placeholder counts, the new leave-it-empty line, the criteria pointer, the `AGENTS.md` → conventions update link, and the five-step procedure. Confirmed the stale wording is gone.
  - 15 links 200, anchors and ToC parity clean, PyPI renders, badge `sed` matches, `treaty validate` passes on the render.

### Led the README's setup path with agent prompts (claude-opus-5)

The maintainer pointed out an inconsistency: a package whose selling point is agent autonomy had a README assuming you type everything by hand, when in practice he sets these up by asking an agent. Install, Quick Start, and Update now lead with the prompt, then show the command underneath.

**Pushed back on replacing the commands entirely**, which was offered as an option. The prompts only work *because* the commands are documented — an agent landing on the PyPI page reads the README to learn what `treaty init` does, so a prompt-only README is circular. A Python package with no `pip install` line also reads as broken to anyone evaluating it, and conflict recovery needs the exit-code and `git add` semantics. Adjacent, prompt first, is the version that serves both.

- The onboarding prompt fills a **genuine content hole**: the README never explained how the bracket placeholders get filled. That is the step that makes the treaty useful and the one an agent does better than a human, since it can read the whole repo first.
- **Caught myself teaching the anti-pattern.** The first draft of that prompt said to seed `work_log.md` from recent git history — which is exactly the "implemented function X" noise the log exists to avoid, since git history *is* the diff. Rewrote it to seed only `next_steps.md`, and added an explicit line telling adopters to leave `work_log.md` empty until the next session. Worth remembering: the treaty's own rules apply to the instructions we write about it.
- The description claimed "two prompts" while the draft had three. Merged install and `treaty init` into one ask, matching how the maintainer actually drives it, rather than weakening the claim to a vague count.

- Verification:
  - Rendered through `readme_renderer[md]`: 4 blockquotes render, and markdown **inside** `<details>` is fully processed on PyPI — checked the emitted HTML directly rather than assuming, since a collapsible that renders as raw markdown text on the package page would have been a silent regression from the earlier restructure.
  - All 15 external links 200; anchors and ToC parity clean; badge `sed` pattern still matches. 300 lines.

### Closed out #13 and #14: `treaty --version`, and real merge tests (claude-opus-5)

**#13 — `treaty --version`.** Eager top-level Typer callback printing the CLI version, plus the pinned `_commit` and `_src_path` when run inside an installed project. Reuses `_read_answers(...)`. Confirmed `no_args_is_help` still behaves: bare `treaty` prints help and exits 2, checked against the **published v0.5.0 wheel** in a scratch venv rather than assumed, since that is the pre-change build.

**#14 — real Copier merge tests.** `tests/test_update_integration.py`, 10 tests, closing the gap where every update test mocked `copier.run_update`.

- **Synthetic throwaway template, not this repo's own.** Testing against our real template would couple the tests to release history and to tags surviving a shallow CI checkout. A two-commit template built in a temp dir drives the identical Copier code path with none of that fragility.
- Covers: clean update, local edits outside the changed region surviving, overlapping edits conflicting with a non-zero exit and named file, upstream file additions landing in an older project, answer reuse without reprompting, and the hidden-alias migration.
- `CopierConfigContractTests` asserts the properties of our **real** `copier.yml` that adopters depend on: `test_command` hidden, declared after `verification_command`, and inherited by its default. Pure YAML parsing, so it runs even in fast mode.
- Added `test_alias_declared_before_its_replacement_loses_the_answer`, which pins the *failure* mode — Copier clearing a hidden question's answer as it walks past it. If a future Copier release stops doing that, this test tells us the declaration-order constraint can be dropped, instead of us carrying a cargo-culted rule forever.

Two things worth keeping:

- **The first migration test failed for a fixture reason, not a product one**, and the output proved it: the answers migrated correctly (`test_command: 'pytest -q' → None`, `verification_command: None → 'pytest -q'`) while `AGENTS.md` conflicted. The cause was a hand-written baseline `AGENTS.md` that never matched what template v1 would render, so the three-way merge had no sane common ancestor. Rebuilt as a genuine two-version template. **Lesson: an update fixture's baseline must come from an actual render of the old template, never from hand-written content.**
- **Mutation-tested the guard rather than trusting a green run.** Reordered `copier.yml` to put `test_command` first and confirmed `CopierConfigContractTests` fails with the explanatory message, then restored the file and verified it byte-identical via `git diff --stat`. A guard test that passes but would not fail is worse than none.

- Verification:
  - Full suite **51 tests, ~13s, all pass**; `TREATY_SKIP_INTEGRATION=1` → 0.14s with 8 skipped (7 integration + the pre-existing case-collision skip), contract tests still running.
  - `treaty --version` checked in three states: inside an installed project (prints both lines), in this repo which has no `.copier-answers.yml` (CLI line only), and bare `treaty` (help, exit 2, unchanged from the published build).
  - `treaty --help` reviewed for duplicate help text after adding the callback — clean.

## 2026-07-30

### Released v0.5.0 (claude-opus-5)

Cut the release for the issue #12 work logged on 2026-07-29. The maintainer authorized the full sequence — merge, tag, and publish — in this session rather than doing the `dev → main` merge themselves.

- `dev` was exactly one commit ahead of `main` with no divergence, so the merge was a plain fast-forward. No adopters-badge bot commit had landed since v0.4.1.
- Tagged `v0.5.0` on `main` and pushed, firing `release.yml` (PyPI trusted publishing + GitHub Release).
- The auto-generated release notes were replaced with a body that leads on adopter impact: the `treaty_conventions.md` split costs anyone who customized `AGENTS.md` a **one-time** merge conflict, and they should run `treaty diff` before updating. `generate_release_notes: true` alone would not have said this, and it is the one thing an adopter needs to know before running `treaty update`.

- Verification:
  - `git fetch --all --tags`, `git log --left-right --cherry-pick origin/main...dev` — confirmed a single commit ahead, no divergence, before touching `main`.
  - `python -m unittest discover -s tests` (38 pass, 1 skipped), `treaty validate .`, `git diff --check` — all clean at the tagged commit.
  - `git ls-remote --tags origin` and `git ls-remote --heads origin main` — confirmed the pushed refs.
  - Watched the `Release to PyPI` workflow to completion and confirmed the published version.

### Bumped workflow action pins off deprecated Node 20 (claude-opus-5)

The v0.5.0 release run succeeded but annotated that `actions/checkout@v4`, `actions/setup-python@v5`, and `softprops/action-gh-release@v2` target Node 20 and were being force-run on Node 24. Bumped to the current majors — `checkout@v7`, `setup-python@v7`, `action-gh-release@v3` — across all three workflows.

- `pypa/gh-action-pypi-publish` stays on `release/v1`. It is a **composite** action, so it has no Node runtime to deprecate, and `release/v1` is pypa's own recommended floating pin.
- Checked the intervening majors for breaking changes rather than bumping blind. Three mattered in principle and none apply here: `checkout@v7` blocks fork-PR checkout for `pull_request_target` / `workflow_run` (neither trigger is used in this repo), `setup-python@v6` moved to Node 24 and requires runner ≥ v2.327.1 (GitHub-hosted runners are past it), and `setup-python@v7` removed the `pip-install` input (not used).

- Verification:
  - `python -c "yaml.safe_load(...)"` over all three workflow files — parse clean.
  - Dispatched `test-publish.yml` on `dev` (`gh workflow run --ref dev`) so the bumped pins ran end to end before reaching `main`. It exercises the same checkout → setup-python → build → publish shape as `release.yml`, against TestPyPI. Run succeeded with **no Node deprecation annotation**.
  - `gh run view --log` on the release-path steps to confirm the annotation is gone rather than merely unreported.

### Issue triage after the release (claude-opus-5)

- **#12 closed** as completed, with a comment mapping each proposal to what shipped and naming the trigger for revisiting full P3: adopter reports that the vocabulary still doesn't fit *now that the split has landed*, not a schedule.
- **#10 stays open, scoped down to items 6–7.** Item 5 is answered by the `treaty_conventions.md` split rather than by the managed-section markers it proposed — splitting by maintenance ownership removes the collision instead of asking a merge to respect marker regions. Its stated minimum acceptance criteria were already met in v0.4.0, so offered to split 6–7 into their own issues and close it; awaiting the maintainer's call.
- Item 7 is worth being precise about: every update test in `tests/test_cli.py` mocks `copier.run_update`, so the real three-way merge is still unexercised in CI. The v0.5.0 migration and conflict paths were validated against git-backed scratch projects **manually** — recorded in the 2026-07-29 entry, not committed as tests. That gap is the whole of item 7.
- The maintainer is migrating the other adopting repos themselves and will file issues if anything surfaces.
- **Then split and closed #10** on the maintainer's call: item 6 became #13 (`treaty --version`), item 7 became #14 (real Copier-merge tests), both labeled `enhancement`. #14 carries the two things that cost time to rediscover — the `--ref HEAD` requirement for local template sources, and the declaration-order dependency between `test_command` and `verification_command` in `copier.yml`.

- Verification:
  - `gh issue view 10/12` — confirmed #12 CLOSED (COMPLETED) and #10 OPEN with the comment posted.
  - `treaty --version` errors and `rg 'patch\("copier' tests/test_cli.py` returns 7 hits — confirmed items 6 and 7 are genuinely open before reporting them as such.

## 2026-07-29

### Issue #12: split the template by maintenance ownership, add `treaty diff` (claude-opus-5, plan mode then execute)

Issue #12 came from adopting the treaty into a **non-code repo** (a novel), where 11 of 12 `AGENTS.md` sections had to be rewritten or deleted. The measured finding that drove the design: **conflict risk tracks whether a section's body is maintained upstream, not how much the adopter edited it.** `project_overview.md` changed 135 lines against an 89-line original with almost no merge risk, because its body is all bracket placeholders upstream will never revise.

So the template is now split by who maintains what:

- **`AGENTS.md`** keeps the project's own answers — runtime, tasks, doc map, reminders — with short bodies. Upstream does not revise these.
- **`treaty_conventions.md`** (new) holds the mechanics we do revise: work-log criteria, dated-entry and rotation rules, branch handoff, the release gate, and the `treaty update` procedure. Adopters are told not to edit it. This is #10 item 5, arrived at without managed-section markers.

Every `##` heading survived the split — only bodies shrank. A rename would have handed every existing adopter an unresolvable conflict.

Also landed:

- **Three opt-out questions** (`has_releases`, `uses_precommit`, `include_git_ownership_note`), all defaulting to true so code repos see no change. Answering no is strictly better than deleting: a section that never renders can never conflict.
- **`treaty diff`** — renders the pinned template to a temp dir and reports per-section untouched/modified/removed/added, flagging **renamed headings** specifically. `work_log.md` and `next_steps.md` are exempt from the risk total; their drift is the point of the treaty.
- **`verification_command`** replaces `test_command` (a test runner, a linter, a link checker, and `treaty validate` are all the same slot). `env_activation` now accepts `none` for repos that deliberately have no environment.
- Work-log criteria restated around **decisions, not the content of the work produced** — "implemented function X" and "drafted chapter 4" are noise for the same reason.
- `project_overview.md` gained an **Authored vs. Derived** axis alongside Active vs. Legacy. Getting that one wrong is destructive in a way active/legacy usually isn't.

Deliberately **not** done: the full `project_kind` question from P3. Jinja conditionals across a doc template get unmaintainable fast, and the split above removes most of its motivation.

Two things worth not rediscovering:

- Rendering a **local** template source uses that repo's git HEAD, not the working tree. The first smoke test silently rendered the old template and reported 219 lines. `--ref HEAD` is required.
- `copier.yml` declares `test_command` with `when: false` as the legacy alias, and it **must stay declared after `verification_command`**. Copier renders question defaults in declaration order and *deletes* a `when: false` question's recorded answer as it passes it, so reordering would silently drop every adopter's migration. Confirmed by reading `copier/_main.py::_ask`, then by an end-to-end update.

Line counts, all measured on a real render: default `AGENTS.md` **219 → 132** lines (the template's own stated target is under 150, which #11 flagged it for missing); with the three sections opted out, **91**, plus a 77–98 line `treaty_conventions.md` that nobody has to read at session start.

- Verification:
  - `python -m unittest discover -s tests -v` — 38 tests, 1 skipped, pass (11 new in `tests/test_diff.py`, 3 new in `tests/test_cli.py`).
  - `treaty init` renders with `--ref HEAD`: full defaults (132 lines), all three sections opted out plus `env_activation=none` (91 lines), `treaty validate` passes on both.
  - **Migration**: v0.4.1 project with `test_command: pytest -q` → update to HEAD. Result: `verification_command: pytest -q`, `test_command` gone from `.copier-answers.yml`, the value wired into the rendered `AGENTS.md`, `treaty_conventions.md` added, **zero conflicts**.
  - **Customized adopter**: v0.4.1 project with the three sections deleted and two bodies rewritten → `treaty diff` predicted 4 at-risk sections beforehand; the update then produced exactly 3 conflict hunks in `AGENTS.md`. The one-time cost of the split is real, is confined to `AGENTS.md`, and is now visible before you run the update.
  - `treaty diff` end-to-end on a clean render (0 exposure) and on one with a renamed + deleted heading (flagged both).
  - `git diff --check` clean; `python -c "import agent_collab_treaty, agent_collab_treaty.cli"` ok.

Version bumped to **0.5.0** in `pyproject.toml` and `__init__.py`. Not tagged in this session — released the next day, see 2026-07-30.

## 2026-07-26

### Adopter count fixed: read our own repos directly instead of trusting code search (claude-opus-5)

The adopters badge had been stuck at **6** while 13 of our public repos actually carry the treaty. The badge is now **13**.

- `scripts/count_adopters.sh` now unions two sources: an **owner scan** that lists `yzhaoinuw`'s public non-fork repos via the repos API and reads `README.md`, `.copier-answers.yml`, and `AGENTS.md` directly, plus the existing **code search** for third-party adopters. Our own repos no longer depend on GitHub's code-search index.
- Output marks third-party adopters explicitly, so the index-dependent part of the number stays visible.
- Fail-safe behavior is unchanged and now covers both sources: any failure or rate limit prints an empty `ADOPTER_COUNT` and exits non-zero, so the weekly Action leaves the displayed count alone. Code-search failure stays fatal even when the owner scan succeeded — reporting owner-only results would silently drop third-party adopters and shrink the badge.

Root cause, measured rather than assumed: **7 of the 13 adopting repos are not in GitHub's code-search index at all.** Probing each with an ordinary word known to be in its own README, scoped to that repo, returned 0 hits for all 7, while indexed repos returned 8–34. The split tracks repo creation date — every missed repo was created 2026-03 or later, every found one 2025-07 or earlier — and *not* stars: `fp_analysis` and `sdreamer_flow` have 0 stars/0 forks and are indexed fine. Nothing on our side gets those repos indexed, hence reading them directly.

Note for whoever probes this next: `repo:X path:README.md` with no free-text term always returns 0 from the code-search API and is **not** a valid index-membership test. Use a real search term.

- Known wart: the badge links to the GitHub code-search results page, which still shows only the indexed subset. Badge says 13, the link shows 6. Logged in `next_steps.md`.
- Verification:
  - `bash -n scripts/count_adopters.sh` -> syntax OK.
  - `./scripts/count_adopters.sh` -> 13 adopters, `ADOPTER_COUNT=13`, exit 0, ~16s. List matches an independent per-repo content check of all 32 public repos.
  - Forced owner-scan failure (nonexistent owner) -> `ADOPTER_COUNT=` and exit 1, i.e. badge left unchanged.
  - Workflow's badge rewrite replayed against a README copy -> `adopters-13-6d81f1`.
  - `python -m unittest discover -s tests -v` -> all pass.
  - `treaty validate .` -> passes. `git diff --check` -> clean.
