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
        self.assertIn("- `<docs_dir>/treaty_conventions.md`: maintained upstream", notes)
        self.assertNotIn("`{{`", notes, "paths with spaces stay whole")
        self.assertIn("python -m pip install -U agent-collab-treaty", notes)

    def test_bot_commits_are_left_out(self) -> None:
        """v0.9.1's range includes the weekly adopters-badge bot commit."""
        cwd = os.getcwd()
        os.chdir(REPO_ROOT)
        try:
            notes = _load().main("v0.9.1")
        finally:
            os.chdir(cwd)

        self.assertIn("Stop treaty update from hiding rejected merges", notes)
        self.assertNotIn("Update adopters badge count", notes)

    def test_commits_touching_only_our_own_treaty_docs_are_left_out(self) -> None:
        """v0.10.3's range has a commit that only updated treaty_docs/."""
        cwd = os.getcwd()
        os.chdir(REPO_ROOT)
        try:
            notes = _load().main("v0.10.3")
        finally:
            os.chdir(cwd)

        self.assertIn("Point flat projects at treaty relocate", notes)
        self.assertNotIn("Record #34's field confirmation", notes)


if __name__ == "__main__":
    unittest.main()


class TemplateLabelTests(unittest.TestCase):
    def test_labels_are_paths_an_adopter_would_recognise(self) -> None:
        label = _load().template_label
        self.assertEqual("copier.yml", label("copier.yml"))
        self.assertEqual("AGENTS.md", label("template/AGENTS.md.jinja"))
        self.assertEqual(
            "<docs_dir>/work_log_archive/README.md",
            label("template/{{ docs_dir }}/work_log_archive/README.md"),
        )
        self.assertEqual(
            "<docs_dir>/README.md",
            label("template/{{ docs_dir }}/{% if docs_dir not in ['.', ''] %}README.md{% endif %}.jinja"),
        )
