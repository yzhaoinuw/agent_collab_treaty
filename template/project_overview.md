# Project Overview

This document orients a new agent (or human collaborator) to the codebase. It's the single most valuable artifact for getting useful work done quickly. Keep it current — when the active code path changes, update the relevant sections here.

## What This Repo Is

[One or two paragraphs describing what the project is, who uses it, and what it does at a high level. Mention the entry point(s) and the primary technology stack.]

## Active Runtime Path

Describe the path from "user invokes the app" to "result". List each layer briefly with a pointer to the relevant file.

### 1. Entrypoint

[`path/to/entrypoint`](path/to/entrypoint)

- [what it does]
- [what it imports / hands off to]

### 2. Main module

[`path/to/main_module`](path/to/main_module)

- [key responsibilities]
- [important imports]

### 3. [Add subsections as needed for UI layer, business logic, persistence, etc.]

## Repo Structure Map

```text
project_root/
|- AGENTS.md
|- project_overview.md
|- next_steps.md
|- work_log.md
|- work_log_archive/
|- README.md
|- [src/ or app/ or lib/]
|- [tests/]
|- [scripts/]
|- [docs/]
|- [config files: pyproject.toml / package.json / Cargo.toml / etc.]
```

## What Looks Active vs. Legacy

This is the single most important section for agents. Many repos accumulate parallel implementations during refactors; without an explicit map, an agent will frequently edit the wrong file.

### Active / relevant now

- [`path/to/active_file_1`](path/to/active_file_1)
- [`path/to/active_file_2`](path/to/active_file_2)

### Likely older or secondary

- [`path/to/legacy_file_1`](path/to/legacy_file_1) — [why it's still in-tree]
- [`path/to/legacy_file_2`](path/to/legacy_file_2) — [reason]

## Tests And Fixtures

[Where the test suite lives, what kinds of tests exist (unit / integration / smoke / e2e), and what fixtures or sample data are canonical for development.]

- [`path/to/tests/`](path/to/tests/) — [brief description]
- [`path/to/sample_data/`](path/to/sample_data/) — [what's in it]

## User Data Expectations

If the application consumes external data, document the expected schema here.

[Required / optional fields, file formats, conventions.]

## Practical Mental Model

If you only want to understand the current product, read files in this order:

1. [`README.md`](README.md)
2. [`path/to/entrypoint`](path/to/entrypoint)
3. [`path/to/main_module`](path/to/main_module)
4. [next most important file]
5. [...]

## Questions Worth Clarifying Later

Not blockers, just places where intent would help future agents:

- [Whether the legacy `[X]` module should be removed or kept as reference]
- [Whether `[Y]` is a stable contract or a moving target]
- [Anything where you, as the maintainer, would otherwise have to answer the same question from each new agent]
