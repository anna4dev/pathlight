import os
import unittest
from unittest import mock

from pathlight.tools.registry import build_tools, legacy_tools_enabled


class ToolGatingTests(unittest.TestCase):
    def test_default_registers_only_shape_a_tools(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertFalse(legacy_tools_enabled())
            names = {tool.name for tool in build_tools()}
            self.assertEqual(
                names,
                {
                    "get_instructional_context",
                    "validate_teacher_artifact",
                    "render_teacher_artifact",
                },
            )

    def test_flag_enables_legacy_tools(self) -> None:
        with mock.patch.dict(os.environ, {"PATHLIGHT_ENABLE_LEGACY_TOOLS": "1"}, clear=True):
            self.assertTrue(legacy_tools_enabled())
            names = {tool.name for tool in build_tools()}
            self.assertIn("generate_instructional_plan", names)
            # Shape A tools remain available alongside legacy tools.
            self.assertIn("render_teacher_artifact", names)

    def test_flag_accepts_truthy_words(self) -> None:
        for value in ("true", "YES", "on"):
            with mock.patch.dict(os.environ, {"PATHLIGHT_ENABLE_LEGACY_TOOLS": value}, clear=True):
                self.assertTrue(legacy_tools_enabled())


if __name__ == "__main__":
    unittest.main()
