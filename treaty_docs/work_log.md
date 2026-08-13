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

## 2026-08-13

### README prompt/shell disambiguation, and the migration lesson from `docs_dir` (claude-opus-5)

- **Maintainer read the README cold and could not tell that the blockquoted lines are things you type to an agent.** Lead-ins like "Hand this to your agent" and "One prompt fills them" implied it without ever saying it, and the surrounding `bash` blocks trained the eye to read every set-off block as a shell command. Fixed by naming it four times rather than once: an explicit `**Prompt — type this into your agent's chat:**` label above each of the four prompts (install, set up, migrate existing docs, update), plus a "How to read this README" paragraph in the intro that says these are not shell commands and that nothing needs installing before the first one. Repetition over elegance was the deliberate call — a reader who lands mid-page from the Contents list never sees a one-time convention note.
- **"The Workflow In Practice" was reading as instructions for the user.** It is a description of what the agent does unprompted, but its imperative numbered steps ("Read `AGENTS.md` first") are indistinguishable from a user checklist. Rewrote the steps in third person about the agent and opened the section by saying outright that it is not a checklist for the reader. Kept the section rather than cutting it: knowing the expected shape of a session is how an adopter notices when one skips the work-log step.
- Moved `Why "Treaty"` above `Badge` — the badge is cosmetic and was sitting between two sections that explain the product.
- **Recorded the `docs_dir` retrospective as an `AGENTS.md` reminder**, prompted by the maintainer asking why that work took a full day. The two mechanical lessons were already there (never move a template file; the flat rendering is frozen); what was missing is the process one: price a path/layout change as a migration *before* writing it, over three questions — what Copier sees on the next update, what the adopter must run and in what order, and what silently stops matching afterward. Both v0.8.0→v0.9.0 costs trace to skipping it: the flat-rendering freeze was found by conflict sweep rather than reasoning, and the four-step manual relocation guide shipped in v0.8.0 had to be replaced by `treaty relocate` a day later. Distilled to: **a migration we can only describe as a manual procedure is a command we have not written yet.**
- Docs only — no template, CLI, or `copier.yml` change, so no adopter-facing behavior moves and the flat-rendering guard is untouched.
- Verification:
  - `python -m unittest discover -s tests` with `TREATY_SKIP_INTEGRATION=1` — 96 tests, OK (16 skipped).
  - `treaty validate .` — passed. `git diff --check` — clean.
  - Confirmed the four prompt labels render at the four intended sites and the new heading order is Workflow → Why "Treaty" → Badge → Contributing, with the Contents list reordered to match; grepped first for other references to the moved anchors (`#badge`, `#why-treaty`) — the Contents list was the only one.

### Released v0.9.0 (claude-opus-5)

- Ships `treaty relocate` and the `treaty-doc-gitignored` validation check.
- **Minor, not the patch originally asked for.** Two reasons: it matches this repo's own precedent (v0.5.0 added `treaty diff`, v0.6.0 added `treaty --version`, both minor), and the new validation code changes existing behaviour — an adopter with a deny-all `.gitignore` who relocates will newly fail `treaty validate`, which can break a CI job. A patch bump would deliver that unannounced. Maintainer chose v0.9.0 when the trade-off was put to them.
- Nothing else outstanding on `relocate`: Windows-verified by Codex (GPT-5) across all seven checks in issue #21, with the one finding (case-only target reporting four spurious collisions) fixed before release.
- Verification:
  - `python -m unittest discover -s tests` — 96 tests, OK (1 skipped), on the release commit.
  - `treaty --help`, `treaty --version` (reports 0.9.0), `treaty relocate --help`, `treaty validate .`, import smoke, `git diff --check` — clean.
  - `python -m build` in a throwaway venv: both artifacts produced at 0.9.0.
  - Version consistency across `pyproject.toml`, `src/agent_collab_treaty/__init__.py`, `CITATION.cff` (`version:` and `date-released: 2026-08-13`).
  - Post-push ref verification, release-workflow outcome, and a clean-venv install from PyPI.
