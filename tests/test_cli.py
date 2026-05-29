from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from agent_collab_treaty.cli import app


class TreatyCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.runner = CliRunner()

    def test_init_blocks_before_copy_for_noncanonical_treaty_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "Work_Log.md").write_text("# Legacy Work Log\n", encoding="utf-8")

            with patch("copier.run_copy") as run_copy:
                result = self.runner.invoke(
                    app,
                    ["init", str(root), "--source", ".", "--defaults"],
                )

            self.assertEqual(1, result.exit_code)
            self.assertIn("noncanonical-treaty-paths", result.output)
            self.assertIn("Resolve noncanonical treaty-looking paths", result.output)
            self.assertFalse((root / "AGENTS.md").exists())
            run_copy.assert_not_called()

    def test_init_warns_for_overlapping_docs_and_preserves_existing_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "TODO.md").write_text("# TODO\n", encoding="utf-8")

            with patch("copier.run_copy") as run_copy:
                result = self.runner.invoke(
                    app,
                    ["init", str(root), "--source", ".", "--defaults"],
                )

            self.assertEqual(0, result.exit_code)
            self.assertIn("overlapping-project-docs", result.output)
            kwargs = run_copy.call_args.kwargs
            self.assertIn("work_log.md", kwargs["skip_if_exists"])
            self.assertIn("AGENTS.md", kwargs["skip_if_exists"])

    def test_validate_migration_hints_reports_overlapping_docs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_valid_project(root)
            (root / "TODO.md").write_text("# TODO\n", encoding="utf-8")

            default_result = self.runner.invoke(app, ["validate", str(root)])
            hinted_result = self.runner.invoke(
                app,
                ["validate", str(root), "--migration-hints"],
            )

        self.assertEqual(0, default_result.exit_code)
        self.assertNotIn("TODO.md", default_result.output)
        self.assertEqual(0, hinted_result.exit_code)
        self.assertIn("Migration hints", hinted_result.output)
        self.assertIn("TODO.md", hinted_result.output)

def write_valid_project(root: Path) -> None:
    (root / "work_log_archive").mkdir()
    (root / "AGENTS.md").write_text("# Guidelines\n", encoding="utf-8")
    (root / "project_overview.md").write_text("# Project Overview\n", encoding="utf-8")
    (root / "next_steps.md").write_text(
        "\n".join(
            [
                "# Next Steps",
                "",
                "## Currently Hot",
                "",
                "- **Thread** - see [Thread](#thread-gpt-5).",
                "",
                "## Thread (gpt-5)",
                "",
                "Status: proposed",
            ]
        ),
        encoding="utf-8",
    )
    (root / "work_log.md").write_text(
        "\n".join(
            [
                "# Work Log",
                "",
                "## 2026-05-27",
                "",
                "### Entry (gpt-5)",
                "",
                "- Did a thing.",
                "- Verification:",
                "  - checked",
            ]
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    unittest.main()
