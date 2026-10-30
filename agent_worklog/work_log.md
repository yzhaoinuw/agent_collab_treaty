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

### Wrap-up: this repo's own docs moved to `agent_worklog/`; relocate gap fixed (claude-opus-5-5, high)

- **Renamed this repo's `treaty_docs/` with `treaty relocate --to agent_worklog`, eating our own cooking.** The maintainer accepted the earlier concern: past PyPI READMEs link to `main/treaty_docs/...` and now 404. Only the current PyPI page is normally seen. The release-notes filter (`OWN_DOCS`) now matches both names, because notes for older tags are rebuilt too.
- **Gap found by dogfooding:** relocate rewrote file paths (`treaty_docs/work_log.md`) but not the bare folder (`[treaty_docs/](treaty_docs/)`, or `|- treaty_docs/` in a diagram), and didn't even report them, because they sat in treaty-owned root docs. The template's own `project_overview.md` structure map draws `{{ docs_dir }}/`, so every adopter doing the folder-to-folder rename v0.11.0 recommends would keep a stale folder name. Fixed for folder-to-folder moves: bare mentions are rewritten in `AGENTS.md`/`project_overview.md` and reported in other files. A path that continues past the slash (`treaty_docs/fig.png`) is left alone, since the adopter's own files don't move. Flat moves are untouched (nothing to name). `sleep_scoring` didn't hit this: its customized docs had no bare mentions, and Codex fixed the paper by hand. This is unreleased.
- **This repo's folder README is hand-written, not the template text:** the repo has no `treaty_conventions.md` (its `AGENTS.md` carries the conventions), so the template's link to it would be broken. Root-vs-template boundary.
- Open issues: only #19, still on hold.
- Verification:
  - `treaty relocate --to agent_worklog --dry-run`, then applied; `python -m unittest discover -s tests` (full suite, see below); `treaty validate .`; `git diff --check`

### v0.11.0 field result: Codex relocated `sleep_scoring` (claude-opus-5-5, high)

- **The first real v0.11.0 run, as the maintainer intended:** Codex on another machine ran update plus `relocate --to agent_worklog` on `sleep_scoring` (ae41dd1, on both `main` and `dev`). Checked here from a `git archive` snapshot: pinned at `v0.11.0`, `docs_dir: agent_worklog`, every doc moved with history (`R` renames), `agent_worklog/README.md` byte-identical to `folder_readme_text('agent_worklog')`, no `treaty_docs` references left outside the logs, no conflict markers, `treaty validate` passes. The paper's disclosure line now reads `agent_worklog/`. The README's three sleep_scoring showcase links return 200, so the 404 window from the v0.11.0 README is closed.
- **Found, older than the migration:** overlapping archive chunks in `sleep_scoring`, from b554dd5 and 5ba8193; details are in next_steps. This one is the maintainer's to fix, and validate doesn't detect it yet.
- Verification:
  - `treaty validate .` on the ae41dd1 snapshot; README byte comparison; `grep` for leftover `treaty_docs` and conflict markers; `curl` status for the three README links

### README pitch repositioned after v0.11.0 (claude-opus-5-5, high)

- **Decision:** the opening pitch now names three jobs, adding **AI-use disclosure** to handoff and the project record, and answers "doesn't my agent already have memory?". The maintainer raised both. Disclosure is a benefit built-in agent memory can't offer: the log is written during the work, so a maintainer cites it instead of reconstructing it, as sleep_scoring's JOSS manuscript does.
- **Positioning against built-in memory: complementary, not competing.** Memory is per tool and per account and hard to review. The treaty is in the repo, shared by every agent and collaborator, and versioned. Memory holds facts about the user; the log holds the project's decisions.
- **Wording kept deliberately modest:** "a record kept as the work happens", not "complete proof". Logs skip casual Q&A and cover only sessions after adoption, and sleep_scoring's own disclosure says its 2023–2025 model versions weren't recorded. "Update" and "validate" stay out of the pitch and are covered further down.
- The disclosure bullet links the sleep_scoring repo, not the paper. Codex is relocating sleep_scoring and handling the paper on another machine; once that's done, the maintainer wants Claude to check it and swap in a paper link if one is public.
- Verification:
  - `treaty validate .`; `git diff --check`

### Docs folder renamed to `agent_worklog/`, with a README; update check at each rotation (claude-opus-5-5, high)

- **Why rename:** the maintainer noticed that a reader with no context, such as a JOSS reviewer following `sleep_scoring`'s AI disclosure, can't tell what `treaty_docs/` holds. Names considered: `agent_docs/` (describes the folder but not what humans go there for, the log), `ai_worklog/` (clearest to outsiders, but loses the visual pairing with `AGENTS.md`), `agent_log(s)/` (reads as an agent's runtime traces, and plural `logs/` collides with common `.gitignore` rules). The maintainer chose **`agent_worklog/`**. The conventions file living in a "worklog" folder was judged fine: humans come for the log, and agents follow the conventions.
- **Only the default changes.** Existing folder adopters keep `treaty_docs/` because Copier reuses the recorded answer, and `treaty relocate --to agent_worklog` already handles folder-to-folder renames. This repo's own folder stays `treaty_docs/` for now: the PyPI READMEs of past releases link into it on `main`.
- **Folder README** (`{{ docs_dir }}/{% if docs_dir not in ['.', ''] %}README.md{% endif %}.jinja`): it renders only for folder layouts, because in the flat layout the name belongs to the adopter's own README, and the flat path-freeze test stays green. Measured in a scratch template tagged v0.99.0 over v0.10.3 adopters: `treaty_docs` gets it as a new file, flat gets nothing, and `docs_dir: docs` with an existing `docs/README.md` gets a **visible whole-file conflict** (UU, both sides kept), not a silent overwrite. `_conflict_notes` now says which side is theirs. `_skip_if_exists` was rejected: it would freeze the README's text after the first install.
- **Relocate carries the README:** it moves it folder to folder, writes it when leaving the root, deletes it when flattening if unedited, and reports and leaves an edited one. The package doesn't ship `template/`, so the text is duplicated in `relocate._FOLDER_README_TEXT`. The relocate-vs-fresh-install test now covers all four directions and catches any drift.
- **Update reminder:** the maintainer asked for a check at each rotation, which happens about every five dates. It goes in conventions (free to change), the archive README, and the `work-log-rotation-needed` message. The `work_log.md` template is frozen (2026-10-22), so its intro is not touched. The agent runs `treaty update --dry-run`, which works on a dirty tree, and *reports* a newer version without applying it, because conventions keep updating the maintainer's call. This is the cheap version of the parked "automated update notifications" thread. The dry run on `sleep_scoring` showed `v0.9.0 -> v0.10.3`, exactly the drift it targets.
- **Released as v0.11.0 (2026-10-29)** on the maintainer's go, together with a README pass that fixed the sleep_scoring example links (404 since sleep_scoring moved to `treaty_docs/`; now pointed at `agent_worklog/`, ahead of its relocation), dropped stale entry counts, and replaced `git add -A` in the update example. Then `dev` was fast-forwarded into `main` and the tag pushed.
- Verification:
  - `python -m unittest discover -s tests` — 167 tests OK (1 skipped), including real Copier renders of the folder README, link resolution, and relocate-vs-fresh-install for `.`→`agent_worklog`, `.`→`docs/agents`, `agent_worklog`→`docs/agents`, and `docs/agents`→`.`
  - `treaty init proj --source . --ref HEAD --defaults` in a scratch dir: `agent_worklog/README.md` rendered with `../AGENTS.md` links; `treaty validate` passed
  - `treaty update --dry-run` in `sleep_scoring` to confirm the `Template version:` line the reminder points at
  - scratch Copier update experiment described above; `treaty validate .`; `git diff --check`

### Release notes skip commits that only touch `treaty_docs/` (claude-opus-5-5, medium)

- The v0.10.3 notes listed "Record #34's field confirmation in the treaty docs" as a change with no bullets. A commit that only edits this repo's own treaty docs changes nothing a user installs, so `scripts/release_notes.py` now skips it, alongside release bumps and `[bot]` commits. The check is on files changed, not the subject line, so a code commit that also updates the log still shows.
- Backfilled with the new script: v0.10.3 and v0.9.1, which had "Re-anchor Currently Hot on what is actually in flight". The other v0.9.x/v0.10.x releases were unchanged. The workflow runs the script as of the tag being released, so the skip applies automatically from the next tag.
- Verification:
  - `python -m unittest discover -s tests` — full suite OK, including a test against v0.10.3
  - entry counts compared between every published release body since v0.9.1 and the new script's output
  - `treaty validate .`; `git diff --check`

### #22 field result, untracked files in relocate's hint, a flat-layout pointer in `treaty update`; released v0.10.3 (claude-opus-5-5, high)

- **#22 on a real adopter (Codex, `ai_crash_course`, Windows, v0.10.2, committed as 521f84e there):** `relocate --force` straight after the update matched the new help text. Relocate staged its own rewrites and named the work log, edited beforehand, as a leftover, with no `git add -A`. 22.3 (line numbers) wasn't exercised: the repo has no outside references. It's unit-tested, which is enough to close #22.
- **Gap the run found:** an archive chunk from a rotation not yet committed moved with its folder, but the hint skipped it, because the hint listed only tracked files (`git diff --name-only`). It now also names untracked files under the paths relocate moved. Other untracked files stay out on purpose: they may be data hidden with `.git/info/exclude`, the #22 workflow that removed `git add -A`.
- **Flat-layout pointer (maintainer's call, option 1 of three):** `treaty update` and `--dry-run` end with one line on a project whose recorded `docs_dir` is `.`: staying flat is fine, and `treaty relocate` moves the docs. It fires only on an explicit `.`. A missing answer means a template without the question, not a flat project. Rejected: `treaty update --relocate` (worth it only if most of the 13 flat repos are moving) and auto-moving (a move can break references in the adopter's own files that relocate only reports).
- Verification:
  - `python -m unittest discover -s tests` — full suite OK, including a CLI update of a real v0.7.0-era adopter asserting the pointer appears and nothing moves
  - relocate CLI test with an untracked archive chunk (named) and an untracked `data.csv` (not named)
  - `treaty validate .`; `git diff --check`
- **Released as v0.10.3** (2026-10-29), bundling this with #35's conventions prefix fix. `main` was an ancestor of `dev` (no bot commits since v0.10.2), so it fast-forwarded. Patch bump: a template path fix, one new CLI hint, one hint fix.

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
