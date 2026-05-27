# Next Steps

Use this checklist alongside `work_log.md`.

## Currently Hot

Active threads — read these first to know what work is in flight:

- **`treaty validate`** — lint work_log entries against the documented format and rotation policy. See [`treaty validate`](#treaty-validate-claude-opus-4-7).

When an agent (or human) creates or significantly updates a thread/plan here, include model + version, effort/thinking mode, and token budget (if known) in parentheses after the thread name or at the end of the status line, using the same compact convention as `work_log.md`.

Other sections below are background or paused; treat them as reference unless a new request reopens them.

## `treaty validate` (claude-opus-4-7)

Status: proposed

The treaty defines a strict format (rotation policy, model+effort parenthetical, `Verification:` sub-section). Without a linter, drift is inevitable, especially across multiple agents.

A `treaty validate` command would catch:

- `work_log.md` entries missing the model+effort parenthetical
- `work_log.md` over 5 unique dates (rotation needed)
- Entry shape violations (e.g., free-floating "verified with…" lines instead of the documented `Verification:` sub-section — exactly the bug review fixes for PR #1 caught manually)
- `next_steps.md` "Currently Hot" pointer drifting from the actual thread sections (broken anchor links)

Proposed plan:

- Add `treaty validate [path]` subcommand to the CLI. Default path: current directory.
- Walk the standard treaty files and report issues with file:line locations.
- Provide `--fix` for the mechanically-correctable subset (e.g., bulk-add `(model, effort)` placeholders to legacy entries; rotate work_log when it goes over 5 dates).

Remaining work:

- Decide the validation depth — strict (exit non-zero, fail CI) vs. advisory (warning-only, always exit 0). Probably strict by default with `--warn-only` opt-out.
- Decide how strict the entry-shape check should be. Markdown is forgiving; over-validation creates friction.

## Background / Paused

Sections below this line are older threads kept for context. They're not the current focus, but recording the state they were left in saves the next agent from re-deriving it.

_(No paused threads yet.)_
