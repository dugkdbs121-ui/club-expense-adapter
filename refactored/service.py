"""Adapter와 공통 검사·집계·저장을 연결한다."""

import argparse
import json
from pathlib import Path

from refactored.adapters import ClubAdapter, EventAdapter
from refactored.storage import read_rows, save_report
from refactored.summary import summarize
from refactored.validation import validate_records


ADAPTERS = {"club": ClubAdapter(), "event": EventAdapter()}


def run_with_adapter(text, adapter, output_path):
    rows = read_rows(text, adapter.required_columns)
    records = []
    for row_number, row in rows:
        records.append(adapter.adapt(row, row_number))
    validate_records(records, rows)
    report = summarize(records)
    save_report(report, output_path)
    return report


def run_text(text, format_name, output_path):
    if format_name not in ADAPTERS:
        raise ValueError("지원하지 않는 양식입니다: " + str(format_name))
    adapter = ADAPTERS[format_name]
    return run_with_adapter(text, adapter, output_path)


def main():
    parser = argparse.ArgumentParser(description="동아리 지출 CSV 구조 개선판")
    parser.add_argument("input", help="UTF-8 CSV 경로")
    parser.add_argument("--format", required=True, choices=["club", "event"])
    parser.add_argument("--output", default="outputs/refactored_report.json")
    args = parser.parse_args()
    try:
        text = Path(args.input).read_text(encoding="utf-8-sig")
        report = run_text(text, args.format, args.output)
    except (ValueError, OSError) as error:
        print("오류:", error)
        return 1
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print("저장:", args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
