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
