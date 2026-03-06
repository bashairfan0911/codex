from datetime import datetime, timezone
from typing import Any

from app.repository import LeaveRepository


ROLE_SEQUENCE = ["advisor", "hod", "principal"]


class LeaveService:
    def __init__(self, repository: LeaveRepository) -> None:
        self.repository = repository

    def submit_request(self, payload: dict[str, Any]) -> dict[str, Any]:
        required = ["student_name", "reason", "from_date", "to_date"]
        missing = [field for field in required if not payload.get(field)]
        if missing:
            raise ValueError(f"Missing fields: {', '.join(missing)}")

        data = {
            **payload,
            "status": "pending_advisor",
            "advisor_status": "pending",
            "hod_status": "pending",
            "principal_status": "pending",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        request_id = self.repository.create_request(data)
        return self.get_request_with_history(request_id)

    def list_requests(self) -> list[dict[str, Any]]:
        requests = self.repository.list_requests()
        for item in requests:
            item["decisions"] = self.repository.list_decisions(item["id"])
        return requests

    def get_request_with_history(self, request_id: int) -> dict[str, Any]:
        leave_request = self.repository.get_request(request_id)
        if not leave_request:
            raise ValueError("Request not found")
        leave_request["decisions"] = self.repository.list_decisions(request_id)
        return leave_request

    def take_action(self, request_id: int, role: str, action: str, comment: str = "") -> dict[str, Any]:
        role = role.lower().strip()
        action = action.lower().strip()

        if role not in ROLE_SEQUENCE:
            raise ValueError("Invalid role")
        if action not in {"approve", "reject"}:
            raise ValueError("Invalid action")

        leave_request = self.repository.get_request(request_id)
        if not leave_request:
            raise ValueError("Request not found")
        if leave_request["status"] in {"approved", "rejected"}:
            raise ValueError("Request already finalized")

        expected_role = self._next_pending_role(leave_request)
        if role != expected_role:
            raise ValueError(f"Only {expected_role} can act at this stage")

        updates: dict[str, str] = {f"{role}_status": action}
        if action == "reject":
            updates["status"] = "rejected"
        elif role == "principal":
            updates["status"] = "approved"
        else:
            next_role = ROLE_SEQUENCE[ROLE_SEQUENCE.index(role) + 1]
            updates["status"] = f"pending_{next_role}"

        self.repository.update_request_status(request_id, updates)
        self.repository.add_decision(
            request_id=request_id,
            role=role,
            action=action,
            comment=comment,
            decided_at=datetime.now(timezone.utc).isoformat(),
        )
        return self.get_request_with_history(request_id)

    def _next_pending_role(self, leave_request: dict[str, Any]) -> str:
        for role in ROLE_SEQUENCE:
            if leave_request[f"{role}_status"] == "pending":
                return role
        return "principal"
