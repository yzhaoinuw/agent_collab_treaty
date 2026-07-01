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

## 2026-07-01

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
