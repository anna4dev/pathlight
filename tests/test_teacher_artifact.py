import asyncio
import json
import unittest

from pydantic import ValidationError

from src.pathlight.schemas import TeacherDeliverable, render_teacher_markdown
from src.pathlight.tools.registry import dispatch_tool


SAMPLE = {
    "student_id": "stu_01",
    "lesson_id": "community",
    "before_class_checklist": [
        {"action": "Print large-font question cards", "accommodation_ref": "acc_01 (p.18)"},
        {"action": "Set up quiet seating"},
    ],
    "by_phase": [
        {
            "phase_id": "warm_up",
            "teacher_actions": ["Pre-teach the word 'community'"],
            "scaffolded_questions": [
                {
                    "question_id": "q1",
                    "original": "Why are communities important?",
                    "scaffolded": "Name one way your community helps you.",
                }
            ],
            "accommodation_reminders": [
                {"label": "Extra processing time", "source": "acc_02 (p.19)"}
            ],
        }
    ],
}


class TeacherDeliverableSchemaTests(unittest.TestCase):
    def test_parses_valid_payload(self) -> None:
        deliverable = TeacherDeliverable.model_validate(SAMPLE)
        self.assertEqual(deliverable.student_id, "stu_01")
        self.assertEqual(len(deliverable.by_phase), 1)
        self.assertEqual(deliverable.by_phase[0].scaffolded_questions[0].question_id, "q1")

    def test_optional_refs_default_to_none(self) -> None:
        deliverable = TeacherDeliverable.model_validate(SAMPLE)
        self.assertIsNone(deliverable.before_class_checklist[1].accommodation_ref)

    def test_rejects_missing_leaf_field(self) -> None:
        # scaffolded_questions require question_id/original/scaffolded.
        bad = json.loads(json.dumps(SAMPLE))
        del bad["by_phase"][0]["scaffolded_questions"][0]["question_id"]
        with self.assertRaises(ValidationError):
            TeacherDeliverable.model_validate(bad)

    def test_rejects_omitted_top_level_sections(self) -> None:
        # Omitted structural sections must error, not default to [].
        for key in ("before_class_checklist", "by_phase"):
            bad = json.loads(json.dumps(SAMPLE))
            del bad[key]
            with self.assertRaises(ValidationError, msg=f"omitting {key} should fail"):
                TeacherDeliverable.model_validate(bad)

    def test_rejects_omitted_phase_sections(self) -> None:
        for key in ("teacher_actions", "scaffolded_questions", "accommodation_reminders"):
            bad = json.loads(json.dumps(SAMPLE))
            del bad["by_phase"][0][key]
            with self.assertRaises(ValidationError, msg=f"omitting phase.{key} should fail"):
                TeacherDeliverable.model_validate(bad)

    def test_rejects_unknown_top_level_key(self) -> None:
        bad = json.loads(json.dumps(SAMPLE))
        bad["unexpected"] = "x"
        with self.assertRaises(ValidationError):
            TeacherDeliverable.model_validate(bad)

    def test_rejects_unknown_nested_key(self) -> None:
        # Misspelled / unexpected keys on nested objects must not be silently dropped.
        bad = json.loads(json.dumps(SAMPLE))
        bad["by_phase"][0]["scaffold_questions"] = []  # typo of scaffolded_questions
        with self.assertRaises(ValidationError):
            TeacherDeliverable.model_validate(bad)

    def test_rejects_coerced_types(self) -> None:
        # strict=True: an int must not be coerced into a string field.
        bad = json.loads(json.dumps(SAMPLE))
        bad["by_phase"][0]["scaffolded_questions"][0]["question_id"] = 1
        with self.assertRaises(ValidationError):
            TeacherDeliverable.model_validate(bad)

    def test_empty_sections_are_allowed_when_present(self) -> None:
        # Emptiness is a semantic concern (Phase 5), not a schema error.
        ok = json.loads(json.dumps(SAMPLE))
        ok["by_phase"][0]["scaffolded_questions"] = []
        ok["by_phase"][0]["accommodation_reminders"] = []
        deliverable = TeacherDeliverable.model_validate(ok)
        self.assertEqual(deliverable.by_phase[0].scaffolded_questions, [])


class RendererTests(unittest.TestCase):
    def test_rendering_is_deterministic(self) -> None:
        deliverable = TeacherDeliverable.model_validate(SAMPLE)
        first = render_teacher_markdown(deliverable)
        second = render_teacher_markdown(deliverable)
        self.assertEqual(first, second)

    def test_rendering_contains_grounded_content(self) -> None:
        deliverable = TeacherDeliverable.model_validate(SAMPLE)
        md = render_teacher_markdown(deliverable)
        self.assertIn("# Teacher Lesson Adaptation", md)
        self.assertIn("- [ ] Print large-font question cards  (acc_01 (p.18))", md)
        self.assertIn("- [ ] Set up quiet seating", md)
        self.assertIn("## Phase: warm_up", md)
        self.assertIn("[q1] Why are communities important?", md)
        self.assertIn("Extra processing time  (acc_02 (p.19))", md)

    def test_action_without_ref_has_no_suffix(self) -> None:
        deliverable = TeacherDeliverable.model_validate(SAMPLE)
        md = render_teacher_markdown(deliverable)
        self.assertIn("- [ ] Set up quiet seating\n", md)


class RenderToolDispatchTests(unittest.TestCase):
    def test_render_tool_returns_markdown_and_json(self) -> None:
        result = asyncio.run(dispatch_tool(ctx=None, name="render_teacher_artifact", arguments=SAMPLE))
        self.assertEqual(len(result), 1)
        payload = json.loads(result[0].text)
        self.assertIn("rendered_markdown", payload)
        self.assertIn("deliverable", payload)
        self.assertIn("# Teacher Lesson Adaptation", payload["rendered_markdown"])
        self.assertEqual(payload["deliverable"]["student_id"], "stu_01")


if __name__ == "__main__":
    unittest.main()
