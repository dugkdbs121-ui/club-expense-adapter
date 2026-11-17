"""등록 목록만 확장하고 기존 실행 절차를 재사용한다."""

import argparse
import json
from pathlib import Path

from extended.adapters import BankAdapter
from refactored.adapters import ClubAdapter, EventAdapter
from refactored.service import run_with_adapter


ADAPTERS = {
    "club": ClubAdapter(),
    "event": EventAdapter(),
    "bank": BankAdapter(),
}


def run_text(text, format_name, output_path):
    if format_name not in ADAPTERS:
        raise ValueError("지원하지 않는 양식입니다: " + str(format_name))
    adapter = ADAPTERS[format_name]
    return run_with_adapter(text, adapter, output_path)


def main():
    parser = argparse.ArgumentParser(description="동아리 지출 CSV 최종판")
    parser.add_argument("input", help="UTF-8 CSV 경로")
    parser.add_argument("--format", required=True, choices=["club", "event", "bank"])
    parser.add_argument("--output", default="outputs/extended_report.json")
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
