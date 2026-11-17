"""실행: python check_all.py / 검사 기록: evidence/test_results.json, .md"""

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from baseline.main import run_text as run_baseline
from refactored.service import run_text as run_refactored
from extended.service import run_text as run_extended
from tests.cases import common_cases, new_format_cases
from tests.runner import run_case, compare_existing_results, write_evidence


def main():
    project_dir = Path(__file__).resolve().parent
    versions = [
        ("기본판", run_baseline),
        ("구조 개선판", run_refactored),
        ("기능 변경판", run_extended),
    ]
    cases = common_cases(project_dir)
    results = []
    for version_name, run_text in versions:
        for case in cases:
            results.append(run_case(version_name, run_text, case))

    comparisons = compare_existing_results(results, cases)
    for version_name, run_text in versions:
        for case in new_format_cases(project_dir):
            if version_name != "기능 변경판":
                case = case.copy()
                case["expected"] = None
                case["error"] = "지원하지 않는 양식입니다: bank"
            results.append(run_case(version_name, run_text, case))

    all_passed = True
    for item in results:
        if not item["passed"]:
            all_passed = False
    for item in comparisons:
        if not item["three_versions_identical"]:
            all_passed = False

    korea_time = timezone(timedelta(hours=9))
    report = {
        "executed_at_kst": datetime.now(korea_time).isoformat(timespec="seconds"),
        "python_version": sys.version.split()[0],
        "common_cases": len(cases),
        "total_case_version_runs": len(results),
        "results": results,
        "comparisons": comparisons,
        "all_passed": all_passed,
    }
    write_evidence(project_dir, report)
    for item in results:
        if not item["passed"]:
            print("실패:", item["case_id"], item["version"], item["actual"], item["checks"])
    print("기존", len(cases), "사례 × 3버전 + 새 양식 3사례 × 3버전 =", len(results), "회 검사")
    print("기존 입력의 결과·오류·저장 내용 동일:", all_passed)
    print("검사 기록: evidence/test_results.json, evidence/test_results.md")
    if not all_passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
