"""외부 CSV 행을 공통 date/category/amount 구조로 변환한다."""

from datetime import datetime


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


class ClubAdapter:
    required_columns = ["날짜", "항목", "금액"]

    def adapt(self, row, row_number):
        date = convert_date(row["날짜"], "%Y-%m-%d", row_number)
        amount = convert_amount(row["금액"], row_number)
        return {"date": date, "category": row["항목"], "amount": amount}


class EventAdapter:
    required_columns = ["사용일", "분류", "지출액"]

    def adapt(self, row, row_number):
        date = convert_date(row["사용일"], "%Y/%m/%d", row_number)
        amount = convert_amount(row["지출액"], row_number)
        return {"date": date, "category": row["분류"], "amount": amount}
