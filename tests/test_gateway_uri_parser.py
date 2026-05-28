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


if __name__ == "__main__":
    unittest.main()
