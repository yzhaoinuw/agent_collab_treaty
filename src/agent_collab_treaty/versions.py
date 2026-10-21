"""Compare the running CLI's version with the template version a project pins."""

from __future__ import annotations

import re
from typing import Optional

from . import __version__

_VERSION_RE = re.compile(r"^v?(\d+)\.(\d+)(?:\.(\d+))?")

UPGRADE_COMMAND = "python -m pip install -U agent-collab-treaty"


def parse_version(text: object) -> Optional[tuple[int, int, int]]:
    """Read ``0.9.0`` / ``v0.9.0`` / ``v0.9.0-4-gabc123`` as a comparable tuple.

    Returns None for anything else (a bare commit hash, a branch name), so a
    pin we cannot read never produces a warning.
    """
    if not isinstance(text, str):
        return None
    match = _VERSION_RE.match(text.strip())
    if not match:
        return None
    major, minor, patch = match.groups()
    return int(major), int(minor), int(patch or 0)


def cli_older_than(template_commit: object, cli_version: str = __version__) -> bool:
    """True when this CLI predates the template version a project is pinned to.

    An older CLI still runs against a newer project, quietly: it lacks the
    commands and safeguards the project's own docs describe (`treaty relocate`
    arrived in v0.9.0), and it validates against rules the template has moved
    past. Adopters hit this when a project env carries an old install.
    """
    template = parse_version(template_commit)
    cli = parse_version(cli_version)
    return template is not None and cli is not None and cli < template


def skew_message(template_commit: object, cli_version: str = __version__) -> str:
    return (
        f"treaty CLI {cli_version} is older than this project's template "
        f"({template_commit}), so it may lack commands and checks that template "
        f"relies on. Upgrade with: {UPGRADE_COMMAND}"
    )
