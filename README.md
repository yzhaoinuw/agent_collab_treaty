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
| `AGENTS.md` | First-read contract. Runtime env, common task recipes, git/commit conventions, project-specific reminders. Both Codex and Claude Code / Cowork recognize this file by convention. |
| `CLAUDE.md` | One-line pointer to `AGENTS.md` for Claude-flavored tools that look for this filename specifically. Add similar pointer files (e.g. `CODEX.md`, `GEMINI.md`) if other agents in your workflow look for their own. |
| `project_overview.md` | Orientation doc. Active vs. legacy code map, repo structure, recommended read order. The single most valuable artifact for an agent that's never seen the codebase. |
| `next_steps.md` | The roadmap. A "Currently Hot" pointer at the top names the active threads so an agent doesn't have to scroll. |
| `work_log.md` | Session journal, newest-on-top. Each agent session appends a structured entry before handoff. |
| `work_log_archive.md` | Rotated older entries from `work_log.md`. Keeps the live log cheap to load. |

## How To Use

1. Copy these files into the root of your repo (excluding this `README.md`, which is for the template itself).
2. Fill in the placeholders — they're marked `[...]` in each file and are obvious in context.
3. Commit them. Future agent sessions will read them automatically.
4. As work progresses, prepend new entries to `work_log.md` and keep `next_steps.md` honest about what's currently hot.

## The Workflow In Practice

When a new agent session opens in a repo that uses this template:

1. Read `AGENTS.md` for env, conventions, and common tasks.
2. Skim `project_overview.md` to know what's active vs. legacy before touching code.
3. Read the top of `work_log.md` to pick up in-flight context. Use the cheap-read recipe in `AGENTS.md` to load only the most recent entries rather than the whole file.
4. Check `next_steps.md` → "Currently Hot" for the active priorities.
5. Do the work, following the conventions in `AGENTS.md`.
6. Before commit: run the pre-flight checklist from `AGENTS.md` and prepend a structured entry to `work_log.md`.

## Rotation Policy

`work_log.md` grows linearly over time. The template's recommended policy:

- Keep the current month's entries in `work_log.md`.
- At the start of each new month (or whenever the live log exceeds ~200-300 lines), move older entries into `work_log_archive.md` and update the rotation-date line at the top of the live log.
- The archive uses the same `## YYYY-MM-DD` header convention, so the cheap-read recipe in `AGENTS.md` works against it too.

## Why "Treaty"

Because it's a small, deliberate agreement between humans and agents about how they'll work together on the same code — what each side reads, what each side writes, where context lives, and how it stays current. Drop it into any repo and every agent that walks in inherits the same contract.

## Customization

Treat this as a starting point, not a fixed standard. Common per-project additions:

- A "Pre-commit Note" or "CI Note" section in `AGENTS.md` with the specific commands your stack uses (e.g., Black + pytest for Python, Prettier + Jest for JS).
- A "Domain Reminders" section in `AGENTS.md` for non-obvious gotchas (e.g., "don't blow away debug breadcrumbs during pipeline iteration").
- Subsections of `project_overview.md` for the architecture diagrams or data schemas that matter most.

Keep additions coherent with the existing structure rather than rewriting it — the value of a shared template is that every repo looks the same to the next agent.
