import os
import unittest
from unittest import mock

from src.pathlight.tools.registry import build_tools, legacy_tools_enabled


class ToolGatingTests(unittest.TestCase):
    def test_default_disables_legacy_tools(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertFalse(legacy_tools_enabled())
            self.assertEqual(build_tools(), [])

    def test_flag_enables_legacy_tools(self) -> None:
        with mock.patch.dict(os.environ, {"PATHLIGHT_ENABLE_LEGACY_TOOLS": "1"}, clear=True):
            self.assertTrue(legacy_tools_enabled())
            names = {tool.name for tool in build_tools()}
            self.assertIn("generate_instructional_plan", names)

    def test_flag_accepts_truthy_words(self) -> None:
        for value in ("true", "YES", "on"):
            with mock.patch.dict(os.environ, {"PATHLIGHT_ENABLE_LEGACY_TOOLS": value}, clear=True):
                self.assertTrue(legacy_tools_enabled())


if __name__ == "__main__":
    unittest.main()
