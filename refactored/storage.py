"""CSV를 읽고 성공한 집계 결과를 JSON 파일로 저장한다."""

import csv
import io
import json
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


def save_report(report, output_path):
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = None
    try:
        # 모두 쓴 파일만 교체하므로 실패 시 이전 결과는 남는다.
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
