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

## 2026-08-01

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
