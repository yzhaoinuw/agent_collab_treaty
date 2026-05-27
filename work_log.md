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
