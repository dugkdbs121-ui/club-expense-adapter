"""예상·실제, 파일 상태, 구조 개선 전후의 동일성을 검사한다."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory

OLD_OUTPUT = '{"previous": "기존 저장 결과"}\n'.encode("utf-8")


def run_case(version_name, run_text, case):
    expected = {"result": case["expected"], "error": case["error"]}
    actual = {"result": None, "error": None}
    checks = {}

    with TemporaryDirectory() as directory:
        folder = Path(directory)
        input_path = folder / "input.csv"
        output_path = folder / "result.json"
        original_input = case["text"].encode("utf-8")
        input_path.write_bytes(original_input)
        output_path.write_bytes(OLD_OUTPUT)
        text = input_path.read_text(encoding="utf-8")

        try:
            actual["result"] = run_text(text, case["format"], output_path)
        except ValueError as error:
            actual["error"] = str(error)
        except Exception as error:
            actual["error"] = type(error).__name__ + ": " + str(error)

        checks["expected_matches_actual"] = actual == expected
        checks["input_file_unchanged"] = input_path.read_bytes() == original_input

        if case["error"] is None:
            expected_file = json.dumps(case["expected"], ensure_ascii=False, indent=2) + "\n"
            saved_file = output_path.read_bytes()
            checks["saved_json_matches_expected"] = saved_file == expected_file.encode("utf-8")
        else:
            saved_file = output_path.read_bytes()
            checks["previous_output_preserved"] = saved_file == OLD_OUTPUT
            absent_path = folder / "not_created.json"
            second_error = None
            try:
                run_text(text, case["format"], absent_path)
            except ValueError as error:
                second_error = str(error)
            except Exception as error:
                second_error = type(error).__name__ + ": " + str(error)
            checks["no_file_created_on_error"] = not absent_path.exists()
            checks["same_error_without_previous_file"] = second_error == case["error"]

        passed = True
        for value in checks.values():
            if not value:
                passed = False

        return {
            "case_id": case["id"],
            "case_name": case["name"],
            "version": version_name,
            "format": case["format"],
            "expected": expected,
            "actual": actual,
            "checks": checks,
            "passed": passed,
            "saved_file_text": saved_file.decode("utf-8"),
        }


def compare_existing_results(results, cases):
    """오류 메시지와 파일 내용까지 포함해 기존 입력의 동작 보존을 비교한다."""
    comparisons = []
    for case in cases:
        selected = []
        for result in results:
            if result["case_id"] == case["id"]:
                selected.append(result)
        same = len(selected) == 3
        first = selected[0]
        for result in selected:
            if result["actual"] != first["actual"]:
                same = False
            if result["saved_file_text"] != first["saved_file_text"]:
                same = False
        comparisons.append({"case_id": case["id"], "three_versions_identical": same})
    return comparisons


def describe(value):
    if value["error"] is not None:
        return "오류: " + value["error"]
    result = value["result"]
    return str(result["count"]) + "건 / " + format(result["total"], ",") + "원"


def write_evidence(project_dir, report):
    directory = project_dir / "evidence"
    directory.mkdir(exist_ok=True)
    data = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    (directory / "test_results.json").write_text(data, encoding="utf-8")

    lines = [
        "# 실제 검사 결과",
        "",
        "실행 시각(한국): " + report["executed_at_kst"],
        "",
        "Python: " + report["python_version"],
        "",
        "예상값은 tests/cases.py의 독립 상수이다. 실제값은 세 버전의 run_text를 실행해 기록했다.",
        "같은 임시 입력과 같은 기존 결과 파일에서 시작한다. 오류가 나면 기존 결과가 보존되고, 새 결과 파일도 생성되지 않는지 확인한다.",
        "이 파일은 검사 도구의 실행 기록이며, 학생 본인의 독립적인 예측·실행 이력을 대신하지 않는다.",
        "",
        "| 사례 | 버전 | 예상 | 실제 | 결과 |",
        "| --- | --- | --- | --- | --- |",
    ]
    for item in report["results"]:
        state = "통과" if item["passed"] else "실패"
        lines.append("| " + item["case_id"] + " " + item["case_name"] + " | " + item["version"] +
                     " | " + describe(item["expected"]) + " | " + describe(item["actual"]) + " | " + state + " |")
    lines.extend(["", "## 기존 입력의 동작 보존", ""])
    for item in report["comparisons"]:
        state = "동일" if item["three_versions_identical"] else "불일치"
        lines.append("- " + item["case_id"] + ": 결과·오류 메시지·저장 파일이 세 버전에서 " + state)
    lines.extend([
        "",
        "## 의도된 기능 변화",
        "",
        "X1~X3의 bank 양식은 기본판·구조 개선판에서 지원하지 않는다. 기능 변경판에서만 bank 변환을 지원한다.",
        "X1은 정상 집계로 바뀌고, X2·X3은 새 양식에 맞는 금액·날짜 검사 오류로 바뀐다.",
        "기존 N1~E10 사례는 기능 변경 뒤에도 다시 실행하여 같은 결과를 확인한다.",
        "",
        "전체 통과: " + str(report["all_passed"]),
        "",
        "각 분류별 합계와 파일 상태의 세부 검사는 test_results.json에서 확인할 수 있다.",
    ])
    (directory / "test_results.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
