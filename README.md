# Agent Collab Treaty

[![Agent Collab Treaty](./assets/treaty-adopted.svg)](https://github.com/yzhaoinuw/agent_collab_treaty) [![DOI](https://img.shields.io/badge/DOI-10.5281%2Fzenodo.21746757-6d81f1?style=flat-square)](https://doi.org/10.5281/zenodo.21746757) <!-- adopters-badge:start -->[![Public adopters](https://img.shields.io/badge/adopters-16-6d81f1?style=flat-square)](https://github.com/search?q=%22yzhaoinuw%2Fagent_collab_treaty%22&type=code)<!-- adopters-badge:end -->

A drop-in documentation contract for repositories worked on by agents, humans, or both. Five Markdown files and an archive folder — two at your repo root, the rest tucked into `agent_worklog/` — doing two jobs:

- **Agent handoff.** The next session picks up where the last one left off — less repeated reading, fewer lost decisions — whether it's the same agent, a different model, or a different machine.
- **Planning and work log, for you.** The same files are a running record of what's in flight, what shipped, and what was decided and why. Plain Markdown in git: nothing to log into, diffable, and ready to lift straight into a status update.

Language- and framework-agnostic — code repos, but also prose, research, and ops. Your agent can set it up in two prompts and maintain it unsupervised from there. Battle-tested across Codex, Claude Code / Cowork, and Grok Build with near-zero friction.

**How to read this README.** The blockquoted lines below — the ones introduced by *"Prompt — type this into your agent's chat"* — are **exactly that: sentences you type or paste into your AI coding agent** (Claude Code, Codex, Cursor, Gemini CLI, whichever you use). They are not shell commands, and you do not need anything installed before sending the first one: the agent installs the CLI and runs it for you. Every prompt is paired with a collapsed *"Prefer to run it yourself?"* section holding the equivalent terminal commands, for when you'd rather drive.

## Contents

- [What's In The Template](#whats-in-the-template)
- [See It In A Real Project](#see-it-in-a-real-project)
- [Install](#install)
- [Set Up](#set-up)
- [Update](#update)
- [Validate](#validate)
- [Wiring Up Your Agent](#wiring-up-your-agent)
- [The Workflow In Practice](#the-workflow-in-practice)
- [Why "Treaty"](#why-treaty)
- [Badge](#badge)
- [Contributing](#contributing)

## What's In The Template

| File | Purpose |
|---|---|
| `AGENTS.md` | First-read contract: startup rule, doc map, runtime, common tasks, commit conventions, project reminders. **This is the file you customize.** |
| `project_overview.md` | Orientation map: active vs. legacy code, authored vs. derived files, repo structure, where to look first. |
| `agent_worklog/treaty_conventions.md` | The generic mechanics `AGENTS.md` links to: work-log criteria, rotation and dating rules, branch handoff, release gate, update procedure. **Maintained upstream — leave it alone** and `treaty update` keeps it current. |
| `agent_worklog/next_steps.md` | Active roadmap. "Currently Hot" points agents at the threads that matter now. |
| `agent_worklog/work_log.md` | Session journal, newest first. Agents prepend substantive work before handoff. |
| `agent_worklog/work_log_archive/` | Rotated older work-log chunks, so the live log stays cheap to read. |
| `agent_worklog/README.md` | Tells anyone browsing the repo — a reviewer, a new contributor — what the folder is, before they open a file. Maintained upstream. |

`AGENTS.md` and `treaty_conventions.md` split along how they're maintained — your answers in one, shared mechanics in the other. That's what keeps `treaty update` close to conflict-free.

The working docs sit in `agent_worklog/` so they don't crowd your repo root; `AGENTS.md` and `project_overview.md` stay at the root, where a newcomer and an agent both expect to find them. Set the `docs_dir` question to rename that folder, or to `.` to keep every file flat at the root. Projects installed before v0.8.0 stay flat automatically — see *Where the docs live* under [Install](#install).

## See It In A Real Project

Not samples — living docs, filled in by months of real sessions:

- **[sleep_scoring](https://github.com/yzhaoinuw/sleep_scoring)** — sleep-staging app; 39 dated entries since April 2026, rotated across 8 archive chunks: [work_log.md](https://github.com/yzhaoinuw/sleep_scoring/blob/main/work_log.md) · [next_steps.md](https://github.com/yzhaoinuw/sleep_scoring/blob/main/next_steps.md)
- **[fp_analysis](https://github.com/yzhaoinuw/fp_analysis)** — fiber-photometry app; 20 dated entries since March 2026, 21 sessions in the live log alone: [work_log.md](https://github.com/yzhaoinuw/fp_analysis/blob/main/work_log.md) · [next_steps.md](https://github.com/yzhaoinuw/fp_analysis/blob/main/next_steps.md)
- **This repo** maintains itself the same way: [work_log.md](https://github.com/yzhaoinuw/agent_collab_treaty/blob/main/treaty_docs/work_log.md) · [next_steps.md](https://github.com/yzhaoinuw/agent_collab_treaty/blob/main/treaty_docs/next_steps.md)

Open any `work_log.md` and read one entry. It says *why* something was decided, not which files changed — that's what makes it worth reading months later, by an agent or by you.

## Install

Handing the install to your agent is the intended path, and how these docs are maintained in practice.

**Prompt — type this into your agent's chat:**

> pip install agent-collab-treaty (needs Python 3.10+), then run `treaty init` in this repo.

The agent installs the CLI, runs `treaty init`, and answers its questions with you. Nothing needs to be installed on your side first.

The CLI needs **Python 3.10 or newer**. On macOS, `python3` and `pip3` are often Apple's 3.9, and its pip answers "No matching distribution found" rather than saying Python is too old. If `python3 --version` is below 3.10, install with a newer interpreter (`python3.13 -m pip install …`, or conda's `python -m pip install …`).

<details>
<summary>Prefer to run it yourself?</summary>

```bash
pipx install agent-collab-treaty     # isolated (recommended)
pip install agent-collab-treaty      # or in a regular venv

cd your-project && treaty init
```

`treaty init` asks a few short questions and writes the treaty files into the current directory.

</details>

<details>
<summary>Other ways to install the treaty</summary>

The CLI is a thin wrapper around [Copier](https://copier.readthedocs.io/), so you can skip it:

```bash
pipx run copier copy gh:yzhaoinuw/agent_collab_treaty .
```

Or copy the files by hand from [`template/`](template/) — not from this repo's root, which holds our own dogfooded docs. Replace the Jinja placeholders in `template/AGENTS.md.jinja`, rename it to `AGENTS.md`, and fill in the bracket placeholders in the other files. The literal `{{ docs_dir }}` directory in there is the docs folder awaiting its name: copy its contents into `agent_worklog/` (or straight to the root for a flat layout, leaving out its `README.md`).

Hand-copied projects have no `.copier-answers.yml`, so `treaty update` and `treaty diff` won't work on them — you'd copy new sections from [`template/`](template/) by hand instead.

</details>

## Set Up

`treaty init` leaves bracket placeholders for the project-specific parts. One more prompt fills them.

**Prompt — type this into your agent's chat:**

> Fill out the docs in the treaty.

That's the whole setup. The agent reads the repo, replaces the placeholders, and records what's in flight — the installed docs tell it the rest.

From there it's self-sustaining: sessions read `AGENTS.md` at startup, prepend to `work_log.md` before handoff, and keep `next_steps.md` honest, unprompted. The only recurring ask is the occasional [update](#update).

<details>
<summary>Prefer to run it yourself?</summary>

Fill in the bracket placeholders in `AGENTS.md` (runtime, common tasks, project reminders) and `project_overview.md` (entrypoints, active vs. legacy, authored vs. derived), then put whatever is in flight into `next_steps.md` and run `treaty validate .`.

Leave `work_log.md` empty — it starts accumulating from the next session. Backfilling it from git history produces exactly the "implemented function X" noise the log exists to avoid.

Non-interactive install, if you're scripting adoption:

```bash
treaty init . --defaults \
  --data integration_branch=main \
  --data env_activation='conda activate myenv' \
  --data verification_command='pytest -v -m "not slow"' \
  --data has_releases=false \
  --data 'agent_pointers=["claude-code", "cursor"]'
```

</details>

<details>
<summary>The questions it asks</summary>

Three questions drop sections that don't apply to your project. All default to yes, so code repos see no change:

| Question | Answering no drops |
|---|---|
| `has_releases` | The "Release / Tag Checklist" section (and the release gate in `treaty_conventions.md`) |
| `uses_precommit` | The "Pre-commit Note" section |
| `include_git_ownership_note` | The "Git Ownership Note" section |

Opting out beats deleting: a section that never rendered can never conflict, while a section you deleted collects a conflict every time upstream revises it.

Three more worth knowing:

- **`docs_dir`** is the folder the working docs live in, `agent_worklog` by default (`treaty_docs` before v0.11.0). Answer `.` to keep everything flat at the repo root. See *Where the docs live* below.
- **`env_activation`** accepts `none` for projects that deliberately have no managed environment. `AGENTS.md` then says so explicitly, instead of leaving an agent to helpfully create a venv.
- **`verification_command`** is whatever proves the repo is in good shape — `pytest`, `npm test`, a link checker, a lint pass, or `treaty validate .`. It replaced `test_command` in v0.5.0; older projects carry their recorded answer over automatically.

</details>

<details>
<summary>Where the docs live</summary>

New installs put the working docs in `agent_worklog/`, leaving `AGENTS.md` and `project_overview.md` at the repo root:

```text
your_repo/
|- .copier-answers.yml
|- AGENTS.md
|- project_overview.md
|- agent_worklog/
|  |- README.md
|  |- treaty_conventions.md
|  |- next_steps.md
|  |- work_log.md
|  |- work_log_archive/
```

The folder was `treaty_docs/` from v0.8.0 to v0.10.x. It was renamed because a reviewer or newcomer browsing a repo could not tell what a folder named after the tool held. Projects installed then keep `treaty_docs/`: the name is recorded in `.copier-answers.yml`, and `treaty update` never moves files. They get the folder README on their next update. To take the new name, run `treaty relocate --to agent_worklog`.

The folder README is only rendered for folder layouts. In the flat layout that filename is your project's own README. If you already kept a `README.md` in your docs folder, the update shows it as a conflict: your version against the treaty's. Keep yours.

`AGENTS.md` has to stay at the root: agents resolve the *nearest* `AGENTS.md` up the directory tree, so one nested inside `agent_worklog/` would apply only to files inside that folder — the opposite of what you want. `project_overview.md` stays with it as the human-facing entry point.

**`.copier-answers.yml` stays at the root too, at every `docs_dir` value** — including after `treaty relocate` moves the working docs. It is Copier's bookkeeping, not a treaty doc: it records your answers and the template version you are pinned to, and `treaty update` / `treaty diff` read it from the repo root. It is also the file that records `docs_dir` itself, so it cannot live inside the folder it names. Commit it; a gitignored answers file breaks every later update, which is why `treaty init` warns about one and `treaty validate` flags it.

The `docs_dir` question controls the folder name. Answer `.` for the flat layout, or any other name (`docs/agents`, `.treaty`) to put them elsewhere.

**Projects installed before v0.8.0 are not moved.** They have no recorded `docs_dir`, and `treaty update` pins those to the flat layout automatically, so updating changes nothing but adds `docs_dir: '.'` to `.copier-answers.yml`. After updating a flat project, `treaty update` prints a one-line reminder that `treaty relocate` can move the docs; nothing moves unless you run it. Verified against every Copier-managed adopter we maintain: identical files touched, identical conflicts, versus the same update on v0.7.0.

To move an existing project into a folder, use `treaty relocate`:

```bash
treaty update                       # first: records docs_dir
git commit -am "Update the treaty"  # or skip this and pass --force below
treaty relocate --dry-run           # see the plan
treaty relocate                     # apply it
```

`treaty relocate` wants a clean tree, so the relocation is one change you can undo on its own. To relocate on top of the update's uncommitted changes and commit both together, pass `--force`; that is what it is for.

It moves the four working docs with `git mv` so history follows, carries the folder README along (writing one when leaving the root, and deleting an unedited one when flattening, where it would collide with your own `README.md`), rewrites the doc links in `AGENTS.md` and `project_overview.md`, retargets the project-relative links *inside* the moved docs for their new depth, records the new `docs_dir`, and does it in one pass so the recorded answer and the files on disk never disagree. Everything it changes is staged when it finishes; it prints the `git add` for any earlier changes it left alone, including files it moved that git wasn't tracking yet. `--to` picks a different folder, and `--to .` flattens everything back to the root.

Two things it will not do silently:

- **It refuses to run before `treaty update`.** A project whose answers predate `docs_dir` is pinned to a template that hardcodes the flat paths, so moving first guarantees a conflict on the next update. The command says so and stops.
- **It checks your `.gitignore`.** If your repo denies everything (`*`) and re-allows specific files, those rules stop matching once the docs move — already-tracked files survive, but the next work-log rotation is silently untracked. `treaty relocate` names the offending rule, and `treaty validate` keeps flagging it (`treaty-doc-gitignored`) until it is fixed.

Links pointing in **both** directions are handled, but differently:

- **Out of a moved doc, at your own files** — a `[demo](media/README.md)` in `next_steps.md` — is **rewritten** to `../media/README.md` so it still resolves. URLs, bare anchors, absolute paths, and links that were already broken are left exactly as written. The dry run lists these before it touches anything.
- **Into the treaty docs, from files the treaty does not own** — your README, CHANGELOG, CI config — is **reported, with line numbers, but never rewritten**. Those are yours to update.

</details>

<details>
<summary>Adding the treaty to a project that already has docs</summary>

`treaty init` runs a non-destructive preflight first. It warns about existing treaty files, case-mismatched ones such as `Work_Log.md`, and common planning docs such as `TODO.md`, `ROADMAP.md`, `NOTES.md`, or `CLAUDE.md`. It never moves, archives, rewrites, or deletes anything, and matching treaty paths are skipped rather than overwritten.

Case-mismatched treaty-looking paths **block** the install, because they can prevent canonical files from being created — especially on Windows. Rename or archive them, then rerun.

To fold existing docs into the treaty, say so explicitly — migration touches files the treaty otherwise never rewrites.

**Prompt — type this into your agent's chat:**

> Migrate this repo's existing planning and logging docs into the treaty. Preserve the originals.

</details>

## Update

Occasionally a new treaty version lands. One prompt takes care of it.

**Prompt — type this into your agent's chat:**

> Update the treaty.

This is the step most worth handing over. The merge can leave conflicts, and resolving them is judgment work — deciding which side of each hunk is your content and which is new upstream guidance. The agent doesn't need telling: the procedure is in the `treaty_conventions.md` sitting in your repo.

<details>
<summary>Prefer to run it yourself?</summary>

```bash
pipx upgrade agent-collab-treaty      # get the latest CLI first

treaty --version                      # CLI version, and the template you're pinned to
treaty diff                           # which sections would conflict?
git add -A && git commit -m "wip"     # update refuses a dirty tree
treaty update --dry-run               # preview: answer changes, updated files, conflicts
treaty update --dry-run --diff        # ...plus the full diff of each file
treaty update                         # apply
```

`treaty update` does a **three-way merge** from your pinned version up to the latest release, so edits that don't overlap upstream changes are kept automatically. If any file is left conflicted, the command names it and **exits non-zero** — a conflicted update is never reported as a success.

`treaty update --dry-run` runs that same merge in a disposable clone of your committed state and prints the summary a real apply would print — planned answer changes, files that update cleanly, files that would conflict — without writing anything to your project. It exits non-zero when the merge would conflict, so scripts can use it the same way as a real apply. Because the clone is of your *committed* state, uncommitted edits aren't previewed — but `--data` values are, since they come from the command line. Add `--diff` to see what changes inside each file, not just which files; the [release notes](https://github.com/yzhaoinuw/agent_collab_treaty/releases) list the CLI changes and which template files each release touches.

You don't have to remember to check. Since v0.11.0 the conventions have agents run `treaty update --dry-run` each time they rotate the work log (roughly every five working days) and tell you if a newer version is out. Updating stays your call.

Upgrade the CLI before updating. Template fixes often lean on CLI checks, and an old CLI runs without complaint: its `treaty validate` passes without knowing what the new template expects.

**Answering questions that are new in the target version.** Recorded answers are reused, and any question added since your pinned version silently takes the template default. Name the ones you care about with `--data`, repeatable:

```bash
treaty update --data uses_precommit=false --data verification_command="python -m pytest -q"
```

That is the whole reason it exists: without it, a big version jump leaves you re-prompting for *every* question with `--interactive`, or hand-editing the `.copier-answers.yml` whose first line tells you not to. `--data docs_dir=…` is refused on purpose — changing the layout through Copier deletes your customized docs and writes pristine ones at the new path, which is what [`treaty relocate`](#where-the-docs-live) exists to do safely.

`treaty diff` writes nothing. It renders the template version you're pinned to into a temp directory and compares section by section:

```text
AGENTS.md
  untouched 9   modified 1   removed 3   added 1
  ! removed: '## Release / Tag Checklist' — upstream edits arrive with nothing local to merge into
  ~ modified: '## Runtime Environment'

Conflict exposure: 4 section(s) across 1 file(s) would conflict if upstream revises them.
```

</details>

<details>
<summary>What your edits cost at update time</summary>

Cost depends on *what* you edit, not how much:

| Edit | Cost on `treaty update` |
|---|---|
| Filling in a bracket placeholder | None. Upstream never ships a revision to `[path/to/entrypoint]`. |
| Adding a section | None. Additions always merge cleanly. |
| Rewriting a maintained body | A conflict whenever upstream revises the same region. |
| Deleting a section | A conflict every time upstream touches it, with nothing local to merge into. Prefer the `has_releases` / `uses_precommit` / `include_git_ownership_note` answers, which stop it rendering at all. |
| Renaming a heading | The worst case. The merge reads it as a delete plus an unrelated add, so it conflicts *and* can't be auto-resolved. Change the body, keep the heading. |

`treaty diff` reports this breakdown for your project, and calls out renamed headings by name so you can restore the upstream heading and keep your body. `work_log.md` and `next_steps.md` are yours by design, so their drift is reported but never counted as risk.

</details>

<details>
<summary>Resolving conflicts, and the git requirement</summary>

Where your edits overlap a changed region, the merge leaves standard markers (`<<<<<<< before updating` / `>>>>>>> after updating`) in an unmerged file. Resolve them like any `git merge` — keep your content, fold in the new sections — and don't commit unresolved markers:

```bash
# after resolving, stage every file treaty update listed, conflicted or not:
git add AGENTS.md .copier-answers.yml && git commit
```

Stage `.copier-answers.yml` along with the resolved files: it records the new template version, and committing the merge without it leaves the project pinned to the old one. `treaty update` prints the exact `git add` line for you; it names files rather than using `git add -A`, so untracked files you kept out of the way during the update stay out of the commit.

After merging, `treaty update` prints a summary: old → new template version, answer changes, updated files, conflicted files. "Updated files" counts content changes only. Under `core.autocrlf=true`, Git can keep listing files whose line endings were rewritten during the merge; the summary lists those separately, and committing them changes nothing. Your recorded answers are reused by default; pass `--interactive` only to re-answer the template questions.

The project must be **git-tracked with a clean working tree** — Copier uses git for the three-way merge and to show a reviewable diff. Run `git init && git add . && git commit -m "treaty baseline"` once if you haven't.

To keep unrelated untracked files (data, scratch output) from tripping the clean-tree check, list them in `.git/info/exclude`. **Don't hide them with `status.showUntrackedFiles=no`, and make sure `*.rej` isn't gitignored** (a repo that ignores everything with `*` can add a `!*.rej` exception): Copier finds each conflict through the `.rej` file it leaves in `git status`, so with either setting a conflicting file would be silently replaced by the template version. `treaty update` refuses to run under either one, and fails if a merge leaves a `.rej` behind anyway.

</details>

## Validate

```bash
treaty --version                      # what you have, and what you're pinned to
treaty validate                       # in any project using the treaty
treaty validate --migration-hints     # plus overlap hints for legacy docs
```

It checks canonical filenames, `work_log.md` structure, live-log rotation, session verification sections, `next_steps.md` "Currently Hot" links, and whether git would ignore the treaty docs themselves. Exits non-zero when issues are found; `--warn-only` keeps it advisory.

Some checks are warnings, which print but never fail:

- a `CLAUDE.md` that doesn't import `AGENTS.md` (a line asking Claude to read it isn't an import; `@AGENTS.md` is);
- a `treaty` CLI older than the template your project is pinned to;
- template placeholders still unfilled, such as `[what it does]` or links to `path/to/...`. A fresh install has plenty, and an update can add a section full of them to a doc you finished long ago;
- template text that only your copy can fix: the "Setting this up for the first time?" paragraph in a work log that already has entries, an "Other sections below are background or paused" line sitting above active threads in `next_steps.md`, and a Currently Hot thread filed under Background / Paused.

The template keeps that text because changing `work_log.md` or `next_steps.md` upstream would conflict with nearly every adopter's own edits. So `validate` points it out instead, and you delete it once.

## Wiring Up Your Agent

`AGENTS.md` is the one file every agent should read at session start. Some tools load it directly; others want a small pointer file, which `treaty init` can generate:

| Tool | Pointer | Notes |
|---|---|---|
| Codex | none | Reads `AGENTS.md` natively. |
| Claude Code / Cowork | `CLAUDE.md` | Imports `AGENTS.md` with Claude's `@AGENTS.md` syntax. |
| Cursor | `.cursor/rules/treaty.mdc` | Always-applied project rule pointing back to `AGENTS.md`. Cursor also supports root `AGENTS.md` directly. |
| Windsurf | `.windsurf/rules/treaty.md` | Always-on workspace rule pointing Cascade back to `AGENTS.md`. Windsurf also processes root `AGENTS.md` directly. |
| Aider | `.aider.conf.yml` | Configures Aider to always read `AGENTS.md` as read-only context. |

For any other tool, add a one-line default instruction: *"At the start of every new chat or session in this repository, read `AGENTS.md` first and follow the documentation map there."*

## The Workflow In Practice

**This section describes what your *agent* does on its own — it is not a checklist for you to follow or to paste into a chat.** The installed docs already tell the agent all of it. It's written out here so you know what a session should look like, and can tell when one has skipped a step.

When a new agent session opens, the agent:

1. Reads `AGENTS.md` first.
2. Uses its documentation map to open only the relevant docs.
3. Reads the top of `work_log.md` for recent context.
4. Checks `next_steps.md` → "Currently Hot" for active priorities.
5. Does the work, following the conventions in `AGENTS.md`.
6. At the end of substantive work: runs the pre-flight checklist, runs `treaty validate`, prepends an entry to `work_log.md`, and updates `next_steps.md` if follow-up changed.

Your only part in this is the occasional [update](#update) prompt.

The rule that decides what goes in the log: **it records decisions about the project, not the content of the work produced.** The work itself is already in version control. "Implemented function X" and "drafted chapter 4" are noise for the same reason — the diff already says that. What belongs is the decision, the reversal, the approach tried and discarded and why, and evidence a future agent would otherwise have to rediscover.

That rule is also what makes the log worth reading for *you*. Because it captures decisions rather than activity, `next_steps.md` answers "where does this stand?" and `work_log.md` answers "what did we decide, and why?" — the two questions a status update or a handoff to a colleague actually needs. It costs no extra bookkeeping: the agent writes it as part of finishing the work.

`treaty_conventions.md` carries the full criteria, plus the log rotation policy that keeps `work_log.md` cheap to read.

## Why "Treaty"

Because it's a small agreement about where project context lives, what agents read first, and what they write back before leaving.

Treat it as a starting point, not a fixed standard. Add a "CI Note" section for your stack's commands, a "Domain Reminders" section for non-obvious gotchas, extra `project_overview.md` subsections for the diagrams or schemas that matter. Keep additions coherent with the existing structure rather than rewriting it — the value of a shared template is that every repo looks the same to the next agent.

## Badge

`treaty init` offers an opt-in "adopted" badge. It's hosted centrally by this repository, so your project receives **no extra files** and picks up any future design improvements automatically.

```markdown
[![Agent Collab Treaty](https://raw.githubusercontent.com/yzhaoinuw/agent_collab_treaty/main/assets/treaty-adopted.svg)](https://github.com/yzhaoinuw/agent_collab_treaty)
```

<details>
<summary>Why this one, and the fallback for non-GitHub renders</summary>

The tri-color SVG above is the primary recommendation: its text is outlined to vector paths, with no embedded or system font, so it renders **identically on GitHub across every platform** — no font substitution, no clipping.

Use the single-color shields.io fallback only if your README also renders **outside GitHub** — e.g. on PyPI or npm — where raw SVG images may be sanitized or blocked:

```markdown
[![Agent Collab Treaty](https://img.shields.io/badge/Agent_Collab_Treaty-adopted-6d81f1?style=flat-square)](https://github.com/yzhaoinuw/agent_collab_treaty)
```

This repo's own README uses the tri-color badge via a relative path; adopters use the `raw.githubusercontent.com` URL, which is the same image.

</details>

## Contributing

Bug reports, feature ideas, and PRs are welcome — see [CONTRIBUTING.md](CONTRIBUTING.md). It's the contributor front door, and it also carries the release and publishing mechanics for maintainers. To cite the project, use the repo's `CITATION.cff` (GitHub's "Cite this repository" button) or the DOI badge above — [10.5281/zenodo.21746757](https://doi.org/10.5281/zenodo.21746757), which always resolves to the latest archived release. Zenodo also mints a DOI per release if you need to cite a specific version.
