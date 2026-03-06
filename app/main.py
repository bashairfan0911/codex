import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from app.repository import LeaveRepository
from app.service import LeaveService

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"

repository = LeaveRepository(str(BASE_DIR / "data" / "approviq.db"))
service = LeaveService(repository)


class AppHandler(BaseHTTPRequestHandler):
    def _send_json(self, payload: dict, status: int = HTTPStatus.OK) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json_body(self) -> dict:
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        raw = self.rfile.read(length).decode("utf-8")
        return json.loads(raw)

    def _serve_file(self, file_path: Path) -> None:
        if not file_path.exists():
            self.send_error(HTTPStatus.NOT_FOUND)
            return

        content_type = "text/html"
        if file_path.suffix == ".css":
            content_type = "text/css"
        elif file_path.suffix == ".js":
            content_type = "application/javascript"

        data = file_path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self._serve_file(STATIC_DIR / "index.html")
            return

        if parsed.path == "/styles.css":
            self._serve_file(STATIC_DIR / "styles.css")
            return

        if parsed.path == "/app.js":
            self._serve_file(STATIC_DIR / "app.js")
            return

        if parsed.path == "/api/requests":
            self._send_json({"data": service.list_requests()})
            return

        self.send_error(HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)

        try:
            payload = self._read_json_body()
            if parsed.path == "/api/requests":
                created = service.submit_request(payload)
                self._send_json({"data": created}, status=HTTPStatus.CREATED)
                return

            if parsed.path.startswith("/api/requests/") and parsed.path.endswith("/decision"):
                parts = parsed.path.strip("/").split("/")
                request_id = int(parts[2])
                updated = service.take_action(
                    request_id=request_id,
                    role=payload.get("role", ""),
                    action=payload.get("action", ""),
                    comment=payload.get("comment", ""),
                )
                self._send_json({"data": updated})
                return

            self.send_error(HTTPStatus.NOT_FOUND)
        except ValueError as err:
            self._send_json({"error": str(err)}, status=HTTPStatus.BAD_REQUEST)
        except json.JSONDecodeError:
            self._send_json({"error": "Invalid JSON payload"}, status=HTTPStatus.BAD_REQUEST)


def run(port: int = 8000) -> None:
    server = ThreadingHTTPServer(("0.0.0.0", port), AppHandler)
    print(f"ApprovIQ server running on http://localhost:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run()
