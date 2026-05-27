# Next Steps

Use this checklist alongside `work_log.md`.

## Currently Hot

Active threads — read these first to know what work is in flight:

- **Publish to PyPI** — `LICENSE` + GitHub Actions workflows landed. Blocked on user-side PyPI Pending Publisher + GitHub environments setup, then a TestPyPI dry-run, then a `v0.1.0` tag. See [Publish to PyPI](#publish-to-pypi-claude-opus-4-7).
- **Per-agent pointer files in `treaty init`** — auto-generate `CLAUDE.md`, `.cursor/rules/treaty.mdc`, `.windsurfrules`, etc. based on a multiselect prompt. See [Per-agent pointer files in init](#per-agent-pointer-files-in-init-claude-opus-4-7).
- **`treaty validate`** — lint work_log entries against the documented format and rotation policy. See [`treaty validate`](#treaty-validate-claude-opus-4-7).

When an agent (or human) creates or significantly updates a thread/plan here, include model + version, effort/thinking mode, and token budget (if known) in parentheses after the thread name or at the end of the status line, using the same compact convention as `work_log.md`.

Other sections below are background or paused; treat them as reference unless a new request reopens them.

## Publish to PyPI (claude-opus-4-7)

Status: in progress — code landed, blocked on user-side PyPI setup

Today the only install path is `pip install git+https://github.com/yzhaoinuw/agent_collab_treaty.git@main`. To get to the README's promised `pipx install agent-collab-treaty`, we need a real PyPI release.

Done:

- `LICENSE` (MIT) at the repo root, matching the metadata in `pyproject.toml`.
- `.github/workflows/release.yml` — fires on `v*` tag push, builds sdist + wheel, publishes to PyPI via trusted publishing (OIDC), creates a GitHub Release with auto-generated notes + attached dist files.
- `.github/workflows/test-publish.yml` — `workflow_dispatch` (manual) trigger, publishes to TestPyPI for dry-runs without burning a real version number.
- README "Releasing to PyPI" section documenting the one-time setup steps and the release flow.

Remaining work (blocked on the user):

- Create PyPI account at https://pypi.org (if you don't have one) and a separate TestPyPI account at https://test.pypi.org.
- Register `agent-collab-treaty` as a Pending Publisher on both PyPI and TestPyPI with the exact values documented in the README "Releasing to PyPI" section (repo `yzhaoinuw/agent_collab_treaty`, workflow filename `release.yml` / `test-publish.yml`, environment name `pypi` / `testpypi`).
- Create the two GitHub Environments (`pypi`, `testpypi`) under repo Settings → Environments.
- Manually fire `test-publish.yml` from the Actions tab to dry-run against TestPyPI.
- Once TestPyPI looks good, tag `v0.1.0` on `main` to trigger the real release.

Open question:

- Whether to keep the GitHub-URL install documented as a fallback for unreleased changes, or remove it once PyPI is the canonical path.

## Per-agent pointer files in init (claude-opus-4-7)

Status: proposed

The MVP `treaty init` doesn't generate per-agent pointer files — the post-install message just tells users to set them up manually. That defeats part of the original value prop: "agents automatically follow the treaty moving forward."

Proposed plan:

- Add a multiselect `agents` question to `copier.yml` with choices: `claude-code`, `cursor`, `windsurf`, `aider`. (Codex doesn't need a pointer file — it reads `AGENTS.md` natively.)
- For each selected agent, conditionally render the right pointer file using Copier's filename-templating pattern: `{% if "claude-code" in agents %}CLAUDE.md.jinja{% endif %}`.
- Pointer file contents should be minimal — a one-liner pointing at `AGENTS.md` is plenty.

Remaining work:

- Confirm the exact filenames and paths each agent looks for: Cursor's `.cursor/rules/*.mdc` format, Windsurf's `.windsurfrules`, Aider's conventions doc.
- Decide whether to commit these pointer files by default (currently the repo's `.gitignore` excludes `CLAUDE.md`/`CODEX.md`/`GEMINI.md` — that policy was about keeping the *treaty repo itself* agent-agnostic, and may not apply to projects that install the treaty).

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
