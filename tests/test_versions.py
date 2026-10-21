from __future__ import annotations

import unittest

from agent_collab_treaty.versions import cli_older_than, parse_version


class VersionTests(unittest.TestCase):
    def test_parse_reads_tags_describe_strings_and_bare_versions(self) -> None:
        self.assertEqual((0, 9, 0), parse_version("v0.9.0"))
        self.assertEqual((0, 9, 0), parse_version("0.9.0"))
        self.assertEqual((0, 7, 0), parse_version("v0.7.0-12-g462ff24"))
        self.assertEqual((1, 2, 0), parse_version("v1.2"))

    def test_parse_gives_up_on_anything_else(self) -> None:
        for value in ("abc1234", "main", "", None, 7):
            with self.subTest(value=value):
                self.assertIsNone(parse_version(value))

    def test_older_cli_is_detected_numerically_not_lexically(self) -> None:
        self.assertTrue(cli_older_than("v0.10.0", cli_version="0.9.0"))
        self.assertTrue(cli_older_than("v0.9.0", cli_version="0.3.1"))
        self.assertFalse(cli_older_than("v0.9.0", cli_version="0.9.0"))
        self.assertFalse(cli_older_than("v0.9.0-4-gabc", cli_version="0.9.0"))
        self.assertFalse(cli_older_than("v0.3.1", cli_version="0.9.0"))
        self.assertFalse(cli_older_than("deadbeef", cli_version="0.9.0"))


if __name__ == "__main__":
    unittest.main()
