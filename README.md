# Agent Collab Treaty

A drop-in template for the documentation contract that lets multiple coding agents (Claude, Codex, future tools) collaborate productively on the same repository.

## What This Is

A small, opinionated set of root-level Markdown files that any agent reads at the start of a session to know:

- what environment to run in,
- what's active code versus legacy,
- what work is currently in flight,
- what was done in recent sessions,
- and what conventions to follow for commits and code style.

The template is language- and framework-agnostic. It works whether the project is Python, JavaScript, Go, Rust, or a mix — you fill in the project-specific details, the structure stays the same.

## What's In The Template

| File | Purpose |
|---|---|
| `AGENTS.md` | First-read contract. Startup rule, documentation map, runtime env, common task recipes, git/commit conventions, project-specific reminders. Both Codex and Claude Code / Cowork recognize this file by convention. |
| `project_overview.md` | Orientation doc. Active vs. legacy code map, repo structure, recommended read order. The single most valuable artifact for an agent that's never seen the codebase. |
| `next_steps.md` | The roadmap. A "Currently Hot" pointer at the top names the active threads so an agent doesn't have to scroll. |
| `work_log.md` | Session journal, newest-on-top. Holds at most the 5 most recent unique calendar dates. Each agent session prepends a structured entry before handoff. |
| `work_log_archive/` | Directory of rotated 5-date chunks from `work_log.md`. Each file is named `work_log_<earliest>_to_<latest>.md` and holds exactly 5 dates. Keeps the live log cheap to load. |

## How To Use

The fastest path is the `treaty` CLI, which scaffolds (and later updates) the treaty files in any project — new or existing.

### Option 1 — install the CLI, then run `treaty init`

```bash
# isolated install (recommended; requires pipx)
pipx install agent-collab-treaty

# or in a regular venv
pip install agent-collab-treaty

# then, from inside the project you want to add the treaty to:
treaty init
```

`treaty init` asks a few short questions (integration branch, env activation command, test command) and drops the treaty files into the current directory. Re-run later with `treaty update` to pull in upstream refinements without losing your local edits.

> **Note**: `treaty update` requires the target project to be a git-tracked repo (Copier uses git for three-way merges). If your project isn't a git repo yet, run `git init && git add . && git commit -m "treaty baseline"` once before the first `treaty update`.

Non-interactive use:

```bash
treaty init . --defaults \
  --data integration_branch=main \
  --data env_activation='conda activate myenv' \
  --data test_command='pytest -v -m "not slow"'
```

### Option 2 — use Copier directly (no install)

The CLI is a thin wrapper around [Copier](https://copier.readthedocs.io/). If you'd rather not install another tool:

```bash
pipx run copier copy gh:yzhaoinuw/agent_collab_treaty .
```

### Option 3 — just copy the files

Old-school: copy the root-level Markdown files (`AGENTS.md`, `work_log.md`, `next_steps.md`, `project_overview.md`, `work_log_archive/`) from this repo into your project and fill in the `[...]` placeholders by hand.

Whichever path you pick, future agent sessions will read the files automatically. As work progresses, prepend new entries to `work_log.md` and keep `next_steps.md` honest about what's currently hot.

## Wiring Up Your Agent

The template is intentionally **agent-agnostic** — it does not ship `CLAUDE.md`, `CODEX.md`, `GEMINI.md`, or any other vendor-specific pointer file. `AGENTS.md` is the one file every agent should read at the start of a session, but not every tool looks for that name by default. Configure the tool(s) you actually use so they always read `AGENTS.md` first:

- **Codex** and **Claude Code / Cowork** recognize `AGENTS.md` by convention — no extra configuration needed.
- For any other tool, add a one-line default instruction (system prompt, custom instructions, or equivalent) such as: *"At the start of every new chat or session in this repository, read `AGENTS.md` first and follow the documentation map there."*
- If your tool only reads a vendor-specific file (e.g. `CLAUDE.md`, `GEMINI.md`), create that pointer locally — the `.gitignore` already excludes those filenames so they stay on your machine and the template repo remains vendor-neutral.

## The Workflow In Practice

When a new agent session opens in a repo that uses this template:

1. Read `AGENTS.md` first. Its **Startup Rule** tells the agent not to auto-load every Markdown file, and its **Documentation** section is the map of which other docs to open for which kind of task.
2. From the documentation map, skim `project_overview.md` if the task touches an unfamiliar area, or jump straight to the relevant doc otherwise.
3. Read the top of `work_log.md` to pick up in-flight context. Use the cheap-read recipe in `AGENTS.md` to load only the most recent entries rather than the whole file.
4. Check `next_steps.md` → "Currently Hot" for the active priorities.
5. Do the work, following the conventions in `AGENTS.md`.
6. Before commit: run the pre-flight checklist from `AGENTS.md` and prepend a structured entry to `work_log.md`.

## Rotation Policy

`work_log.md` grows linearly over time. The template's policy keeps the live file cheap to load by rotating in fixed-size chunks:

- The live `work_log.md` holds at most the **5 most recent unique calendar dates**.
- When prepending a new date would push the live log past 5 unique dates, move the oldest 5 dates as a chunk into a new file at `work_log_archive/work_log_<earliest>_to_<latest>.md`. Each archive file holds exactly 5 dates.
- All files (live and archive) use the same `## YYYY-MM-DD` header convention, so the anchor-grep recipe in `AGENTS.md` works across both with one command:

  ```
  rg -n '^## [0-9]{4}-[0-9]{2}-[0-9]{2}' work_log.md work_log_archive/
  ```

## Why "Treaty"

Because it's a small, deliberate agreement between humans and agents about how they'll work together on the same code — what each side reads, what each side writes, where context lives, and how it stays current. Drop it into any repo and every agent that walks in inherits the same contract.

## Customization

Treat this as a starting point, not a fixed standard. Common per-project additions:

- A "Pre-commit Note" or "CI Note" section in `AGENTS.md` with the specific commands your stack uses (e.g., Black + pytest for Python, Prettier + Jest for JS).
- A "Domain Reminders" section in `AGENTS.md` for non-obvious gotchas (e.g., "don't blow away debug breadcrumbs during pipeline iteration").
- Subsections of `project_overview.md` for the architecture diagrams or data schemas that matter most.

Keep additions coherent with the existing structure rather than rewriting it — the value of a shared template is that every repo looks the same to the next agent.
