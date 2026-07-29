from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_collab_treaty.diff import (
    PREAMBLE_KEY,
    compare_file,
    compare_trees,
    detect_renames,
    format_report,
    split_sections,
)

PRISTINE = "\n".join(
    [
        "# Guidelines",
        "",
        "Intro line.",
        "",
        "## Startup Rule",
        "",
        "Read this first.",
        "",
        "## Runtime Environment",
        "",
        "[env placeholder]",
        "",
        "## Release / Tag Checklist",
        "",
        "Gate the tag.",
        "",
    ]
)


class SplitSectionsTests(unittest.TestCase):
    def test_collects_preamble_and_sections_in_order(self) -> None:
        sections = split_sections(PRISTINE)
        self.assertEqual(
            [
                PREAMBLE_KEY,
                "## Startup Rule",
                "## Runtime Environment",
                "## Release / Tag Checklist",
            ],
            list(sections),
        )
        self.assertEqual("Read this first.", sections["## Startup Rule"])

    def test_omits_empty_preamble(self) -> None:
        self.assertNotIn(PREAMBLE_KEY, split_sections("## Only\n\nbody\n"))

    def test_ignores_headings_deeper_than_level_two(self) -> None:
        sections = split_sections("## Top\n\nbody\n\n### Nested\n\nmore\n")
        self.assertEqual(["## Top"], list(sections))
        self.assertIn("### Nested", sections["## Top"])


class CompareFileTests(unittest.TestCase):
    def test_classifies_untouched_modified_removed_and_added(self) -> None:
        local = "\n".join(
            [
                "# Guidelines",
                "",
                "Intro line.",
                "",
                "## Startup Rule",
                "",
                "Read this first.",
                "",
                "## Runtime Environment",
                "",
                "conda activate proj",
                "",
                "## Story Bible Ownership",
                "",
                "Who owns which layer.",
                "",
            ]
        )
        result = compare_file("AGENTS.md", PRISTINE, local)

        self.assertEqual([PREAMBLE_KEY, "## Startup Rule"], result.untouched)
        self.assertEqual(["## Runtime Environment"], result.modified)
        self.assertEqual(["## Release / Tag Checklist"], result.removed)
        self.assertEqual(["## Story Bible Ownership"], result.added)
        self.assertEqual([], result.renamed)
        self.assertEqual(2, result.at_risk)

    def test_flags_a_renamed_heading_instead_of_delete_plus_add(self) -> None:
        local = PRISTINE.replace("## Release / Tag Checklist", "## Publishing")
        result = compare_file("AGENTS.md", PRISTINE, local)

        self.assertEqual([], result.removed)
        self.assertEqual([], result.added)
        self.assertEqual(1, len(result.renamed))
        self.assertEqual("## Release / Tag Checklist", result.renamed[0].old)
        self.assertEqual("## Publishing", result.renamed[0].new)

    def test_reports_a_file_missing_from_the_project(self) -> None:
        result = compare_file("treaty_conventions.md", PRISTINE, None)
        self.assertTrue(result.missing_locally)
        self.assertEqual(0, result.at_risk)

    def test_adopter_owned_files_carry_no_risk(self) -> None:
        result = compare_file("work_log.md", PRISTINE, "## Startup Rule\n\nrewritten\n")
        self.assertTrue(result.adopter_owned)
        self.assertEqual(0, result.at_risk)


class DetectRenamesTests(unittest.TestCase):
    def test_ignores_unrelated_removals_and_additions(self) -> None:
        renames = detect_renames(
            ["## Gone"],
            ["## Fresh"],
            {"## Gone": "totally different prose about releases"},
            {"## Fresh": "unrelated notes on story continuity"},
        )
        self.assertEqual([], renames)

    def test_matches_each_removal_to_at_most_one_addition(self) -> None:
        body = "the same body text, word for word, in both places"
        renames = detect_renames(
            ["## A"],
            ["## B", "## C"],
            {"## A": body},
            {"## B": body, "## C": body},
        )
        self.assertEqual(1, len(renames))


class CompareTreesTests(unittest.TestCase):
    def test_walks_markdown_files_and_notes_missing_ones(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pristine, local = root / "pristine", root / "local"
            (pristine / "work_log_archive").mkdir(parents=True)
            local.mkdir()
            (pristine / "AGENTS.md").write_text(PRISTINE, encoding="utf-8")
            (pristine / "work_log_archive" / "README.md").write_text(
                "## Archive\n\nrules\n", encoding="utf-8"
            )
            (local / "AGENTS.md").write_text(PRISTINE, encoding="utf-8")

            diffs = {diff.path: diff for diff in compare_trees(pristine, local)}

        self.assertEqual({"AGENTS.md", "work_log_archive/README.md"}, set(diffs))
        self.assertEqual(0, diffs["AGENTS.md"].at_risk)
        self.assertTrue(diffs["work_log_archive/README.md"].missing_locally)


class FormatReportTests(unittest.TestCase):
    def test_calls_out_renames_and_removals_and_totals_exposure(self) -> None:
        local = PRISTINE.replace(
            "## Release / Tag Checklist", "## Publishing"
        ).replace("[env placeholder]", "conda activate proj")
        report = "\n".join(
            format_report([compare_file("AGENTS.md", PRISTINE, local)], "v0.4.1")
        )

        self.assertIn("template version v0.4.1", report)
        self.assertIn("! renamed:", report)
        self.assertIn("~ modified: '## Runtime Environment'", report)
        self.assertIn("Conflict exposure: 2 section(s) across 1 file(s)", report)
        self.assertIn("Renamed headings are the costliest drift", report)
        self.assertIn("Nothing was written.", report)


if __name__ == "__main__":
    unittest.main()
