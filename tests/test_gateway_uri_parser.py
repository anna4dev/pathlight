import json
import unittest

from src.pathlight.resources.gateway import list_resource_catalog, read_resource_payload


class GatewayUriParserTests(unittest.TestCase):
    STUDENT_ID = "35110GST"
    LESSON_ID = "community"

    def test_overview_resource_contains_grounding_fields(self) -> None:
        payload = read_resource_payload(f"lesson://{self.LESSON_ID}/overview")
        data = json.loads(payload)

        for key in (
            "grade",
            "subject",
            "unit_topic",
            "duration_minutes",
            "instructional_objective_summary",
        ):
            self.assertIn(key, data)

    def test_instructional_core_scope_excludes_dob(self) -> None:
        payload = read_resource_payload(f"student://{self.STUDENT_ID}/scopes/instructional_core")
        data = json.loads(payload)
        self.assertIn("profile", data)
        self.assertNotIn("dob", data["profile"])

    def test_question_resource_uses_id_lookup(self) -> None:
        payload = read_resource_payload(f"lesson://{self.LESSON_ID}/questions/q1")
        data = json.loads(payload)
        self.assertEqual(data["question_id"], "q1")
        self.assertIn("question", data)

    def test_terminal_student_profile_rejects_extra_segments(self) -> None:
        with self.assertRaises(ValueError):
            read_resource_payload(f"student://{self.STUDENT_ID}/profile/extra")

    def test_terminal_lesson_overview_rejects_extra_segments(self) -> None:
        with self.assertRaises(ValueError):
            read_resource_payload(f"lesson://{self.LESSON_ID}/overview/extra")

    def test_terminal_lesson_full_rejects_extra_segments(self) -> None:
        with self.assertRaises(ValueError):
            read_resource_payload(f"lesson://{self.LESSON_ID}/full/extra")

    def test_resource_catalog_contains_segmented_uris(self) -> None:
        uris = {str(resource.uri) for resource in list_resource_catalog()}
        self.assertIn(f"student://{self.STUDENT_ID}/scopes/instructional_core", uris)
        self.assertIn(f"lesson://{self.LESSON_ID}/questions/q1", uris)

    def test_instructional_phase_scope_bundles_phase_questions_and_accommodations(self) -> None:
        uri = f"student://{self.STUDENT_ID}/scopes/lesson/{self.LESSON_ID}/phase/intro"
        data = json.loads(read_resource_payload(uri))

        self.assertEqual(data["student_id"], self.STUDENT_ID)
        self.assertEqual(data["lesson_id"], self.LESSON_ID)
        self.assertEqual(data["phase_id"], "intro")
        self.assertEqual(data["phase"]["phase_id"], "intro")

        self.assertIn("accommodations", data["student_instructional_core"])
        self.assertEqual(data["formative_checks"][0]["question_id"], "q1")

    def test_instructional_phase_scope_rejects_unknown_phase(self) -> None:
        uri = f"student://{self.STUDENT_ID}/scopes/lesson/{self.LESSON_ID}/phase/nope"
        with self.assertRaises(ValueError):
            read_resource_payload(uri)

    def test_resource_catalog_contains_instructional_phase_scope(self) -> None:
        uris = {str(resource.uri) for resource in list_resource_catalog()}
        self.assertIn(
            f"student://{self.STUDENT_ID}/scopes/lesson/{self.LESSON_ID}/phase/intro",
            uris,
        )


if __name__ == "__main__":
    unittest.main()
