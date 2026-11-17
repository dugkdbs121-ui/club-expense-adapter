"""로컬 웹 화면을 파이썬 지출 처리 함수에 연결한다."""

import argparse
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from extended.service import run_text


PROJECT_DIR = Path(__file__).resolve().parent
MAX_UPLOAD_BYTES = 1024 * 1024
MAX_REQUEST_BYTES = MAX_UPLOAD_BYTES * 2 + 1024
FORMATS = ["club", "event", "bank"]
STATIC_FILES = {
    "/": ("static/index.html", "text/html; charset=utf-8"),
    "/static/styles.css": ("static/styles.css", "text/css; charset=utf-8"),
    "/static/app.js": ("static/app.js", "text/javascript; charset=utf-8"),
}
SAMPLE_FILES = ["club_normal.csv", "event_normal.csv", "bank_normal.csv"]


class ExpenseHandler(BaseHTTPRequestHandler):
    """HTTP 요청의 입력·출력을 맡고 계산은 서비스 함수에 위임한다."""

    def send_bytes(self, content, content_type, status=200, download=False):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy",
                         "default-src 'self'; object-src 'none'; frame-ancestors 'none'")
        if download:
            self.send_header("Content-Disposition", 'attachment; filename="expense_report.json"')
        self.end_headers()
        self.wfile.write(content)

    def send_json(self, data, status=200):
        content = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_bytes(content, "application/json; charset=utf-8", status)

    def send_file(self, path, content_type, download=False):
        try:
            content = path.read_bytes()
        except OSError:
            self.send_json({"ok": False, "error": "파일을 찾을 수 없습니다."}, 404)
            return
        self.send_bytes(content, content_type, download=download)

    def do_GET(self):
        path = urlsplit(self.path).path
        if path in STATIC_FILES:
            relative_path, content_type = STATIC_FILES[path]
            self.send_file(PROJECT_DIR / relative_path, content_type)
        elif path == "/download":
            self.send_file(self.server.output_path, "application/json; charset=utf-8", True)
        elif path.startswith("/samples/"):
            filename = path.removeprefix("/samples/")
            if filename not in SAMPLE_FILES:
                self.send_json({"ok": False, "error": "없는 예제 파일입니다."}, 404)
                return
            self.send_file(PROJECT_DIR / "examples" / filename, "text/csv; charset=utf-8")
        else:
            self.send_json({"ok": False, "error": "없는 주소입니다."}, 404)

    def read_request(self):
        content_type = self.headers.get("Content-Type", "").split(";")[0].strip()
        if content_type != "application/json":
            raise ValueError("JSON 형식으로 요청해 주세요.")
        try:
            size = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            raise ValueError("요청 크기가 올바르지 않습니다.") from None
        # JSON의 따옴표·줄바꿈 이스케이프에 필요한 여유를 둔다.
        if size <= 0 or size > MAX_REQUEST_BYTES:
            raise ValueError("요청 크기는 1MB 이하여야 합니다.")
        try:
            data = json.loads(self.rfile.read(size).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise ValueError("요청 내용을 읽을 수 없습니다.") from None
        if not isinstance(data, dict):
            raise ValueError("요청에는 CSV 내용과 양식이 필요합니다.")
        text = data.get("csv_text")
        format_name = data.get("format")
        if not isinstance(text, str) or not isinstance(format_name, str):
            raise ValueError("CSV 내용과 양식을 문자열로 보내 주세요.")
        if len(text.encode("utf-8")) > MAX_UPLOAD_BYTES:
            raise ValueError("CSV 파일 크기는 1MB 이하여야 합니다.")
        if format_name not in FORMATS:
            raise ValueError("지원하지 않는 CSV 양식입니다.")
        return text, format_name

    def do_POST(self):
        if urlsplit(self.path).path != "/api/analyze":
            self.send_json({"ok": False, "error": "없는 주소입니다."}, 404)
            return
        try:
            text, format_name = self.read_request()
            result = run_text(text, format_name, self.server.output_path)
        except ValueError as error:
            self.send_json({"ok": False, "error": str(error)}, 400)
            return
        except OSError:
            self.send_json({"ok": False, "error": "결과 파일을 저장하지 못했습니다. 출력 폴더를 확인해 주세요."}, 500)
            return
        self.send_json({"ok": True, "result": result})


def create_server(host="127.0.0.1", port=8765, output_path=None):
    """검사에서는 port=0과 임시 출력 경로를 지정할 수 있다."""
    server = HTTPServer((host, port), ExpenseHandler)
    if output_path is None:
        output_path = PROJECT_DIR / "outputs" / "latest_report.json"
    server.output_path = Path(output_path)
    return server


def main():
    parser = argparse.ArgumentParser(description="동아리 지출 정리 로컬 웹앱")
    parser.add_argument("--port", type=int, default=8765, help="접속 포트 (기본: 8765)")
    args = parser.parse_args()
    server = create_server(port=args.port)
    print(f"브라우저에서 http://127.0.0.1:{server.server_port} 를 여세요.")
    print("서버를 종료하려면 Ctrl+C를 누르세요.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n서버를 종료합니다.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
