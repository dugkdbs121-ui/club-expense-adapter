"""실제 HTTP 요청으로 웹 연결과 저장·다운로드를 검사한다."""

import json
import sys
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from tests.cases import NORMAL_RESULT
from web_app import create_server


def request(url, data=None):
    if data is None:
        message = Request(url)
    else:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        message = Request(url, data=body, headers={"Content-Type": "application/json"})
    try:
        response = urlopen(message, timeout=5)
    except HTTPError as error:
        response = error
    with response:
        return response.status, response.read()


def main():
    root = Path(__file__).resolve().parent
    results = []
    with TemporaryDirectory() as directory:
        output = Path(directory) / "result.json"
        server = create_server(port=0, output_path=output)
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        url = "http://127.0.0.1:" + str(server.server_port)
        try:
            status, body = request(url + "/")
            results.append({"test": "웹 화면 열기", "passed": status == 200 and b"analysis-form" in body})
            status, body = request(url + "/download")
            results.append({"test": "실행 전 다운로드 없음", "passed": status == 404 and not output.exists()})
            for name in ["club", "event", "bank"]:
                text = (root / "examples" / (name + "_normal.csv")).read_text(encoding="utf-8")
                status, body = request(url + "/api/analyze", {"csv_text": text, "format": name})
                answer = json.loads(body)
                passed = status == 200 and answer == {"ok": True, "result": NORMAL_RESULT}
                results.append({"test": name + " 양식 API 처리", "passed": passed})
            status, body = request(url + "/download")
            saved = output.read_bytes()
            results.append({"test": "다운로드와 실제 저장 파일 일치", "passed": status == 200 and body == saved})
            invalid = (root / "examples" / "club_invalid_amount.csv").read_text(encoding="utf-8")
            status, body = request(url + "/api/analyze", {"csv_text": invalid, "format": "club"})
            answer = json.loads(body)
            results.append({"test": "잘못된 금액 오류와 이전 파일 보존", "passed": status == 400 and not answer["ok"] and output.read_bytes() == saved})
            status, body = request(url + "/api/analyze", {"csv_text": "x", "format": "unknown"})
            results.append({"test": "미지원 양식 거부", "passed": status == 400 and output.read_bytes() == saved})
            status, body = request(url + "/api/analyze", {"csv_text": "x" * (1024 * 1024 + 1), "format": "club"})
            results.append({"test": "1MB 초과 CSV 거부", "passed": status == 400 and output.read_bytes() == saved})
            status, body = request(url + "/samples/../README.md")
            results.append({"test": "허용하지 않은 파일 경로 거부", "passed": status == 404})
        finally:
            server.shutdown()
            server.server_close()
            worker.join(timeout=5)

    all_passed = True
    for item in results:
        print(item["test"], ":", item["passed"])
        if not item["passed"]:
            all_passed = False
    korea_time = timezone(timedelta(hours=9))
    report = {
        "executed_at_kst": datetime.now(korea_time).isoformat(timespec="seconds"),
        "python_version": sys.version.split()[0],
        "results": results,
        "all_passed": all_passed,
    }
    folder = root / "evidence"
    folder.mkdir(exist_ok=True)
    (folder / "web_test_results.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if not all_passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
