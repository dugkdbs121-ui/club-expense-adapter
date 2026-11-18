"""세 버전의 실제 명령행 실행과 원본 경로 보호를 확인한다."""

import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

from tests.cases import NORMAL_RESULT


def execute(module, source, destination, root):
    command = [
        sys.executable, "-m", module, str(source),
        "--format", "club", "--output", str(destination),
    ]
    environment = os.environ.copy()
    environment["PYTHONIOENCODING"] = "utf-8"
    return subprocess.run(
        command, cwd=root, env=environment, capture_output=True,
        text=True, encoding="utf-8", timeout=15,
    )


def main():
    root = Path(__file__).resolve().parent
    original = (root / "examples/club_normal.csv").read_bytes()
    results = []
    modules = ["baseline.main", "refactored.service", "extended.service"]
    with TemporaryDirectory() as directory:
        source = Path(directory) / "input.csv"
        for module in modules:
            source.write_bytes(original)
            destination = Path(directory) / (module + ".json")
            execution = execute(module, source, destination, root)
            saved = None
            if destination.exists():
                saved = json.loads(destination.read_text(encoding="utf-8"))
            passed = execution.returncode == 0 and saved == NORMAL_RESULT
            passed = passed and source.read_bytes() == original
            results.append({"test": module + " 정상 실행", "passed": passed})

            execution = execute(module, source, source, root)
            error = "입력 파일과 결과 저장 경로는 달라야 합니다."
            passed = execution.returncode == 1 and error in execution.stdout
            passed = passed and source.read_bytes() == original
            results.append({"test": module + " 동일 경로 거부·원본 보존", "passed": passed})

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
    (folder / "cli_test_results.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8",
    )
    if not all_passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
