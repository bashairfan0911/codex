import tempfile
import unittest
from pathlib import Path

from app.repository import LeaveRepository
from app.service import LeaveService


class WorkflowTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        db_path = Path(self.temp_dir.name) / "test.db"
        self.repo = LeaveRepository(str(db_path))
        self.service = LeaveService(self.repo)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_happy_path_approval(self) -> None:
        created = self.service.submit_request(
            {
                "student_name": "Asha",
                "reason": "Medical",
                "from_date": "2026-03-10",
                "to_date": "2026-03-11",
            }
        )
        request_id = created["id"]

        step_1 = self.service.take_action(request_id, "advisor", "approve", "ok")
        self.assertEqual(step_1["status"], "pending_hod")

        step_2 = self.service.take_action(request_id, "hod", "approve", "ok")
        self.assertEqual(step_2["status"], "pending_principal")

        step_3 = self.service.take_action(request_id, "principal", "approve", "ok")
        self.assertEqual(step_3["status"], "approved")

    def test_sequence_enforced(self) -> None:
        created = self.service.submit_request(
            {
                "student_name": "Ravi",
                "reason": "Family event",
                "from_date": "2026-04-01",
                "to_date": "2026-04-02",
            }
        )
        with self.assertRaises(ValueError):
            self.service.take_action(created["id"], "hod", "approve", "skip")


if __name__ == "__main__":
    unittest.main()
