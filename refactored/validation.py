"""공통으로 사용하는 금액 범위와 빈 분류 검사."""


def validate_records(records, rows):
    for index in range(len(records)):
        record = records[index]
        row_number = rows[index][0]
        if not record["category"]:
            raise ValueError(f"{row_number}행: 분류가 비어 있습니다.")
        if record["amount"] < 0 or record["amount"] > 1000000000:
            raise ValueError(f"{row_number}행: 금액은 0~1,000,000,000원의 정수여야 합니다.")
