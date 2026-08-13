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

### `treaty update --data` for questions new in the target version — issues #23/#17 (claude-opus-5)

- **The friction it removes**, reported from a v0.3.3 → v0.9.0 jump where six questions were new: the only two routes were `--interactive` (re-prompts *every* question through a TUI, awkward from an agent session and easy to fat-finger) or hand-editing `.copier-answers.yml` — whose own first line says not to — which then needs its own commit because Copier refuses a dirty tree. Three steps and a permanent junk commit, to answer two questions.
- **Named `--data`, not `--set` as the issue proposed**, to match the flag `treaty init` already has. Same `_parse_data` parser, same `key=value` repeatable shape, plumbed into the `data=` argument both update paths already passed for the legacy layout pin. `--dry-run` takes it too, so a preview reflects the answers you intend rather than the recorded ones.
- **`--data docs_dir=…` is refused, and this is the load-bearing decision.** Copier applies a layout change as delete-plus-create — no merge, no conflict, no warning. Exposing `data=` without this guard would have handed adopters a one-flag route to exactly the destruction `docs_dir` and `treaty relocate` were built to prevent; the flag that makes the tool scriptable would have made the dangerous thing scriptable too. It exits 1 before writing anything and names `treaty relocate --to <folder>`. **Generalizable: when you expose an internal knob, check what it now reaches that the surrounding design deliberately fenced off.**
- **Also closes #17**, which had carried `--ask-new`/`--set` as "partly mitigated, not implemented" since v0.7.0. #23 rediscovered it independently from an adopter seat, which is what made the case.
- Pinned the *old* behavior in a test as well (`test_a_new_question_silently_takes_its_default_without_data`) — the default-taking is intended, not a bug, and it should not drift unnoticed now that there is a way around it.
- Verification:
  - `python -m unittest discover -s tests` — 112 tests, OK (1 skipped). Five new: answering a genuinely new question end-to-end across two real template versions, the no-`--data` control, dry-run previewing without writing, and the `docs_dir` refusal on both the real and dry-run paths.
  - CLI smoke on a scratch project: refusal message and exit 1, `--data nope` rejected by the parser, help text renders.

### `treaty relocate` now retargets project links inside the moved docs — issue #24 (claude-opus-5)

- **The bug, from a real Windows adopter (`sleep_scoring`):** a link like `[media/README.md](media/README.md)` in a flat `next_steps.md` kept its text when the file moved into `treaty_docs/`, so it silently resolved to `treaty_docs/media/README.md`. Both the dry run and `treaty validate` stayed quiet. `_plan_link_edits` only ever retargeted *treaty* doc names, and `_plan_external_refs` only looked at the other direction — files pointing **into** the treaty docs. Links pointing **out** of a moving doc at the project's own content were nobody's job.
- **Both link directions are now covered, and they are deliberately handled differently:** outbound links are *rewritten* (the treaty owns the file that moved, so it owns the breakage); inbound references from files the treaty does not own stay *reported but untouched*. That asymmetry is the design, not an inconsistency — see the README.
- **What is deliberately left alone**, because a move cannot invalidate it: URLs, bare anchors, absolute paths, targets that escape the repo, and targets that do not resolve. That last one matters — an already-broken or historical link is not ours to guess at, and rewriting it would turn a visible mistake into a plausible-looking wrong one. Percent-encoded paths are skipped too rather than decoded-and-re-encoded.
- **Links to treaty-owned targets are skipped on purpose.** Docs that move in lockstep keep their relative path (`work_log_archive/README.md` → `../work_log.md`), and root-doc links are the existing `_retarget` pass's job. Two passes rewriting one link would compound; the skip set is what keeps them from colliding.
- **The mutation test caught a weak test of my own.** With the fix disabled, 4 of 5 new tests failed but `test_round_trip_restores_the_original_outbound_link` still passed: if nothing is ever rewritten, a round trip is trivially equal. It now asserts the halfway state as well, and all 5 fail without the fix. **A round-trip test that does not pin the midpoint proves nothing.**
- Verification:
  - `python -m unittest discover -s tests` — 107 tests, OK (1 skipped). Six new tests covering the issue's own acceptance list: depth gained on the way in, multi-segment depth, anchors preserved, round trip, links left alone, and the dry run reporting before applying.
  - **Mutation-tested**: monkeypatched `_rewrite_outbound` to the pre-fix behavior and confirmed all 5 outbound tests fail.
  - End-to-end through the CLI on a scratch `treaty init` project reproducing the issue verbatim: `[`media/README.md`](media/README.md)` → `[`media/README.md`](../media/README.md)`, target resolves on disk, link *text* untouched, sibling URL untouched, dry run named the file and count first.

### Settled the flat-rendering freeze: paths frozen, content free (claude-opus-5)

- **The freeze was over-broad, and the evidence says so.** `test_flat_layout_is_byte_identical_to_v070` compared the entire rendered flat tree byte-for-byte against `v0.7.0`, which froze every word of prose in the template. It was blocking three separate improvements (#19, #23.2, #23.3a) and had already redirected the answers-file documentation earlier the same day.
- **Measured what a content change actually costs**, with five real Copier updates against v0.7.0 flat adopters carrying real work-log history (probe kept at `tests/test_docs_dir.py`): adopter left conventions alone → **0 conflicts**; edited a *different* section → **0 conflicts**, both sides survived; edited the *same* section → 1 conflict; the #23.2 `work_log.md` fix on a live log → **0 conflicts**; same fix where the adopter had hand-deleted the paragraph → 1 conflict. **No scenario lost adopter content.** The worst case is one visible, resolvable conflict confined to a region the adopter had edited.
- **The old test's own docstring justified only the path half** — "Copier implements a template-side file move as delete-plus-create… the failure mode that silently destroys an adopter's work log." That argument is about *paths*. The content assertion was bundled in with it and guards a different, far milder failure mode. Best read: the content freeze was a release-scoped proof for v0.8.0/v0.9.0 ("the nested-layout release changes nothing for you") that got mistaken for a permanent law.
- **Corrected a claim I made earlier the same day.** I had said `treaty_conventions.md` was the *wrong* place for the answers-file note because of the freeze. It is the *safest* file in the template to change: adopters are told not to edit it, #23 confirms it sits at zero drift, and when local equals the merge base upstream prose applies cleanly every time. The risk ordering was backwards — the expensive files are the ones adopters edit heavily. The note now lives in the conventions "Updating The Treaty" section, where it belonged.
- **Three-tier policy now in `AGENTS.md`:** paths frozen permanently with no escape hatch; `treaty_conventions.md` content free; content of adopter-edited docs allowed but priced and justified in the log.
- **Replaced the proxy with behavioral tests.** `test_flat_layout_paths_are_frozen` keeps the path-set diff against `v0.7.0`; `FlatConventionsMergeTests` and `FlatWorkLogMergeTests` assert the property the content half was reaching for — adopter content always survives, and a conflict appears only where the adopter edited the same region. **Generalizable: when a behavioral test can tell you what a change costs, don't keep a proxy that forbids it.**
- Also caught a false positive worth not repeating: a plain `'<<<<<<<' in text` check reports a conflict in *every* rendering, because `treaty_conventions.md` documents conflict markers in its own prose. Marker detection has to be line-anchored (`^<{7} `).
- Verification:
  - `python -m unittest discover -s tests` — 101 tests, OK (1 skipped: case-collision, unsupported filesystem). Was 96 before; the 5 new ones are the merge scenarios.
  - **Mutation-tested the replacement path freeze** rather than trusting a green run: `git mv`'d `next_steps.md` → `roadmap.md` in a throwaway template clone and confirmed the path-set diff catches it (`missing from mutated: {'next_steps.md'}`). It is not a weaker guard than what it replaced.
  - Confirmed the live conventions edit merges clean for a v0.7.0 flat adopter who left the file alone.
  - `treaty validate .`, CLI/import smoke, `git diff --check` — all clean.

### Documented why `.copier-answers.yml` stays at the repo root (claude-opus-5)

- **Prompted by a real adopter-side question** while agents were updating repos to v0.9.0: after the working docs move into `treaty_docs/`, why is `.copier-answers.yml` still at the root? Nothing in the README, the prompt help, or the post-copy message answered it, and the tree diagram under *Where the docs live* did not even show the file. Fixed in four places: README (tree + a paragraph), `docs_dir` prompt help, `_message_after_copy` step 2, and `project_overview.md`.
- **The reason worth not re-deriving: it is a chicken-and-egg constraint, not a convention.** The answers file is what *records* `docs_dir`, so it cannot live inside the folder it names — you would have to know `docs_dir` to find the file that tells you `docs_dir`. Everything reads it from the destination root (`validation.py`, `relocate.py`, `cli.py`, and Copier itself). Added this to the root `AGENTS.md` reminder that previously only said "don't remove or rename it", because the gap that reminder leaves open is a future agent tidying it into `template/{{ docs_dir }}/` — which Copier would apply as delete-plus-create and silently break every adopter's update path.
- **Deliberately did not touch `template/treaty_conventions.md.jinja`**, which is where update mechanics normally belong. The flat rendering is frozen against `v0.7.0`, so prose there fails `test_flat_layout_is_byte_identical_to_v070` and lands a conflict in every adopter pinned to `docs_dir: '.'` — 16 of 17 as of today's survey. Worth stating plainly for the next agent: **while the freeze holds, adopter-facing documentation lands in the README, the Copier prompts, and the post-copy message, not in the shipped docs.** That is a real constraint on how the treaty documents itself, and it is the first time it has redirected a change rather than merely blocking one.
- `treaty relocate`'s plan line now reads `Answers: docs_dir -> X (edited in place; .copier-answers.yml stays at the repo root)`, since a relocation preview listing every other doc as a move is exactly where "did it forget this one?" occurs.
- Verification:
  - `python -m unittest discover -s tests -v` — 96 tests, OK (1 skipped: case-collision, unsupported filesystem). Includes the full integration suite and the flat-rendering freeze test, which passes because prompt help and `_message_after_copy` are not part of the rendered tree.
  - `treaty --help`, `treaty --version` (0.9.0), `treaty validate .`, import smoke — all pass. `git diff --check` clean.
  - Rendered a scratch project at `docs_dir=treaty_docs` and confirmed `.copier-answers.yml` lands at the root with the working docs in the folder.

### Wired up the Zenodo DOI (claude-opus-5)

- **Recorded the concept DOI `10.5281/zenodo.21746757`** in `CITATION.cff` under `identifiers:`, added a matching README badge, and pointed the Contributing section's citation line at it. Closes the Zenodo follow-up that had been open since 2026-08-01.
- **Concept DOI, not the version DOI — this is the whole decision.** Zenodo mints both: `10.5281/zenodo.21912341` is v0.9.0 specifically, and `10.5281/zenodo.21746757` resolves to whatever the latest archived release is. The concept DOI is what belongs in citation metadata, because a version DOI would freeze every future citation on v0.9.0. Added an explicit warning to the release checklist in `AGENTS.md`, since the checklist already says to bump `version:`/`date-released:` in `CITATION.cff` each release and the next agent to read it could reasonably assume the DOI wants bumping too. It does not.
- **How the DOI was found, worth not re-deriving:** Zenodo's public search API returns nothing for this record under any query tried (`agent_collab_treaty`, quoted, `title:`, `yzhaoinuw`). The reliable path is the GitHub-integration redirect — `curl -sI https://zenodo.org/badge/latestdoi/<github_repo_id>` returns a 302 whose `location` is the newest version DOI, and `GET https://zenodo.org/api/records/<id>` then gives `conceptdoi` directly. Repo id comes from `gh api repos/<owner>/<repo> --jq .id`.
- **Confirmed the archive is working as designed:** three versions archived — v0.7.0 (2026-08-01), v0.8.0, and v0.9.0 — so `next_steps.md` was right that v0.7.0 would be the first. The record reads `CITATION.cff` correctly: title "Agent Collab Treaty" rather than the default `owner/repo: tag`, ORCID attached, MIT license.
- Chose a shields.io `flat-square` badge over the official Zenodo one so the three README badges read as one system. The official badge is a one-line swap if the more recognisable scholarly styling is preferred.
- **Laid the three badges out flat** (treaty, DOI, adopters) on the maintainer's request. They were stacking because a `<!-- comment -->` alone on a line is an HTML *block*, which split the badges into three separate paragraphs; moving the `adopters-badge` comments inline collapses them into one. Verified through GitHub's own renderer (`gh api /markdown`), which returns all three `<img>`s inside a single `<p>` in the intended order.
- **The `<!-- adopters-badge:start/end -->` markers are decorative — nothing reads them.** `update-adopters-badge.yml` rewrites the count with `sed -E "s/adopters-[0-9]+-6d81f1/…/"`, matching the color string, not the markers. Worth knowing before anyone "fixes" the markers or relies on them. The DOI badge deliberately reuses the same `6d81f1`, so that regex was the one real risk in this change: simulated the workflow's `sed` against the new line and it updated only the adopters count, leaving `…zenodo.21746757-6d81f1` untouched.
- Verification:
  - `python -c "import yaml; yaml.safe_load(open('CITATION.cff'))"` — parses; `identifiers[0]` is the concept DOI.
  - Both DOIs resolved through `doi.org` (302 → the Zenodo record) and the badge image URL fetched 200.
  - `treaty validate .` — passed. `git diff --check` — clean.

### Issue triage and a `next_steps.md` accuracy pass (claude-opus-5)

- **Closed #21** (Windows verification for `treaty relocate`). All seven checks passed, the one finding shipped in v0.9.0, and nothing was left technically outstanding. Three results from that sweep were recorded upstream rather than lost with the issue: `git check-ignore --no-index` is load-bearing on Windows too, the clean-tree guard does *not* false-positive under `core.autocrlf=true` (my prediction was wrong), and report-only for external references is the confirmed default.
- **Kept #15, #17, #19 open, each for a different reason.** #17's proposal (`--ask-new` / `--set`) is genuinely unimplemented — grepped `cli.py` to confirm — and `docs_dir` in v0.8.0 hit exactly that shape but was solved with a per-question pin (`_legacy_layout_data`), not a general mechanism, so the gap is unchanged. #15 is down to its parked remainder. **#19 is blocked on a decision, not on effort**: it asks whether doc-quality guidance belongs in the treaty's scope at all, and no answer has been recorded — worth noting that today's README work was an instance of exactly the defect it describes.
- **`next_steps.md` "Currently Hot" had become a release-announcement archive.** Five of its twelve bullets were shipped releases with nothing in flight, one still said "`dev → main` merge pending" for v0.7.0, and one described the next step in a thread that shipped as v0.9.0. Collapsed all five into a single "shipped, nothing outstanding" line pointing at `work_log.md`, and moved the adopters-badge history to the Background section. The section is meant to answer "what is in flight," and a reader could no longer tell that from it.
- **Surveyed adopter pins directly via the GitHub API**, because the existing tally ("nine of eleven … five remain," dated 2026-08-01) was stale enough to mislead. Actual state: 17 Copier-managed `yzhaoinuw/*` repos, one on v0.9.0, the rest spread from v0.7.0 down to v0.2.0, with 13 pinned below v0.6.0. Recorded the breakdown rather than a summary number, since the summary is what went stale last time.
- **Ruled out a false alarm worth not re-deriving:** the badge reads 14 while the survey found 17 adopters. The gap is exactly the 3 private repos — the badge counts public ones, so it is correct. Checked before flagging it as a counter bug.
- Verification:
  - `treaty validate .` — passed (its "Currently Hot" link check covers the edited section). `git diff --check` — clean.
  - Issue state confirmed with `gh issue list` after closing: #22, #19, #17, #15 open.
  - Pin survey run against the live API across all `yzhaoinuw/*` repos, reading `_commit` from each `.copier-answers.yml`; public/private status cross-checked with `gh repo list`.

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
