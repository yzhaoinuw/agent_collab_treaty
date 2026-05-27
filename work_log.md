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

Model / effort / token info goes in the parentheses after the `###` title when available from the system. Use whatever the model or interface actually reports (do not hallucinate). Purely human-driven work can use `(human)`. Mixed human + agent sessions can combine them, e.g. `(human + grok-4.3, high)`.

Keep the parenthetical compact. Examples:
- `(grok-4.3, high, ~18k tok)`
- `(gpt-4o, high, ~22k tok)`
- `(claude-3.7-sonnet, extended)`
- `(grok-4.3, low)`

Newest entry goes on top. If the session did multiple distinct pieces of work, use multiple `###` subsections under one `##` date header.
-->

## 2026-05-27

### Add model + effort metadata convention to work log entries and plan threads (grok-4.3, high)

- Updated the entry shape comment block in `work_log.md` to document the compact parenthetical `(model + version, effort/thinking mode, token budget if known)` after each `###` title.
- Included a GPT example (`gpt-4o`) in the guidance so GPT (an important agent on the team) is explicitly represented alongside Grok and Claude.
- Added a one-line expectation in `AGENTS.md` pre-flight checklist.
- Added matching guidance in `next_steps.md` for agent-proposed threads/plans, with an updated example thread header demonstrating the convention.
- No change to `work_log_archive/README.md` (the convention lives in the live file's comment block and travels with rotations).

- Verified with search_replace + git diff; the change is minimal, consistent, and immediately dogfooded by this entry.
