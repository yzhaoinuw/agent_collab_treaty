from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_collab_treaty.adoption import (
    format_adoption_notices,
    format_migration_hints,
    inspect_adoption_context,
)


class AdoptionPreflightTests(unittest.TestCase):
    def test_empty_project_has_no_notices(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notices = inspect_adoption_context(Path(tmp))

        self.assertEqual([], notices)

    def test_existing_canonical_treaty_paths_are_reported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "AGENTS.md").write_text("# Agents\n", encoding="utf-8")
            (root / "work_log.md").write_text("# Work Log\n", encoding="utf-8")

            notices = inspect_adoption_context(root)

        notice = self._notice_by_code(notices, "existing-treaty-paths")
        self.assertIn("AGENTS.md", notice.paths)
        self.assertIn("work_log.md", notice.paths)

    def test_wrong_case_treaty_paths_are_reported_as_noncanonical(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "Work_Log.md").write_text("# Legacy Work Log\n", encoding="utf-8")

            notices = inspect_adoption_context(root)

        notice = self._notice_by_code(notices, "noncanonical-treaty-paths")
        self.assertEqual(("Work_Log.md -> work_log.md",), notice.paths)

    def test_overlapping_project_docs_are_preserved_as_is(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "TODO.md").write_text("# TODO\n", encoding="utf-8")
            (root / "ROADMAP.md").write_text("# Roadmap\n", encoding="utf-8")
            (root / "CLAUDE.md").write_text("@AGENTS.md\n", encoding="utf-8")

            notices = inspect_adoption_context(root)

        notice = self._notice_by_code(notices, "overlapping-project-docs")
        self.assertEqual({"TODO.md", "ROADMAP.md", "CLAUDE.md"}, set(notice.paths))

    def test_formatted_notices_say_preflight_is_non_destructive(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "TODO.md").write_text("# TODO\n", encoding="utf-8")

            lines = format_adoption_notices(inspect_adoption_context(root))

        output = "\n".join(lines)
        self.assertIn("Adoption preflight", output)
        self.assertIn("No files will be moved", output)
        self.assertIn("matching treaty template paths will be skipped", output)
        self.assertIn("TODO.md", output)

    def test_migration_hints_exclude_existing_canonical_treaty_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "AGENTS.md").write_text("# Agents\n", encoding="utf-8")
            (root / "TODO.md").write_text("# TODO\n", encoding="utf-8")

            lines = format_migration_hints(inspect_adoption_context(root))

        output = "\n".join(lines)
        self.assertIn("Migration hints", output)
        self.assertIn("TODO.md", output)
        self.assertNotIn("existing-treaty-paths", output)

    def _notice_by_code(self, notices, code):
        for notice in notices:
            if notice.code == code:
                return notice
        self.fail(f"Missing adoption notice: {code}")


if __name__ == "__main__":
    unittest.main()
