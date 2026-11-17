"""예상값은 계산 함수를 호출하지 않고 과제의 규칙에 따라 적었다."""

NORMAL_RESULT = {
    "count": 3,
    "total": 20000,
    "categories": [
        {"category": "간식", "count": 2, "total": 16500},
        {"category": "문구", "count": 1, "total": 3500},
    ],
}

ZERO_RESULT = {
    "count": 1,
    "total": 0,
    "categories": [{"category": "간식", "count": 1, "total": 0}],
}

UPPER_RESULT = {
    "count": 1,
    "total": 1000000000,
    "categories": [{"category": "장비", "count": 1, "total": 1000000000}],
}

AMOUNT_ERROR = "2행: 금액은 0~1,000,000,000원의 정수여야 합니다."
DATE_ERROR = "2행: 날짜 형식 또는 값이 잘못되었습니다."


def make_case(case_id, name, format_name, text, expected=None, error=None):
    return {
        "id": case_id,
        "name": name,
        "format": format_name,
        "text": text,
        "expected": expected,
        "error": error,
    }


def common_cases(project_dir):
    """세 버전에 그대로 반복할 기존 입력. 파일 사례와 직접 작성한 오류 사례."""
    examples = project_dir / "examples"
    club = (examples / "club_normal.csv").read_text(encoding="utf-8")
    event = (examples / "event_normal.csv").read_text(encoding="utf-8")
    zero = (examples / "club_zero.csv").read_text(encoding="utf-8")
    cases = [
        make_case("N1", "기존 club 양식 정상", "club", club, NORMAL_RESULT),
        make_case("N2", "기존 event 양식 정상", "event", event, NORMAL_RESULT),
        make_case("B1", "금액 하한 0원", "club", zero, ZERO_RESULT),
        make_case("B2", "금액 상한 10억 원", "club",
                  "날짜,항목,금액\n2026-11-10,장비,1000000000\n", UPPER_RESULT),
        make_case("E1", "완전히 빈 입력", "club", "", error="CSV가 비어 있습니다."),
        make_case("E2", "제목만 있는 빈 자료", "club", "날짜,항목,금액\n",
                  error="지출 내역이 없습니다."),
        make_case("E3", "필수 열 누락", "club", "날짜,항목\n2026-11-10,간식\n",
                  error="필수 열이 없습니다: 금액"),
        make_case("E4", "음수 금액", "club", "날짜,항목,금액\n2026-11-10,간식,-1000\n",
                  error=AMOUNT_ERROR),
        make_case("E5", "문자 금액", "club", "날짜,항목,금액\n2026-11-10,간식,천원\n",
                  error=AMOUNT_ERROR),
        make_case("E6", "존재하지 않는 날짜", "club", "날짜,항목,금액\n2026-02-30,간식,1000\n",
                  error=DATE_ERROR),
        make_case("E7", "빈 분류", "club", "날짜,항목,금액\n2026-11-10,  ,1000\n",
                  error="2행: 분류가 비어 있습니다."),
        make_case("E8", "금액 상한 초과", "club", "날짜,항목,금액\n2026-11-10,간식,1000000001\n",
                  error=AMOUNT_ERROR),
        make_case("E9", "중복된 열 이름", "club", "날짜,항목,금액,금액\n2026-11-10,간식,1000,1000\n",
                  error="중복된 열 이름이 있습니다."),
        make_case("E10", "행의 열 개수 불일치", "club", "날짜,항목,금액\n2026-11-10,간식\n",
                  error="2행: 열 개수가 제목 행과 다릅니다."),
    ]
    return cases


def new_format_cases(project_dir):
    """bank 지원은 기능 변경판에서만 추가되는 의도된 차이."""
    text = (project_dir / "examples" / "bank_normal.csv").read_text(encoding="utf-8")
    return [
        make_case("X1", "새 bank 양식 정상", "bank", text, NORMAL_RESULT),
        make_case("X2", "새 양식의 잘못된 쉼표", "bank",
                  '거래일,사용처분류,출금액\n2026.11.10,간식,"1,00원"\n',
                  error="2행: 출금액은 1,000원과 같은 원 단위 금액이어야 합니다."),
        make_case("X3", "새 양식의 잘못된 날짜", "bank",
                  "거래일,사용처분류,출금액\n2026.02.30,간식,1000원\n", error=DATE_ERROR),
    ]
