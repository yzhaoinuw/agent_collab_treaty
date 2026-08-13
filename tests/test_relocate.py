"""Tests for `treaty relocate`.

The command exists because doing this by hand fails quietly in three ways —
wrong ordering vs. `treaty update`, stale links in `AGENTS.md`, and a deny-all
`.gitignore` that stops matching after the move. Each of those has a test here.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import yaml

from agent_collab_treaty.relocate import (
    apply_relocation,
    docs_prefix,
    format_plan,
    plan_relocation,
    root_prefix,
)
from agent_collab_treaty.validation import validate_project

MOVABLE = ("treaty_conventions.md", "next_steps.md", "work_log.md")


def _git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True, check=False
    )


class PrefixTests(unittest.TestCase):
    def test_docs_prefix(self) -> None:
        self.assertEqual("", docs_prefix("."))
        self.assertEqual("", docs_prefix(""))
        self.assertEqual("treaty_docs/", docs_prefix("treaty_docs"))
        self.assertEqual("docs/agents/", docs_prefix("docs/agents/"))

    def test_root_prefix_tracks_depth(self) -> None:
        self.assertEqual("", root_prefix("."))
        self.assertEqual("../", root_prefix("treaty_docs"))
        self.assertEqual("../../", root_prefix("docs/agents"))
        self.assertEqual("../../../", root_prefix("a/b/c"))


class RelocateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def _project(self, docs_dir: str = ".", *, answers: bool = True) -> Path:
        """Build a minimal treaty project in the given layout."""
        root = self.tmp / f"proj_{abs(hash(docs_dir)) % 10000}_{int(answers)}"
        prefix = docs_prefix(docs_dir)
        (root / prefix).mkdir(parents=True, exist_ok=True)
        (root / f"{prefix}work_log_archive").mkdir(parents=True, exist_ok=True)
        (root / f"{prefix}work_log_archive" / "README.md").write_text(
            "Older notes rotated out of [`../work_log.md`](../work_log.md).\n",
            encoding="utf-8",
        )
        (root / f"{prefix}work_log.md").write_text(
            "# Work Log\n\n## 2026-01-01\n\n### S (m)\n\n- Verification:\n  - ok\n",
            encoding="utf-8",
        )
        (root / f"{prefix}next_steps.md").write_text(
            "# Next Steps\n\n## Currently Hot\n\n- thing\n", encoding="utf-8"
        )
        rp = root_prefix(docs_dir)
        (root / f"{prefix}treaty_conventions.md").write_text(
            f"# Conventions\n\nSee [`{rp}AGENTS.md`]({rp}AGENTS.md) and "
            f"`{rp}project_overview.md`.\n",
            encoding="utf-8",
        )
        (root / "AGENTS.md").write_text(
            f"# Agents\n\nLog to `{prefix}work_log.md`, plan in "
            f"[`{prefix}next_steps.md`]({prefix}next_steps.md). "
            f"Mechanics: {prefix}treaty_conventions.md. "
            f"Archive: {prefix}work_log_archive/\n",
            encoding="utf-8",
        )
        (root / "project_overview.md").write_text(
            f"# Overview\n\nDocs live in `{prefix}work_log.md`.\n", encoding="utf-8"
        )
        if answers:
            (root / ".copier-answers.yml").write_text(
                f"_commit: v0.8.0\n_src_path: gh:x/y\ndocs_dir: {docs_dir}\n",
                encoding="utf-8",
            )
        _git(root, "init", "-q", ".")
        _git(root, "add", "-A")
        _git(root, "-c", "user.email=t@e.st", "-c", "user.name=T", "commit", "-qm", "base")
        return root

    # --- ordering guard -------------------------------------------------

    def test_blocks_when_answers_predate_docs_dir(self) -> None:
        root = self._project(".")
        (root / ".copier-answers.yml").write_text(
            "_commit: v0.7.0\n_src_path: gh:x/y\n", encoding="utf-8"
        )
        plan = plan_relocation(root, "treaty_docs")
        self.assertTrue(plan.blockers)
        self.assertIn("treaty update", plan.blockers[0])
        with self.assertRaises(ValueError):
            apply_relocation(plan)
        self.assertTrue((root / "work_log.md").exists(), "must not move when blocked")

    def test_allows_a_project_with_no_answers_file(self) -> None:
        root = self._project(".", answers=False)
        plan = plan_relocation(root, "treaty_docs")
        self.assertEqual([], plan.blockers)
        self.assertFalse(plan.answers_update)

    def test_blocks_when_destination_is_occupied(self) -> None:
        root = self._project(".")
        (root / "treaty_docs").mkdir()
        (root / "treaty_docs" / "work_log.md").write_text("theirs\n", encoding="utf-8")
        plan = plan_relocation(root, "treaty_docs")
        self.assertTrue(any("already exists" in b for b in plan.blockers))

    # --- the move itself -------------------------------------------------

    def test_flat_to_nested_moves_docs_and_rewrites_links(self) -> None:
        root = self._project(".")
        apply_relocation(plan_relocation(root, "treaty_docs"))

        for name in MOVABLE:
            self.assertTrue((root / "treaty_docs" / name).exists(), name)
            self.assertFalse((root / name).exists(), f"{name} left behind")
        self.assertTrue((root / "treaty_docs" / "work_log_archive" / "README.md").exists())
        self.assertTrue((root / "AGENTS.md").exists(), "AGENTS.md must stay at root")
        self.assertTrue((root / "project_overview.md").exists())

        agents = (root / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("treaty_docs/work_log.md", agents)
        self.assertIn("treaty_docs/next_steps.md", agents)
        self.assertIn("treaty_docs/work_log_archive/", agents)

        conventions = (root / "treaty_docs" / "treaty_conventions.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("../AGENTS.md", conventions)
        self.assertIn("../project_overview.md", conventions)

        answers = yaml.safe_load((root / ".copier-answers.yml").read_text(encoding="utf-8"))
        self.assertEqual("treaty_docs", answers["docs_dir"])

    def test_same_folder_links_survive_the_move_untouched(self) -> None:
        root = self._project(".")
        apply_relocation(plan_relocation(root, "treaty_docs"))
        archive = (root / "treaty_docs" / "work_log_archive" / "README.md").read_text(
            encoding="utf-8"
        )
        # The archive and the live log move together, so ../work_log.md stays right.
        self.assertIn("../work_log.md", archive)
        self.assertNotIn("treaty_docs/work_log.md", archive)

    def test_round_trip_restores_the_flat_layout(self) -> None:
        root = self._project(".")
        before = (root / "AGENTS.md").read_text(encoding="utf-8")
        apply_relocation(plan_relocation(root, "treaty_docs"))
        apply_relocation(plan_relocation(root, "."))

        for name in MOVABLE:
            self.assertTrue((root / name).exists(), name)
        self.assertFalse((root / "treaty_docs").exists(), "empty folder left behind")
        self.assertEqual(before, (root / "AGENTS.md").read_text(encoding="utf-8"))

    def test_multi_segment_target_gets_matching_link_depth(self) -> None:
        root = self._project(".")
        apply_relocation(plan_relocation(root, "docs/agents"))
        conventions = (root / "docs" / "agents" / "treaty_conventions.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("../../AGENTS.md", conventions)
        # The link has to resolve to the real file, not merely look plausible.
        self.assertTrue(
            (root / "docs" / "agents" / "../../AGENTS.md").resolve().is_file()
        )
        self.assertFalse((root / "docs" / "agents" / "AGENTS.md").exists())

    # --- outbound project links (issue #24) -----------------------------

    def _with_project_content(self, docs_dir: str = ".") -> Path:
        """A project whose treaty docs link *out* at its own files."""
        root = self._project(docs_dir)
        prefix = docs_prefix(docs_dir)
        rp = root_prefix(docs_dir)

        (root / "media").mkdir(exist_ok=True)
        (root / "media" / "README.md").write_text("# Media\n", encoding="utf-8")
        (root / "media" / "demo.png").write_bytes(b"\x89PNG\r\n")
        (root / "src").mkdir(exist_ok=True)
        (root / "src" / "app.py").write_text("x = 1\n", encoding="utf-8")

        (root / f"{prefix}next_steps.md").write_text(
            "# Next Steps\n\n## Currently Hot\n\n"
            f"- Assets in [`media/README.md`]({rp}media/README.md)\n"
            f"- Entry point [app]({rp}src/app.py) and ![demo]({rp}media/demo.png)\n"
            f"- Section link [anchor]({rp}media/README.md#usage)\n"
            "- Homepage <https://example.com/x.md> and [site](https://example.com/y.md)\n"
            "- Same-page [jump](#currently-hot) and absolute [abs](/etc/hosts)\n"
            "- Long gone [ghost](deleted/notes.md)\n\n"
            f"[assets]: {rp}media/README.md\n",
            encoding="utf-8",
        )
        _git(root, "add", "-A")
        _git(root, "-c", "user.email=t@e.st", "-c", "user.name=T", "commit", "-qm", "content")
        return root

    def test_outbound_project_links_gain_depth_on_the_way_in(self) -> None:
        root = self._with_project_content(".")
        apply_relocation(plan_relocation(root, "treaty_docs"))

        moved = root / "treaty_docs" / "next_steps.md"
        text = moved.read_text(encoding="utf-8")
        self.assertIn("(../media/README.md)", text)
        self.assertIn("(../src/app.py)", text)
        self.assertIn("(../media/demo.png)", text)
        self.assertIn("[assets]: ../media/README.md", text)
        # The link must resolve to the real file, not merely look plausible.
        self.assertTrue((moved.parent / "../media/README.md").resolve().is_file())

    def test_outbound_links_keep_their_anchors(self) -> None:
        root = self._with_project_content(".")
        apply_relocation(plan_relocation(root, "treaty_docs"))
        text = (root / "treaty_docs" / "next_steps.md").read_text(encoding="utf-8")
        self.assertIn("(../media/README.md#usage)", text)

    def test_outbound_links_match_multi_segment_depth(self) -> None:
        root = self._with_project_content(".")
        apply_relocation(plan_relocation(root, "docs/agents"))

        moved = root / "docs" / "agents" / "next_steps.md"
        text = moved.read_text(encoding="utf-8")
        self.assertIn("(../../media/README.md)", text)
        self.assertTrue((moved.parent / "../../media/README.md").resolve().is_file())

    def test_round_trip_restores_the_original_outbound_link(self) -> None:
        root = self._with_project_content(".")
        before = (root / "next_steps.md").read_text(encoding="utf-8")

        apply_relocation(plan_relocation(root, "treaty_docs"))
        # Assert the halfway state too, or "restored" is trivially true for a
        # round trip that never rewrote anything in the first place.
        moved = (root / "treaty_docs" / "next_steps.md").read_text(encoding="utf-8")
        self.assertIn("(../media/README.md)", moved)
        self.assertNotIn("(media/README.md)", moved)

        apply_relocation(plan_relocation(root, "."))
        self.assertEqual(before, (root / "next_steps.md").read_text(encoding="utf-8"))

    def test_leaves_links_a_move_cannot_invalidate(self) -> None:
        root = self._with_project_content(".")
        apply_relocation(plan_relocation(root, "treaty_docs"))
        text = (root / "treaty_docs" / "next_steps.md").read_text(encoding="utf-8")

        self.assertIn("<https://example.com/x.md>", text)
        self.assertIn("(https://example.com/y.md)", text)
        self.assertIn("(#currently-hot)", text)
        self.assertIn("(/etc/hosts)", text)
        # Already broken before the move: not ours to guess at.
        self.assertIn("(deleted/notes.md)", text)

    def test_dry_run_reports_outbound_links_before_applying(self) -> None:
        root = self._with_project_content(".")
        plan = plan_relocation(root, "treaty_docs")

        self.assertEqual(
            [(root / "next_steps.md", 5)],
            plan.outbound_edits,
            "the dry run must name the outbound links it will retarget",
        )
        rendered = "\n".join(format_plan(plan))
        self.assertIn("Project links inside the moved docs", rendered)
        self.assertIn("next_steps.md (5 link(s))", rendered)
        # Planning writes nothing.
        self.assertIn("media/README.md", (root / "next_steps.md").read_text(encoding="utf-8"))

    def test_relocation_uses_git_mv_so_history_follows(self) -> None:
        root = self._project(".")
        apply_relocation(plan_relocation(root, "treaty_docs"))
        status = _git(root, "status", "--porcelain").stdout
        self.assertIn("R", status, f"expected renames, got:\n{status}")

    def test_noop_when_already_in_the_target_layout(self) -> None:
        root = self._project("treaty_docs")
        plan = plan_relocation(root, "treaty_docs")
        self.assertTrue(plan.is_noop)
        self.assertEqual([], plan.moves)

    def test_relocated_project_still_validates(self) -> None:
        root = self._project(".")
        apply_relocation(plan_relocation(root, "treaty_docs"))
        self.assertEqual([], validate_project(root))

    def test_case_only_rename_is_refused_with_one_clear_message(self) -> None:
        """Reported from the Windows sweep on #21.

        On a case-insensitive filesystem `treaty_docs` and `Treaty_Docs` are one
        directory, so every destination looked occupied and the planner emitted
        four "already exists" blockers for what is a single unsupported
        operation. Nothing was ever mutated; the message was the defect.
        """
        root = self._project("treaty_docs")
        if not (root / "TREATY_DOCS").is_dir():
            self.skipTest("case-sensitive filesystem; case-only rename is a real move")

        plan = plan_relocation(root, "Treaty_Docs")
        self.assertEqual(1, len(plan.blockers), plan.blockers)
        self.assertIn("case-only rename", plan.blockers[0])
        self.assertFalse(plan.answers_update)
        self.assertEqual([], plan.moves)
        with self.assertRaises(ValueError):
            apply_relocation(plan)
        self.assertTrue((root / "treaty_docs" / "work_log.md").exists())

    def test_a_genuine_rename_still_works(self) -> None:
        root = self._project("treaty_docs")
        apply_relocation(plan_relocation(root, "other_docs"))
        self.assertTrue((root / "other_docs" / "work_log.md").exists())
        self.assertFalse((root / "treaty_docs").exists())

    # --- the things it cannot fix itself ---------------------------------

    def test_reports_references_it_does_not_own(self) -> None:
        root = self._project(".")
        (root / "CONTRIBUTING.md").write_text(
            "Update `work_log.md` and `next_steps.md` before handoff.\n", encoding="utf-8"
        )
        _git(root, "add", "-A")
        _git(root, "-c", "user.email=t@e.st", "-c", "user.name=T", "commit", "-qm", "c")

        plan = plan_relocation(root, "treaty_docs")
        named = {p.name for p, _ in plan.external_refs}
        self.assertIn("CONTRIBUTING.md", named)

        apply_relocation(plan)
        # Reported, deliberately not rewritten: it is not a treaty-owned doc.
        self.assertIn(
            "`work_log.md`", (root / "CONTRIBUTING.md").read_text(encoding="utf-8")
        )

    def test_detects_a_deny_all_gitignore_that_stops_matching(self) -> None:
        root = self._project(".")
        (root / ".gitignore").write_text(
            "*\n!.gitignore\n!AGENTS.md\n!project_overview.md\n!next_steps.md\n"
            "!work_log.md\n!treaty_conventions.md\n!work_log_archive/\n"
            "work_log_archive/*\n!work_log_archive/*.md\n",
            encoding="utf-8",
        )
        _git(root, "add", "-A")
        _git(root, "-c", "user.email=t@e.st", "-c", "user.name=T", "commit", "-qm", "ig")

        plan = plan_relocation(root, "treaty_docs")
        self.assertTrue(plan.gitignore_risk, "should warn that the move breaks tracking")
        self.assertTrue(any("treaty_docs" in risk for risk in plan.gitignore_risk))

    def test_validate_catches_the_ignored_layout_afterwards(self) -> None:
        """relocate warns at the time; validate has to keep catching it."""
        root = self._project(".")
        (root / ".gitignore").write_text(
            "*\n!.gitignore\n!AGENTS.md\n!project_overview.md\n!next_steps.md\n"
            "!work_log.md\n!treaty_conventions.md\n!work_log_archive/\n"
            "work_log_archive/*\n!work_log_archive/*.md\n",
            encoding="utf-8",
        )
        _git(root, "add", "-A")
        _git(root, "-c", "user.email=t@e.st", "-c", "user.name=T", "commit", "-qm", "ig")

        # A deliberate deny-all allowlist is fine while the docs are flat.
        self.assertEqual(
            [], [i for i in validate_project(root) if i.code == "treaty-doc-gitignored"]
        )

        apply_relocation(plan_relocation(root, "treaty_docs"))
        codes = [i.code for i in validate_project(root)]
        self.assertIn("treaty-doc-gitignored", codes)

        with (root / ".gitignore").open("a", encoding="utf-8") as fh:
            fh.write("!treaty_docs/\n!treaty_docs/**\n")
        self.assertEqual(
            [], [i for i in validate_project(root) if i.code == "treaty-doc-gitignored"]
        )


if __name__ == "__main__":
    unittest.main()
