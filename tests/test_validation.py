import asyncio
import copy
import json
import unittest

from pathlight.resources import load_lesson, load_student
from pathlight.schemas import TeacherDeliverable, validate_deliverable
from pathlight.tools.registry import dispatch_tool

STUDENT_ID = "35110GST"
LESSON_ID = "community"
Q1_TEXT = "Which best describes the author’s main purpose in writing the article?"

# Fully grounded draft: every accommodation referenced, valid phase + question.
GOOD = {
    "student_id": STUDENT_ID,
    "lesson_id": LESSON_ID,
    "before_class_checklist": [
        {"action": "Print large-font cards", "accommodation_ref": "acc_01 (p.18)"},
        {"action": "Pre-load notes copy", "accommodation_ref": "acc_02 (p.18)"},
        {"action": "Set up quiet seating", "accommodation_ref": "acc_03 (p.18)"},
        {"action": "Prepare manipulatives", "accommodation_ref": "acc_04 (p.18)"},
    ],
    "by_phase": [
        {
            "phase_id": "intro",
            "teacher_actions": ["Pre-teach the word 'community'"],
            "scaffolded_questions": [
                {
                    "question_id": "q1",
                    "original": Q1_TEXT,
                    "scaffolded": "What is one reason the author wrote this?",
                }
            ],
            "accommodation_reminders": [
                {"label": "Repeat directions", "source": "acc_01 (p.18)"}
            ],
        }
    ],
}


def _mutate(**_):
    return copy.deepcopy(GOOD)


def _validate(payload):
    deliverable = TeacherDeliverable.model_validate(payload)
    return validate_deliverable(deliverable, load_student(STUDENT_ID), load_lesson(LESSON_ID))


class ValidationHappyPathTests(unittest.TestCase):
    def test_fully_grounded_draft_passes_with_no_issues(self) -> None:
        report = _validate(GOOD)
        self.assertTrue(report.ok, msg=str(report.issues))
        self.assertEqual(report.error_count, 0)
        self.assertEqual(report.warning_count, 0)


class GroundingTests(unittest.TestCase):
    def test_ungrounded_accommodation_ref_is_error(self) -> None:
        bad = _mutate()
        bad["before_class_checklist"][0]["accommodation_ref"] = "acc_99 (p.18)"
        report = _validate(bad)
        self.assertFalse(report.ok)
        codes = {i.code for i in report.issues}
        self.assertIn("ungrounded_accommodation_ref", codes)

    def test_page_mismatch_is_warning_not_error(self) -> None:
        bad = _mutate()
        bad["before_class_checklist"][0]["accommodation_ref"] = "acc_01 (p.99)"
        report = _validate(bad)
        self.assertTrue(report.ok)  # still grounded; page is advisory
        codes = {i.code for i in report.issues}
        self.assertIn("accommodation_page_mismatch", codes)


class LessonReferenceTests(unittest.TestCase):
    def test_unknown_question_id_is_error(self) -> None:
        bad = _mutate()
        bad["by_phase"][0]["scaffolded_questions"][0]["question_id"] = "q99"
        report = _validate(bad)
        self.assertFalse(report.ok)
        self.assertIn("unknown_question_id", {i.code for i in report.issues})

    def test_question_text_mismatch_is_warning(self) -> None:
        bad = _mutate()
        bad["by_phase"][0]["scaffolded_questions"][0]["original"] = "totally different"
        report = _validate(bad)
        self.assertTrue(report.ok)
        self.assertIn("question_text_mismatch", {i.code for i in report.issues})

    def test_unknown_phase_id_is_error(self) -> None:
        bad = _mutate()
        bad["by_phase"][0]["phase_id"] = "not_a_phase"
        report = _validate(bad)
        self.assertFalse(report.ok)
        self.assertIn("unknown_phase_id", {i.code for i in report.issues})


class CoverageTests(unittest.TestCase):
    def test_uncovered_accommodations_is_warning(self) -> None:
        bad = _mutate()
        # Drop refs for acc_02/03/04, keep only acc_01.
        bad["before_class_checklist"] = [bad["before_class_checklist"][0]]
        report = _validate(bad)
        self.assertTrue(report.ok)  # coverage is advisory
        uncovered = [i for i in report.issues if i.code == "uncovered_accommodations"]
        self.assertEqual(len(uncovered), 1)
        self.assertEqual(set(uncovered[0].expected), {"acc_02", "acc_03", "acc_04"})


class InstructionalContextToolTests(unittest.TestCase):
    def test_returns_grounded_scoped_payload(self) -> None:
        result = asyncio.run(
            dispatch_tool(
                ctx=None,
                name="get_instructional_context",
                arguments={
                    "student_id": STUDENT_ID,
                    "lesson_id": LESSON_ID,
                    "phase_id": "intro",
                },
            )
        )
        payload = json.loads(result[0].text)
        self.assertEqual(payload["phase_id"], "intro")
        self.assertIn("formative_checks", payload)
        core = payload["student_instructional_core"]
        # Real accommodation labels must be present (not just ids), so Claude can
        # ground the draft instead of inventing generic text.
        labels = " ".join(a["label"] for a in core["accommodations"])
        self.assertIn("Repeat directions", labels)


class ValidateToolDispatchTests(unittest.TestCase):
    def test_tool_returns_structured_report(self) -> None:
        result = asyncio.run(
            dispatch_tool(ctx=None, name="validate_teacher_artifact", arguments=GOOD)
        )
        report = json.loads(result[0].text)
        self.assertTrue(report["ok"])
        self.assertIn("issues", report)
        self.assertEqual(report["error_count"], 0)


if __name__ == "__main__":
    unittest.main()
