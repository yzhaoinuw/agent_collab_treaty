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

## 2026-07-06

### Fix adopters badge counting a rate-limit error as "1 adopter" (claude-opus-4-8, extended thinking)

- Diagnosed why the badge dropped to 1 while 6 repos have adopted. The 2026-07-06 scheduled `update-adopters-badge` run hit GitHub code-search **HTTP 429 secondary rate limits** (default `GITHUB_TOKEN`, shared runner IPs). `count_adopters.sh` suppressed only stderr, so the 429 JSON error body leaked onto stdout, survived the exclude filter, and — being one concatenated line — was counted as `ADOPTER_COUNT=1`. The old ">0" guard passed, so the bot wrote `adopters-1` and pushed it directly to `main` (commit `4fce2ca`). The 2026-06-29 run returned the real 6, so it is intermittent. `dev` still correctly showed 6.
- Reverted the bad bot commit via `dev`: fast-forwarded `dev` to include `4fce2ca`, then `git revert`ed it (dev now descends from `main`, so the maintainer's `dev → main` merge fast-forwards and restores `adopters-6`). Did **not** push to `main` — maintainer merges `dev → main`.
- Hardened `scripts/count_adopters.sh`: keep stdout/stderr separate, detect per-query failure, **hard-fail** (non-zero exit + empty `ADOPTER_COUNT`) on any search error or rate limit, and filter results to valid `owner/repo` lines so an error body can never be miscounted.
- Hardened `.github/workflows/update-adopters-badge.yml`: only rewrite the badge when the script exits 0 **and** the count is a positive integer. Updated the workflow header note and AGENTS.md; recommended setting an `ADOPTERS_TOKEN` PAT to reduce throttling.
- Follow-up caught by re-running the workflow on Actions: GitHub invokes `run:` steps as `bash -e {0}`, and that injected errexit aborted the step on the (intended) non-zero exit from the script before the `rc` check could turn it into a clean "leave badge unchanged." Added `set +e` at the top of the step so a throttled run finishes **green** with the badge untouched instead of a red failure. Confirmed the mechanism locally (`bash -e -c` with/without `set +e`).
- Verification:
  - `bash -n scripts/count_adopters.sh` OK; live run returns `Total adopters: 6`, exit 0.
  - Confirmed the shape filter drops the exact 429 JSON blob and the workflow guard skips empty/`0`/non-numeric counts (`UPDATE` only for positive integers).
  - Live Actions run `28838441565` (before the `set +e` fix) hit HTTP 429 and the script correctly refused to emit a count — the badge stayed at 6 (fix proven end-to-end); the step went red only due to the injected `-e`, now addressed.
  - `git diff --check` clean; `python3 -m unittest discover -s tests` → 18 tests OK (1 skipped); `treaty validate .` passed.
  - `ADOPTERS_TOKEN` (user PAT) added as a repo secret; workflow run `28839889605` authenticated with it, code search succeeded with **no 429**, returned `Total adopters: 6`, and left the badge unchanged (green). Throttling resolved end-to-end.

## 2026-07-01

### Document treaty-update conflict handling for agents (claude-opus-4-8, extended thinking)

- Reproduced that `treaty update` is a Copier three-way merge (git merge under the hood): non-overlapping local edits are preserved, but edits overlapping an upstream change leave `<<<<<<< before updating` / `>>>>>>> after updating` conflict markers and a `UU` unmerged file — on both fresh-init and existing-adoption projects. Not silent data loss (content is recoverable between markers), but easy to mistake for an overwrite. My earlier "clean" verification only appended far from template changes, so it missed this — corrected here.
- Added an **"Updating The Treaty"** section to the shipped `template/AGENTS.md.jinja` so a downstream agent asked to update the treaty has an explicit procedure: commit first (clean tree required), run `treaty update`, resolve conflict markers keeping local content, review `git diff`, don't commit unresolved markers. Framed as maintainer-initiated ("only when asked").
- Fixed the README "Update an installed treaty" section: dropped the "preserving your local edits" overclaim and added the resolve-conflicts workflow.
- Verification:
  - `git diff --check` clean; `treaty validate .` passed; Jinja render of `template/AGENTS.md.jinja` with `StrictUndefined` succeeded (no new undefined vars).

### Add "Update an installed treaty" README section (claude-opus-4-8, extended thinking)

- Added a dedicated `### Update an installed treaty` section to `README.md` (between the install options and "Validate an installed treaty"): the `treaty update` flow, that it three-way-merges from the pinned version up to the latest release while preserving local edits, `--defaults`, the git-tracked prerequisite, and the caveat that manual-copy (Option 3) adopters have no `.copier-answers.yml` and must merge by hand.
- Consolidated the previously scattered git-requirement note (it lived mid-init-flow) into this section to remove duplication.
- Verified the update path end-to-end beforehand: a scratch project pinned at `v0.3.2` ran `treaty update` → advanced to `v0.3.3` and pulled in today's Release/Tag Checklist and dated-entry rule, prior answers preserved.
- Verification:
  - `git diff --check` clean; internal anchor `#option-3---just-copy-the-files` matches its heading.

### Release v0.3.3 (claude-opus-4-8, extended thinking)

- Bumped version `0.3.2` → `0.3.3` in `pyproject.toml` and `__init__.py`. Ships today's `treaty validate` future-date check plus the release/tag-gate and dated-artifact guidance in root `AGENTS.md` and the shipped template, and the badge-adopters/tri-color changes from `c162439`. Patch release — no breaking changes.
- Reconciled the bot divergence first: `origin/main` carried two `update-adopters-badge` bot commits (`f344526`, `b31bcd4`, README badge count) that `dev` lacked. Per the maintainer's call, merged `origin/main` into `dev` (single merge commit, README-only, no conflict) rather than rebasing/force-pushing, then fast-forwarded `main` to `dev` so both branches and the tag stay co-located.
- Flow: merge + bump committed on `dev` and pushed; `main` fast-forwarded to `dev`; annotated tag `v0.3.3` created on that commit and pushed to fire `release.yml` (PyPI publish + GitHub Release).
- Verification:
  - `python -m unittest discover -s tests` → 18 OK (1 skipped); `treaty validate .` passed; `git diff --check` clean after the bump.
  - `git rev-parse main dev origin/main origin/dev` all equal after the fast-forward (no divergence).
  - Pushed tag/branch refs verified with `git ls-remote`; release workflow watched to completion.

### Machine-checked future-date gate in `treaty validate` (follow-up to issue #9) (claude-opus-4-8, extended thinking)

- Added a `work-log-future-date` check to `treaty validate`: it fails when any `## YYYY-MM-DD` work-log heading is dated after the local date. This is the one piece of the release/tag gate worth machine-enforcing — objectively checkable, zero false positives, generic across all treaty projects, no git or project config required. Decision recorded for future agents: the *release gate itself* (version / changelog / docs updated before a tag) stays prose-only guidance because it is project-specific and false-positive-prone; if hard enforcement is ever wanted, its home is a project-owned pre-push or CI check on tag push, not the generic validator.
- `validate_project(root, today=None)` now takes an injectable `today` (defaults to `date.today()`) so tests stay deterministic; threaded it through `_validate_work_log`.
- Added two tests: a future-dated entry raises `work-log-future-date`; an entry dated exactly today does not.
- Documented the new check in the dated-entry rule in both root `AGENTS.md` and `template/AGENTS.md.jinja`.
- Rotated the work log: this `2026-07-01` entry is the 6th unique date, so per the rotation policy the oldest 5 dates (`2026-05-27` → `2026-06-30`) moved as a chunk into `work_log_archive/work_log_2026-05-27_to_2026-06-30.md` — the first archive file. The live log now holds only today.
- Switched the local env to an editable install (`pip install -e .`): the site-packages copy was non-editable (0.3.1), so `src/` edits were not importable and the first test run failed with `unexpected keyword argument 'today'`. `import agent_collab_treaty` now resolves to `src/` and reports 0.3.2.
- Verification:
  - `date +%F` -> `2026-07-01` (local, EDT) — verified before dating this entry (UTC had already rolled to 2026-07-01 the previous session, which is exactly the trap the new check guards).
  - `python -m unittest discover -s tests` -> 18 tests OK (1 skipped: case-only duplicate paths unsupported on APFS); includes the 2 new future-date tests.
  - `treaty validate .` -> "Treaty validation passed." (post-rotation: 1 live date, not future).
  - `git diff --check` -> clean.
