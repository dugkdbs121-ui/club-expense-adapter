"""기본판: 두 양식의 처리 절차를 한 모듈에 둔다."""

import argparse
import csv
import io
import json
from datetime import datetime
from pathlib import Path
import tempfile


def read_rows(text, required_columns):
    reader = csv.reader(io.StringIO(text.lstrip("\ufeff")), strict=True)
    try:
        header = next(reader, None)
        if not header:
            raise ValueError("CSV가 비어 있습니다.")
        columns = []
        for name in header:
            columns.append(name.strip())
        if len(columns) != len(set(columns)):
            raise ValueError("중복된 열 이름이 있습니다.")
        missing = []
        for name in required_columns:
            if name not in columns:
                missing.append(name)
        if missing:
            raise ValueError("필수 열이 없습니다: " + ", ".join(missing))

        rows = []
        for values in reader:
            if not values:
                continue
            row_number = reader.line_num
            if len(values) != len(columns):
                raise ValueError(f"{row_number}행: 열 개수가 제목 행과 다릅니다.")
            row = {}
            for index in range(len(columns)):
                row[columns[index]] = values[index].strip()
            rows.append((row_number, row))
    except csv.Error as error:
        raise ValueError("CSV 문법이 잘못되었습니다.") from error
    if not rows:
        raise ValueError("지출 내역이 없습니다.")
    return rows


def convert_date(value, date_format, row_number):
    try:
        date = datetime.strptime(value, date_format)
        if date.strftime(date_format) != value:
            raise ValueError("날짜 자릿수 불일치")
    except ValueError as error:
        raise ValueError(f"{row_number}행: 날짜 형식 또는 값이 잘못되었습니다.") from error
    return date.strftime("%Y-%m-%d")


def convert_amount(value, row_number):
    if not value or not value.isascii() or not value.isdecimal():
        raise ValueError(f"{row_number}행: 금액은 0~1,000,000,000원의 정수여야 합니다.")
    return int(value)


def convert_rows(rows, format_name):
    records = []
    for row_number, row in rows:
        # 기본판에서는 양식이 늘 때 이 분기를 바꾸어야 한다.
        if format_name == "club":
            date = convert_date(row["날짜"], "%Y-%m-%d", row_number)
            category = row["항목"]
            amount = convert_amount(row["금액"], row_number)
        else:
            date = convert_date(row["사용일"], "%Y/%m/%d", row_number)
            category = row["분류"]
            amount = convert_amount(row["지출액"], row_number)
        records.append({"date": date, "category": category, "amount": amount})
    return records


def validate_records(records, rows):
    for index in range(len(records)):
        record = records[index]
        row_number = rows[index][0]
        if not record["category"]:
            raise ValueError(f"{row_number}행: 분류가 비어 있습니다.")
        if record["amount"] < 0 or record["amount"] > 1000000000:
            raise ValueError(f"{row_number}행: 금액은 0~1,000,000,000원의 정수여야 합니다.")


def summarize(records):
    total = 0
    groups = {}
    for record in records:
        category = record["category"]
        amount = record["amount"]
        total += amount
        if category not in groups:
            groups[category] = {"count": 0, "total": 0}
        groups[category]["count"] += 1
        groups[category]["total"] += amount
    categories = []
    for category in sorted(groups):
        categories.append({
            "category": category,
            "count": groups[category]["count"],
            "total": groups[category]["total"],
        })
    return {"count": len(records), "total": total, "categories": categories}


def save_report(report, output_path):
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = None
    try:
        # 쓰기에 성공한 임시 파일만 교체하여 기존 결과를 보호한다.
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", newline="\n", dir=path.parent,
            prefix="expense_", suffix=".tmp", delete=False,
        ) as stream:
            temporary_path = Path(stream.name)
            stream.write(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        temporary_path.replace(path)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()


def run_text(text, format_name, output_path):
    if format_name == "club":
        columns = ["날짜", "항목", "금액"]
    elif format_name == "event":
        columns = ["사용일", "분류", "지출액"]
    else:
        raise ValueError("지원하지 않는 양식입니다: " + str(format_name))
    rows = read_rows(text, columns)
    records = convert_rows(rows, format_name)
    validate_records(records, rows)
    report = summarize(records)
    save_report(report, output_path)
    return report


def main():
    parser = argparse.ArgumentParser(description="동아리 지출 CSV 기본판")
    parser.add_argument("input", help="UTF-8 CSV 경로")
    parser.add_argument("--format", required=True, choices=["club", "event"])
    parser.add_argument("--output", default="outputs/baseline_report.json")
    args = parser.parse_args()
    try:
        if Path(args.input).resolve() == Path(args.output).resolve():
            raise ValueError("입력 파일과 결과 저장 경로는 달라야 합니다.")
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
