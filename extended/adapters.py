"""점으로 구분한 날짜와 원 단위 금액을 쓰는 새 양식."""

import re

from refactored.adapters import convert_date


def convert_bank_amount(value, row_number):
    # 쉼표는 세 자리 묶음만 허용한다. '1,2,3원'을 조용히 123원으로 바꾸지 않는다.
    pattern = r"(0|[1-9][0-9]*|[1-9][0-9]{0,2}(,[0-9]{3})+)원"
    if re.fullmatch(pattern, value) is None:
        raise ValueError(f"{row_number}행: 출금액은 1,000원과 같은 원 단위 금액이어야 합니다.")
    number = value[:-1].replace(",", "")
    return int(number)


class BankAdapter:
    required_columns = ["거래일", "사용처분류", "출금액"]

    def adapt(self, row, row_number):
        date = convert_date(row["거래일"], "%Y.%m.%d", row_number)
        amount = convert_bank_amount(row["출금액"], row_number)
        return {"date": date, "category": row["사용처분류"], "amount": amount}
