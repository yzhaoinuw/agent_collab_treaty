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

## 2026-10-29

### #35: a conventions path missing its prefix, and a relocate-vs-template parity test (claude-opus-5-5, high)

- **Field result (Codex on `ai_crash_course`, Windows, v0.9.3 → v0.10.2, flat):** clean update, preview and apply agreed, and the staging hint named exactly the two changed files. A controlled check exercised #34's fix on the cases Grok hadn't (`my_repo`, `Background / Paused`) and fired `next-steps-hot-thread-paused` for the first time outside unit tests. That repo was then relocated into `treaty_docs/`, which surfaced #35.
- **#35:** the sentence added to conventions in v0.9.1 ("its design detail belongs in `project_overview.md`") was the one root-doc reference without `{{ root_prefix }}`. Relocate rewrote it correctly, so an unedited conventions file showed one modified section in `treaty diff` after a supported move. Fixed in the template.
- **The guard is a parity test, not a grep:** render flat, relocate to `treaty_docs` and to `docs/agents`, and compare against a fresh render at that layout. It fails on the old line (mutation-checked). It also found that `project_overview.md`'s starter folder diagram is drawn differently per layout, so a relocated one has a different shape. Left alone: adopters replace that diagram, and redrawing the flat one would conflict for them. The test skips only that block.
- **What the fix costs adopters, measured with real updates** from v0.10.2 to a scratch v0.10.3: a fresh `treaty_docs/` install takes the corrected line cleanly. A flat install doesn't change. A repo relocated from flat (like `ai_crash_course`) merges cleanly and then shows zero conventions drift.
- **Layout question from the maintainer:** `treaty update` never moves an old flat repo into `treaty_docs/`. This was confirmed as deliberate: Copier applies a move as delete-plus-create. 13 of 22 adopters are still flat. Options offered: a CLI hint after updating a flat repo, `treaty update --relocate`, or leave it. Not decided.
- Rotated the live log: 2026-08-13 to 2026-10-26 moved to `work_log_archive/work_log_2026-08-13_to_2026-10-26.md`.
- Verification:
  - `python -m unittest discover -s tests` — full suite OK
  - the new parity test fails with the old template line restored
  - real `treaty update` v0.10.2 → scratch v0.10.3 for nested, relocated and flat installs, then `treaty diff` on the relocated one
  - `treaty validate .`; `git diff --check`
