from __future__ import annotations

import tempfile
import unittest
from datetime import date
from pathlib import Path

from agent_collab_treaty.validation import validate_project


class TreatyValidationTests(unittest.TestCase):
    def test_valid_project_has_no_issues(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_valid_project(root)

            issues = validate_project(root)

        self.assertEqual([], issues)

    def test_work_log_reports_missing_metadata_and_verification(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_valid_project(root)
            (root / "work_log.md").write_text(
                "\n".join(
                    [
                        "# Work Log",
                        "",
                        "## 2026-05-27",
                        "",
                        "### Missing metadata",
                        "",
                        "- Did a thing.",
                    ]
                ),
                encoding="utf-8",
            )

            issues = validate_project(root)

        codes = {issue.code for issue in issues}
        self.assertIn("work-log-missing-session-metadata", codes)
        self.assertIn("work-log-missing-verification", codes)

    def test_wrong_case_work_log_reports_one_path_issue_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_valid_project(root)
            (root / "work_log.md").unlink()
            (root / "Work_Log.md").write_text(
                "\n".join(
                    [
                        "# Work Log",
                        "",
                        "## 2026-05-27",
                        "",
                        "### Legacy heading",
                        "",
                        "- Did a thing.",
                    ]
                ),
                encoding="utf-8",
            )

            issues = validate_project(root)

        codes = [issue.code for issue in issues]
        self.assertEqual(["noncanonical-path-case"], codes)

    def test_wrong_case_required_path_reports_noncanonical_name(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_valid_project(root)
            (root / "next_steps.md").unlink()
            (root / "Next_Steps.md").write_text("# Next Steps\n", encoding="utf-8")

            issues = validate_project(root)

        codes = [issue.code for issue in issues]
        self.assertIn("noncanonical-path-case", codes)
        self.assertNotIn("next-steps-missing-currently-hot", codes)

    def test_case_collision_reports_path_collision_when_supported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_valid_project(root)
            (root / "Work_Log.md").write_text("# Legacy Work Log\n", encoding="utf-8")
            work_log_matches = [
                path.name for path in root.iterdir() if path.name.lower() == "work_log.md"
            ]
            if len(work_log_matches) < 2:
                self.skipTest("Filesystem does not support case-only duplicate paths")

            issues = validate_project(root)

        self.assertIn("path-case-collision", {issue.code for issue in issues})

    def test_work_log_reports_rotation_needed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_valid_project(root)
            dates = [
                "2026-05-27",
                "2026-05-26",
                "2026-05-25",
                "2026-05-24",
                "2026-05-23",
                "2026-05-22",
            ]
            body = ["# Work Log", ""]
            for date in dates:
                body.extend(
                    [
                        f"## {date}",
                        "",
                        "### Entry (gpt-5)",
                        "",
                        "- Did a thing.",
                        "- Verification:",
                        "  - checked",
                        "",
                    ]
                )
            (root / "work_log.md").write_text("\n".join(body), encoding="utf-8")

            issues = validate_project(root)

        self.assertIn("work-log-rotation-needed", {issue.code for issue in issues})

    def test_work_log_reports_future_date(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_valid_project(root)
            (root / "work_log.md").write_text(
                "\n".join(
                    [
                        "# Work Log",
                        "",
                        "## 2026-07-02",
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

            issues = validate_project(root, today=date(2026, 7, 1))

        self.assertIn("work-log-future-date", {issue.code for issue in issues})

    def test_work_log_todays_date_is_not_flagged_as_future(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_valid_project(root)
            (root / "work_log.md").write_text(
                "\n".join(
                    [
                        "# Work Log",
                        "",
                        "## 2026-07-01",
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

            issues = validate_project(root, today=date(2026, 7, 1))

        self.assertNotIn("work-log-future-date", {issue.code for issue in issues})

    def test_next_steps_reports_broken_currently_hot_anchor(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_valid_project(root)
            (root / "next_steps.md").write_text(
                "\n".join(
                    [
                        "# Next Steps",
                        "",
                        "## Currently Hot",
                        "",
                        "- **Missing** - see [Missing](#missing-thread).",
                    ]
                ),
                encoding="utf-8",
            )

            issues = validate_project(root)

        self.assertIn("next-steps-broken-hot-link", {issue.code for issue in issues})


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
                "<!--",
                "### Commented heading without metadata",
                "-->",
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
