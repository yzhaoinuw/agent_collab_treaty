"""Print GitHub release notes for a tag, built from the commits since the last tag.

GitHub's generated notes list merged pull requests, and most changes here are
committed straight to `dev` without one, so they came out empty (#32). Commit
bodies already carry the user-facing bullets, so the notes reuse them.

Usage: python scripts/release_notes.py v0.10.1   (needs full history and tags)
"""

from __future__ import annotations

import re
import subprocess
import sys

UPGRADE = (
    "Upgrade the CLI first, then update each project:\n\n"
    "```bash\n"
    "python -m pip install -U agent-collab-treaty\n"
    "treaty update --dry-run   # in the project\n"
    "```"
)

# This repo's own treaty docs. A commit that only touches them changes nothing
# a user installs, so it has no place in the release notes.
OWN_DOCS = "treaty_docs/"

# What each shipped file costs an adopter at update time.
FILE_COST = {
    "treaty_conventions.md.jinja": "maintained upstream; merges cleanly unless you edited it",
    "AGENTS.md.jinja": "may conflict where you edited the same section",
    "project_overview.md.jinja": "may conflict where you edited the same section",
}


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], capture_output=True, text=True, check=True
    ).stdout


def previous_tag(tag: str) -> str | None:
    try:
        return git("describe", "--tags", "--abbrev=0", "--match", "v*", f"{tag}^").strip()
    except subprocess.CalledProcessError:
        return None


def commit_entries(span: str) -> list[str]:
    entries = []
    log = git("log", "--reverse", "--no-merges", "--format=%H%x1f%an%x1f%s%x1f%b%x1e", span)
    for record in filter(str.strip, log.split("\x1e")):
        sha, author, subject, body = record.strip("\n").split("\x1f", 3)
        # Release bumps and the weekly adopters-badge bot are not changes.
        if re.match(r"^Release v\d", subject) or author.endswith("[bot]"):
            continue
        if _only_own_docs(sha):
            continue
        bullets = [
            line
            for line in body.splitlines()
            if line.strip() and not re.match(r"^\s*Co-Authored-By:", line, re.I)
        ]
        entries.append("\n".join([f"- **{subject}**", *("  " + b for b in bullets)]))
    return entries


def _only_own_docs(sha: str) -> bool:
    files = git("diff-tree", "--no-commit-id", "--name-only", "-r", sha).splitlines()
    return bool(files) and all(f.startswith(OWN_DOCS) for f in files)


def template_changes(span_start: str | None, tag: str) -> list[str]:
    if span_start is None:
        return []
    names = git("diff", "--name-only", span_start, tag, "--", "template/", "copier.yml").splitlines()
    lines = []
    for name in names:
        short = name.split("/")[-1]
        cost = FILE_COST.get(short)
        label = short.removesuffix(".jinja")
        lines.append(f"- `{label}`" + (f": {cost}" if cost else ""))
    return lines


def main(tag: str) -> str:
    prev = previous_tag(tag)
    span = f"{prev}..{tag}" if prev else tag
    out = ["## Changes", ""]
    out += commit_entries(span) or ["- No changes besides the version bump."]
    out += ["", "## Template files changed", ""]
    changes = template_changes(prev, tag)
    out += changes or ["- None: `treaty update` only moves the pinned version."]
    out += ["", "## Upgrading", "", UPGRADE]
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: release_notes.py <tag>")
    print(main(sys.argv[1]), end="")
