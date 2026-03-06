import sqlite3
from pathlib import Path
from typing import Any


class LeaveRepository:
    def __init__(self, db_path: str = "approviq.db") -> None:
        self.db_path = db_path
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS leave_requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_name TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    from_date TEXT NOT NULL,
                    to_date TEXT NOT NULL,
                    status TEXT NOT NULL,
                    advisor_status TEXT NOT NULL,
                    hod_status TEXT NOT NULL,
                    principal_status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS decisions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    leave_request_id INTEGER NOT NULL,
                    role TEXT NOT NULL,
                    action TEXT NOT NULL,
                    comment TEXT,
                    decided_at TEXT NOT NULL,
                    FOREIGN KEY(leave_request_id) REFERENCES leave_requests(id)
                )
                """
            )

    def create_request(self, payload: dict[str, Any]) -> int:
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO leave_requests (
                    student_name, reason, from_date, to_date, status,
                    advisor_status, hod_status, principal_status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["student_name"],
                    payload["reason"],
                    payload["from_date"],
                    payload["to_date"],
                    payload["status"],
                    payload["advisor_status"],
                    payload["hod_status"],
                    payload["principal_status"],
                    payload["created_at"],
                ),
            )
            return int(cursor.lastrowid)

    def list_requests(self) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM leave_requests ORDER BY id DESC"
            ).fetchall()
            return [dict(row) for row in rows]

    def get_request(self, request_id: int) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM leave_requests WHERE id = ?", (request_id,)
            ).fetchone()
            return dict(row) if row else None

    def update_request_status(self, request_id: int, fields: dict[str, Any]) -> None:
        columns = ", ".join([f"{key} = ?" for key in fields.keys()])
        values = list(fields.values()) + [request_id]
        with self._connect() as conn:
            conn.execute(
                f"UPDATE leave_requests SET {columns} WHERE id = ?",
                values,
            )

    def add_decision(self, request_id: int, role: str, action: str, comment: str, decided_at: str) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO decisions (leave_request_id, role, action, comment, decided_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (request_id, role, action, comment, decided_at),
            )

    def list_decisions(self, request_id: int) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT role, action, comment, decided_at
                FROM decisions
                WHERE leave_request_id = ?
                ORDER BY id ASC
                """,
                (request_id,),
            ).fetchall()
            return [dict(row) for row in rows]
