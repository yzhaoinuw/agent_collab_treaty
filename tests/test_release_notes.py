from __future__ import annotations

import importlib.util
import os
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _load():
    spec = importlib.util.spec_from_file_location(
        "release_notes", REPO_ROOT / "scripts" / "release_notes.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ReleaseNotesTests(unittest.TestCase):
    """#32: notes come from commit messages, since GitHub's list only PRs."""

    def test_notes_for_a_past_tag(self) -> None:
        cwd = os.getcwd()
        os.chdir(REPO_ROOT)
        try:
            notes = _load().main("v0.10.0")
        finally:
            os.chdir(cwd)

        self.assertIn("- **Warn about template text only the adopter's copy can fix**", notes)
        self.assertIn("  - When work_log.md conflicts", notes)
        self.assertNotIn("Release v0.10.0", notes)
        self.assertNotIn("Co-Authored-By", notes)
        self.assertIn("- `treaty_conventions.md`: maintained upstream", notes)
        self.assertNotIn("`{{`", notes, "paths with spaces stay whole")
        self.assertIn("python -m pip install -U agent-collab-treaty", notes)


if __name__ == "__main__":
    unittest.main()
