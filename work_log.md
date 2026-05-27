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

## 2026-05-27

### Add treaty validate CLI and validation tests (gpt-5)

- Added `treaty validate [path]` with strict-by-default validation and a `--warn-only` advisory mode.
- Added validation checks for required treaty paths, work-log metadata and verification sections, live-log rotation, duplicate date headings, and broken `next_steps.md` Currently Hot anchors.
- Added focused `unittest` coverage for valid docs, missing work-log metadata/verification, rotation overflow, and broken hot links.
- Updated README, root agent guidance, project overview, and `next_steps.md` to document `treaty validate` and mark the validation thread complete.
- Verification:
  - `.venv\Scripts\python.exe -m unittest discover -s tests -v`
  - `.venv\Scripts\treaty.exe validate .`
  - `.venv\Scripts\treaty.exe --help`

### Add opt-in agent pointer files to treaty init (gpt-5)

- Added an `agent_pointers` Copier multiselect so `treaty init` can optionally generate tool-specific pointers while keeping the default install vendor-neutral.
- Added conditional templates for `CLAUDE.md`, `.cursor/rules/treaty.mdc`, `.windsurf/rules/treaty.md`, and `.aider.conf.yml`, all pointing back to `AGENTS.md` as the shared treaty.
- Updated README, project overview, root agent guidance, and `next_steps.md` to document the new pointer behavior and mark the pointer-file thread complete.
- Verification:
  - reviewed current official guidance for Claude Code `CLAUDE.md` imports, Cursor project rules / `AGENTS.md`, Windsurf rules / `AGENTS.md`, Aider always-read conventions, and Copier multiselect/exclude behavior
  - `.venv\Scripts\treaty.exe --help`
  - `.venv\Scripts\python.exe -c "import agent_collab_treaty, agent_collab_treaty.cli; print('import ok')"`
  - rendered `treaty init` from a temporary non-git source copy with default answers and confirmed no pointer files or empty pointer directories were emitted
  - rendered `treaty init` with all `agent_pointers` selected and confirmed `CLAUDE.md`, `.cursor/rules/treaty.mdc`, `.windsurf/rules/treaty.md`, and `.aider.conf.yml` were emitted

### Replace placeholder repo docs with treaty-specific maintainer guidance (gpt-5)

- Rewrote root `AGENTS.md` so future agents get real package/runtime guidance, including the root-vs-template boundary, local smoke-test recipes, release notes, and project-specific reminders.
- Rewrote root `project_overview.md` to describe the actual Typer/Copier package structure, active runtime path, release automation, current test gap, and open product questions.
- Verification:
  - manual read of `AGENTS.md` and `project_overview.md`
  - `git diff -- AGENTS.md project_overview.md`

### Verify PyPI release and clean active handoff queue (gpt-5)

- Confirmed the user-side PyPI/TestPyPI setup, TestPyPI dry-run, and real `v0.1.0` release are complete.
- Verified `v0.1.0` is pushed to `origin`, the GitHub Actions TestPyPI and PyPI release runs both completed successfully, the GitHub Release exists with wheel/sdist assets and publish attestations, and both PyPI registries report `agent-collab-treaty` version `0.1.0`.
- Removed the completed PyPI publish thread from `next_steps.md` so the active queue now only tracks the per-agent pointer-file and `treaty validate` follow-ups.
- Verification:
  - `git ls-remote --tags origin` — confirmed remote `v0.1.0` tag exists
  - `C:\Users\yzhao\miniconda3\python.exe` one-off registry/API probe — confirmed PyPI, TestPyPI, GitHub Actions, and GitHub Release state
  - fresh `.tmp_pypi_smoke` venv: `pip install agent-collab-treaty==0.1.0`, `treaty --help`, and `import agent_collab_treaty, agent_collab_treaty.cli` all passed

### Wire up PyPI publishing — LICENSE + release/test-publish workflows + maintainer docs (claude-opus-4-7)

- Added MIT `LICENSE` at the repo root, matching the license metadata already declared in `pyproject.toml`.
- Added `.github/workflows/release.yml`: fires on `v*` tag push, builds sdist + wheel, publishes to PyPI via PyPI Trusted Publishing (OIDC) — no API token lives in repo secrets. Also creates a GitHub Release with auto-generated notes and attached dist files.
- Added `.github/workflows/test-publish.yml`: `workflow_dispatch` (manual) trigger, publishes to TestPyPI via OIDC for dry-runs without burning a real version number. Accepts an optional `ref` input for building from a non-default branch.
- Added a new "Releasing to PyPI" section to `README.md` documenting the one-time PyPI/TestPyPI Pending Publisher setup (exact values to enter), the GitHub Environments to create, and the dry-run → tag-and-push release flow.
- Updated `next_steps.md` PyPI thread from "proposed" to "in progress — code landed, blocked on user-side PyPI setup," with the concrete remaining steps the user has to do in the PyPI web UI.
- Verification:
  - `python3 -c "import yaml; yaml.safe_load(open(...))"` on both workflows — both parse as valid YAML
  - manual read of both workflow files for correct `permissions: id-token: write` (OIDC) and `environment: name: …` (Trusted Publisher anchor)
  - cannot smoke-test the workflows locally — they only fire on GitHub Actions runners and require the PyPI Pending Publisher to be registered before the first publish

### Disentangle dogfooded root files from the shipped template; populate real next-steps threads (claude-opus-4-7)

- Clarified the architectural seam between the **shipped template** (`template/`) and the **dogfooded root files** (this repo applying the treaty to itself): the root holds real session entries and real next-steps threads, the template holds pristine placeholders.
- Fixed `README.md` Option 3 ("just copy the files") — previously pointed at the repo root, which would have leaked our dogfooded content into anyone doing a manual copy. Now points at `template/` and notes the `AGENTS.md.jinja` markers users need to fill in.
- Replaced the placeholder `next_steps.md` at the repo root with three real threads tracking the deliberately-deferred follow-ups from the MVP installer PR: Publish to PyPI, Per-agent pointer files in `treaty init`, and `treaty validate`. Each thread carries the model attribution (`claude-opus-4-7`) per the metadata convention.
- Committed and pushed directly to `main` (no PR) per the user's note that this is a single-contributor repo with Claude as the agent; the change is doc-only and the user explicitly authorized it.
- Verification:
  - `git diff` to confirm only `README.md`, `next_steps.md`, and `work_log.md` changed
  - manual read of the rendered `next_steps.md` to confirm the "Currently Hot" anchors match the section headings below

### Fix `treaty update` end-to-end: add answers-file template + overwrite flag (claude-opus-4-7)

- Added `template/.copier-answers.yml.jinja` — required by Copier to persist the recorded source + commit ref + user answers into the rendered project. Without it, `.copier-answers.yml` was never written, so `treaty update` had no anchor and would fail.
- Updated `treaty update` in `cli.py` to pass `overwrite=True` to `copier.run_update`. Without it, Copier refused with `UserMessageError: Enable overwrite to update a subproject.` The destination is already required by Copier to be a git-tracked repo (so the user can review the diff), making overwrite the right default.
- Documented the `git init` prerequisite in the `treaty update` docstring (Copier requires git in the destination for three-way merges).
- Verification (full update round-trip in /tmp scratch):
  - Cloned dev to /tmp/treaty_scratch, added answers template, committed
  - Init test project from scratch; `.copier-answers.yml` now records `_commit: 5648bc2`, `_src_path`, and all user answers
  - Made a local edit in test project (`LOCAL_EDIT_SENTINEL` in work_log.md), committed it (Copier requires git-tracked destination)
  - Modified scratch template (added `UPSTREAM_SENTINEL` section to AGENTS.md.jinja), committed → new HEAD 5857077
  - Ran `treaty update`: `UPSTREAM_SENTINEL` appeared in test project's AGENTS.md at line 153, `LOCAL_EDIT_SENTINEL` still present in work_log.md at line 44, `_commit` advanced to `5857077`

### Ship pip-installable `treaty` CLI and Copier template (claude-opus-4-7)

- Added a one-command installer so the treaty can be dropped into any project without manually copying files. After `pipx install agent-collab-treaty`, users run `treaty init` (interactive) or `treaty init --defaults --data key=value ...` (scriptable), and the files land in the current directory with their integration branch / env activation / test command pre-filled.
- Added `treaty update` to pull upstream treaty refinements back into projects that were previously initialized, without losing local edits.
- Authored a Copier template at `template/` plus `copier.yml` at the repo root, so the treaty is also usable directly via `pipx run copier copy gh:yzhaoinuw/agent_collab_treaty .` without installing our CLI.
- Updated `README.md` with three installation paths (CLI, direct Copier, manual copy) so users can pick their level of tooling.
- Verification:
  - `pip install -e .` into a fresh venv; `treaty --help` shows the `init` and `update` subcommands
  - `treaty init <tempdir> --source <repo> --defaults` rendered all 5 docs cleanly with bracket-placeholders intact for empty answers
  - `treaty init <tempdir> --source <repo> --data integration_branch=trunk --data env_activation='source .venv/bin/activate' --data test_command='npm test' --defaults` substituted all three values into `AGENTS.md` at every expected site (`git checkout trunk`, activation block, test runner / pre-flight test command lines)

### Review pass on PR #1 — apply fixes and tighten token-budget spec (claude-opus-4-7)

- Reviewed PR #1 against current repo state; applied three fixes on `dev`:
  - `next_steps.md`: updated Thread B header to also demonstrate the metadata convention (was inconsistent with Thread A).
  - `work_log.md`: replaced stale `claude-3.7-sonnet` example with current `claude-opus-4-7`.
  - `work_log.md`: restructured the dogfooded entry's trailing "verified with…" bullet to follow the documented `- Verification:` sub-section template.
- Tightened the token-budget definition in `work_log.md`: token count is now defined as **output tokens for the session** (output + thinking/reasoning tokens for models that report them separately). Field is omitted if the interface does not surface a count. Reason: the prior "use whatever the model reports" guidance produced ambiguous counts that were not comparable across agents.
- Promoted the per-field guidance into an explicit bulleted definition so the convention is unambiguous at a glance.
- Verification:
  - `git diff` to confirm edits applied cleanly across the three files
  - manual read of the updated comment block, `AGENTS.md` line, and both example thread headers in `next_steps.md` to confirm the convention reads consistently

### Add model + effort metadata convention to work log entries and plan threads (grok-4.3, high)

- Updated the entry shape comment block in `work_log.md` to document the compact parenthetical `(model + version, effort/thinking mode, token budget if known)` after each `###` title.
- Included a GPT example (`gpt-4o`) in the guidance so GPT (an important agent on the team) is explicitly represented alongside Grok and Claude.
- Added a one-line expectation in `AGENTS.md` pre-flight checklist.
- Added matching guidance in `next_steps.md` for agent-proposed threads/plans, with an updated example thread header demonstrating the convention.
- No change to `work_log_archive/README.md` (the convention lives in the live file's comment block and travels with rotations).
- Verification:
  - `git diff` to confirm the edits applied as expected
  - manual read of the three modified files to confirm the convention reads consistently across them
